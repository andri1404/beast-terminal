---
name: hermes-troubleshooting
description: Use when Hermes errors. State DB repair, WAL, gateway, provider 403/blocked, cron timeout.
---

# Hermes Agent Troubleshooting

## State DB Corruption ("session storage could not be written")

### Symptoms
- "No reply: the turn was stopped because session storage could not be written"
- "database disk image is malformed" in logs
- "FTS-corruption error" in logs
- "WAL journal_mode unsupported on this filesystem"

### Diagnosis

Check the logs first:
```
tail -100 ~/.hermes/logs/agent.log
grep -i "malformed\|corruption\|FTS\|state.db" ~/.hermes/logs/agent.log
```

Check state.db integrity:
```
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/ubuntu/.hermes/state.db')
print('Integrity:', conn.execute('PRAGMA integrity_check').fetchone()[0])
conn.close()
"
```

### Repair Escalation Ladder

**Step 1 — Doctor check (read-only):**
```
hermes doctor
```
Reports issues without modifying anything.

**Step 2 — Auto-repair:**
```
hermes doctor --fix
```
Or equivalently:
```
hermes sessions repair
```

**Step 2b — FTS-only corruption (integrity_check passes, writes fail):**

When `hermes sessions repair` and `hermes doctor --fix` both report "no repair needed" but the logs still show `database disk image is malformed` on writes, the FTS5 index is corrupt while the main DB is structurally intact. This is invisible to `PRAGMA integrity_check`.

Confirm by checking logs AND testing a write:
```bash
grep "database disk image is malformed" ~/.hermes/logs/agent.log | tail -5
```

Fix — rebuild the FTS index in-place:
```python
import sqlite3
conn = sqlite3.connect('/home/ubuntu/.hermes/state.db')
# Rebuild both FTS indexes
conn.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")
conn.execute("INSERT INTO messages_fts_trigram(messages_fts_trigram) VALUES('rebuild')")
conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
conn.close()
```

Verify by testing a write after rebuild (see `references/fts-rebuild-verify.md` for full verification script and reproduction recipe).

**Step 3 — If all above fails** (malformed schema, deep corruption):

The repair creates a timestamped backup at `~/.hermes/state.db.malformed-backup-<timestamp>`.

First, inspect recoverability:
```
hermes sessions recover --source ~/.hermes/state.db.malformed-backup-<timestamp> --inspect-only
```

If recoverable, rebuild into a new DB:
```
hermes sessions recover --source ~/.hermes/state.db.malformed-backup-<timestamp> --output recovered-state.db
```

Then swap in the recovered DB:
```
mv ~/.hermes/state.db ~/.hermes/state.db.corrupt
mv recovered-state.db ~/.hermes/state.db
```

### Important: Kill Gateway First

The gateway process holds a read lock on state.db, preventing WAL checkpoint and VACUUM. Before any repair:

```
# Find gateway PID
ps aux | grep "hermes.*gateway run"

# Kill it
kill <gateway_pid>

# After repair, restart:
hermes gateway start
```

### WAL Ballooning

If `state.db-wal` is very large (100MB+), the WAL can't checkpoint because a long-running process (gateway or CLI) holds a read lock. Kill the oldest reader, then:

```
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/ubuntu/.hermes/state.db')
conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
conn.close()
"
```

## Provider HTTP 403 / "Your request was blocked"

### Diagnosis

When a custom provider returns HTTP 403 with a generic "blocked" message but
the API key works from curl, the issue is likely a **request header** being
filtered by the provider's WAF/CDN.

**Isolation ladder:**

1. Test the API key with a minimal curl request:
```bash
curl -s -w "\nHTTP %{http_code}" -X POST "$BASE_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"model":"<model>","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```
If this returns 200, the API key + model are valid — the issue is in the
request shape or headers.

2. Test with headers that the OpenAI Python SDK adds automatically:
```bash
# Test User-Agent header
curl ... -H "User-Agent: OpenAI/v1" ...
# Test x-stainless-lang header
curl ... -H "x-stainless-lang: python" ...
```

3. The most common culprit: `User-Agent: OpenAI/v1` — some providers block
   the OpenAI SDK's default User-Agent string.

### Fix: Override headers via extra_headers

Add `extra_headers` to the offending custom provider entry:

```bash
hermes config set custom_providers.<index>.extra_headers.User-Agent "HermesAgent/1.0"
```

Or in YAML:
```yaml
custom_providers:
  - name: MyProvider
    base_url: https://...
    extra_headers:
      User-Agent: HermesAgent/1.0
```

### Pitfalls

- `hermes config set custom_providers.N.extra_headers '{"Key":"Val"}'` stores
  the value as a JSON *string*, not a dict. Use dot-notation to set individual
  keys instead: `hermes config set custom_providers.N.extra_headers.Key "Val"`.
- Verify the fix with `python3 -c "import yaml; ..."` — the value must be a
  `dict`, not a `str`.

## TokenHarbor / API Gateway 403 Errors

When a custom provider (9Router, TokenRouter, etc.) routes through TokenHarbor
and returns HTTP 403, the error body often contains the real reason.

### email_verification_required

**Symptom:** Model fails with HTTP 403 and error body contains:
```json
{"error":{"message":"Verify your email address to use the API...","type":"email_verification_required","code":"email_verification_required"}}
```

**Cause:** The TokenHarbor API key (identified by UUID prefix in the model name,
e.g. `openai-compatible-chat-bcac984e-.../glm-5.2`) belongs to an account whose
email hasn't been verified.

**Diagnosis — check agent logs for the real error:**
```bash
grep -A2 "email_verification\|PermissionDeniedError" ~/.hermes/logs/agent.log | tail -20
```
The gateway log shows the full error body even when the CLI only shows a generic
"provider failed after retries" message.

**Fix (two options):**

1. Verify the email — open the confirmation link sent to the TokenHarbor
   account's email, or request a new one at https://tokenharbor.ai/dashboard.

2. Switch to a verified API key prefix — multi-key providers like 9Router list
   the same model under different UUID prefixes. Find the models list:
   ```bash
   hermes config get custom_providers | grep -o "openai-compatible-chat-[a-f0-9-]*/[a-z0-9.-]*"
   ```
   Then switch to a working prefix:
   ```bash
   hermes config set model.default "openai-compatible-chat-<verified-uuid>/<model>"
   hermes config set model.provider "<provider-name>"
   ```

### Model switching commands

`hermes model set ...` does NOT exist. Use:
```bash
hermes model                        # interactive picker (TUI)
hermes config set model.default "full/model/path"
hermes config set model.provider "provider-name"
```

## Skills API / MCP Returns 0 Results

### Symptoms
- `search_skills` returns empty results
- `[INDEX] Loaded 0 skills` in `~/.hermes/skills-api/server.log`
- `curl http://127.0.0.1:8765/stats` shows `"total_skills": 0`

### Root Cause
The v1 server (`server.py`) reads `SKILLS_DIRS_EXTRA` from the environment. When set to `""` (empty string), `os.environ.get("SKILLS_DIRS_EXTRA", default)` returns `""` — NOT the default path. This causes the indexer to find 0 skill files.

### Diagnosis
```bash
# Check current env of the running process
PID=$(ss -tlnp | grep 8765 | grep -oP 'pid=\K[0-9]+')
cat /proc/$PID/environ | tr '\0' '\n' | grep SKILLS
# → SKILLS_DIRS_EXTRA=    ← EMPTY = BUG
```

### Fix
1. Kill the process: `fuser -k 8765/tcp`
2. Fix `start-all.sh` — remove `SKILLS_DIRS_EXTRA=""` or set it to the actual path:
   ```bash
   SKILLS_DIR="/home/ubuntu/.hermes/skills" SKILLS_DIRS_EXTRA="/home/ubuntu/.hermes/skills" PYTHONPATH="./deps" nohup python3 server.py ...
   ```
3. Restart: `bash ~/.hermes/skills-api/start-all.sh`
4. Verify: `curl -s -H "X-API-Key: hermes-logs-2026" http://127.0.0.1:8765/stats | python3 -m json.tool | grep total_skills`

### MCP v2: Empty DB
If the v1 REST API works but MCP v2 (`search_skills` via MCP) returns 0 results, the `skills-hub.db` SQLite database is empty. The v2 MCP server reads from the DB, not from files. See `skills-api-fix` skill for comprehensive recovery paths including: local disk sync, .bak restore, GDrive backup, and full DB rebuild. Also check the secondary DB at `~/.hermes/skills-api/skills_hub.db` — both can go empty simultaneously.

## Cron no_agent Script Timeout

When a `no_agent` cron job fails with a script error but the script runs fine
manually, the cron runner's ~30s default timeout is the likely cause. Scripts
with multiple network calls (gRPC, HTTP, API) can exceed this under proxy lag.

See `references/cron-noagent-timeout.md` for the full diagnostic flow (token
check → proxy test → per-call timing → fix options) and real-world HFM gRPC
example.

## Cron no_agent Script: Wrong Interpreter / Missing Deps (silent failure)

A `no_agent` cron script (`.py`) is run with the **gateway's `sys.executable`**,
NOT the shell's `python3`. Find it with `ps aux | grep "gateway run"` — on this
host it is `/usr/local/lib/hermes-agent/venv/bin/python`. Consequences:

- **Top-level import** of a dep missing from that venv → script exits code 1,
  cron shows `status=failed` with `ModuleNotFoundError` in the error column.
- **Import inside a function** (common in scripts that lazy-import `curl_cffi`
  etc.) → the `except` swallows it, script exits 0, cron shows `status=completed`
  with **empty stdout** — the job silently never produces output. This is the
  nasty one: it looks healthy but delivers nothing.

Diagnose via the executions DB (don't trust the `list` summary alone):
```bash
python3 -c "import sqlite3; c=sqlite3.connect('/home/ubuntu/.hermes/cron/executions.db'); \
  [print(r[1], r[2], (r[3] or '')[:120]) for r in c.execute(\"SELECT job_id,status,error FROM executions ORDER BY finished_at DESC LIMIT 20\")]"
```

Fix — install the dep into the gateway venv (NOT deep-eye venv, NOT /usr/bin/python3):
```bash
/usr/local/lib/hermes-agent/venv/bin/python -m pip install curl_cffi
```

Also check `~/.hermes/scripts/*.py` shebangs are irrelevant: the cron runner
ignores the shebang and picks the interpreter by extension (`.sh`→bash, else
the gateway `sys.executable`). See scheduler.py `_run_script` (deliberately
does NOT honour shebang).

## Disk Space ("session storage could not be written" / "No space left on device")

### Symptoms
- "No reply: the turn was stopped because session storage could not be written"
- Terminal tool returns "No space left on device" (OSError 28)
- `df -h /` shows 100% disk usage

### Diagnosis
```bash
df -h /
du -sh ~/.hermes/*/ | sort -rh | head -10
```

### Common space hogs (by size)
| Path | Typical size | Safe to delete? |
|------|-------------|-----------------|
| `~/.hermes/skills-hub.db` | 500M+ | ✅ Yes — use MCP API instead |
| `~/.hermes/omop-skills/` | 300M+ | ✅ Yes — redundant skill copies |
| `~/.cache/ms-playwright/` | 650M+ | ✅ Yes — browser binaries, re-downloadable |
| `~/.cache/go-build/` | 100M+ | ✅ Yes — Go build cache |
| `~/.cache/node-gyp/` | 65M+ | ✅ Yes — Node build cache |
| `/tmp/` | variable | ✅ Yes — clear old session artifacts |
| `~/.hermes/state.db` | 100M+ | ⚠️ VACUUM only, don't delete |
| `~/.hermes/hermes-agent/` | 800M+ | ❌ No — core agent files |

### Quick cleanup (safe)
```bash
# Delete local CVE DB (use MCP API instead)
rm -f ~/.hermes/skills-hub.db
# Delete redundant skill copies
rm -rf ~/.hermes/omop-skills/
# Clean caches
rm -rf ~/.cache/ms-playwright/ ~/.cache/go-build/ ~/.cache/node-gyp/
# Clean /tmp
rm -rf /tmp/*
# VACUUM state.db
python3 -c "import sqlite3; c=sqlite3.connect('$HOME/.hermes/state.db'); c.execute('VACUUM'); c.close()"
```

### Pitfall
- **Don't skip disk check when you see "session storage could not be written"** — the message sounds like DB corruption but a full disk is the more common cause. Check `df -h` first, then diagnose state.db.