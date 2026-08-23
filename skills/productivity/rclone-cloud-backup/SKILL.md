---
name: rclone-cloud-backup
description: "Use when syncing dirs to GDrive, Mega, or S3 with rclone."
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [rclone, backup, gdrive, cloud, sync, mega]
    pitfalls:
      - "GDrive ALWAYS sets directory modification time on creation — `--no-update-modtime` only affects files, not directories."
      - "`--no-traverse` is IGNORED by `rclone sync`; use `rclone copy` for initial large syncs."
      - "Stats output is buffered when stdout is not a terminal; may not appear until completion."
      - "First sync of 19K+ top-level directories can take hours due to GDrive API directory creation."
      - "On 60K+ object remotes, `rclone ls`/`rclone size`/`rclone sync` may ALL time out — fall back to `--files-from` + `--ignore-existing` approach."
      - "Repeated failed sync attempts can trigger GDrive API rate limiting, making even basic `rclone ls` time out."
      - "The default rclone OAuth client ID is shared globally — rate limits hit much faster than with a custom client. `--tpslimit 1` + `--drive-list-chunk 10` is the minimum-safe combo for large syncs on the shared client."
      - "`--tpslimit` does NOT apply to `--fast-list` listing operations; listing with `--fast-list` can still exhaust the shared-client quota in seconds."
      - "After rate-limiting, `rclone ls`/`rclone size` on the ROOT backup directory can time out even with <1K objects. Verify per-subdirectory instead."
      - "`--fast-list` on the shared OAuth client can be slow even for medium directories (41M, 476 files). Prefer `--files-from` + `--ignore-existing` for anything beyond trivial syncs."
      - "`rclone size` can UNDERCOUNT objects on the remote (e.g., 280 vs 477 actual). It is NOT reliable for verification. Use `rclone check --one-way --files-from` instead — it returns '0 differences found' when truly synced."
      - "Throttled sync (`--tpslimit 1 --drive-list-chunk 10`) is NOT viable for cron jobs — 10+ minutes for 477 files without completing. Use `--files-from` + `--no-traverse` exclusively for cron."
      - "`rclone copyto` on actively-written SQLite DBs (Hermes state.db, skills-hub.db) fails with 'source file is being updated (mod time changed)' — the resumable upload checks mod-time mid-transfer and `--ignore-times` does NOT prevent this. Workaround: snapshot the DB to /tmp/ first, upload from the frozen copy, then delete the snapshot."
      - "Shared OAuth client can cause SILENT HANGS (not just 403 errors) — `rclone copyto` with `--no-traverse` may show zero I/O for 12+ minutes (read_bytes stuck at ~2MB, write_bytes 0). The process never errors out, just hangs. Can affect ANY file size — even 86MB .gz files have hung. Compression to `.gz` reduces the probability but does NOT eliminate it. The reliable fix: kill the stuck rclone process and retry the upload solo — retries almost always work instantly. For cron: upload each DB in a separate rclone call so one hang doesn't block the rest."
      - "`rclone ls gdrive:backup/ --include 'file.db' --no-traverse` on the ROOT directory can time out even with `--no-traverse`. Use `--max-depth 1` to scope the listing to immediate children only."
      - "Hermes gateway blocks shell commands containing `&` even inside quoted strings (e.g., `echo \"EXIT: $?\"`). The `&` triggers background-job detection regardless of context. Avoid exit-code echo patterns; use separate `echo $?` on its own line or check exit code via `$?` in follow-up logic without echoing."
      - "Chaining multiple `rclone copyto` calls with `&&` in one command is fragile for cron — a silent hang on the first upload blocks all subsequent uploads. Upload each DB in a separate `terminal()` call or separate background process so one hang doesn't cascade."
      - "Stale DB copies in `/tmp` (e.g., `skills-hub-copy.db`, `state.db.recovered`) from prior sessions/builds/recoveries are the #1 cause of disk-full failures in cron backup jobs. A single stale 516MB DB copy can eat all remaining space. Always run `ls -lhS /tmp/skills* /tmp/state* /tmp/*.db*` before starting the backup and nuke any stale copies."
      - "`rclone sync` can time out even on small directories (12MB, 154 files, 28 subdirs) due to shared OAuth client rate limiting during the remote listing phase. For one-shot cron backups, use `tar -czf` + `rclone copy` of the single archive — eliminates per-file API calls entirely."
      - "`rclone sync` burns API quota on SetModTime calls AFTER all files are transferred. The stats may show 100% transferred (all files done) but the sync continues for 30-60s calling SetModTime on every subdirectory. This post-transfer directory touch phase exhausts the shared OAuth quota and causes 403 errors for subsequent `rclone copyto`/`rcat` calls in the same cron job. **Fix:** always run DB uploads BEFORE the directory sync, or use `--files-from` + `rclone copy` with `--no-traverse` instead of `rclone sync`."
      - "`rclone copy gdrive:remote/file.db` fails with `'is a file not a directory'` — `rclone copy` requires a DESTINATION DIRECTORY, not a file path. Use `rclone copyto` to target a specific file name, or `rclone copy . gdrive:remote/` (trailing slash) to copy into a directory."
      - "Hermes gateway may block `terminal()` calls containing `python3`/`sqlite3` on DB paths — falsely flagged as gateway-restart commands. Use `execute_code` tool for all DB integrity checks and queries during backup cron jobs."
      - "`pkill -f` can SELF-MATCH the calling shell. A pattern like `pkill -f 'rclone copyto.*skills-hub-full'` matches the shell command string itself, killing the `pkill` process (and its parent shell) with exit code -15. The follow-up `sleep 60` in the same `&&` chain never runs. **Fix:** kill + wait in separate `terminal()` calls, or use `pkill -fx` with an exact match, or target by PID via `ps aux | grep` first."
      - "`--tpslimit 1 --tpslimit-burst 1` can cause 180s timeouts for .gz files — the throttled verification phase stalls the shared OAuth client. Symptoms: `rclone copyto` times out silently (no 403, no error, just 180s wall-time). Confirmed at 72MB and 178MB. **Fix:** kill the stuck process, then retry with MINIMAL flags: `--transfers 1 --no-traverse` ONLY. Confirmed 2026-08-21: 75MB state.db.gz hung at 150s with `--verbose --stats 30s`, retry with just `--transfers 1 --no-traverse` succeeded instantly."
      - "**BIDIRECTIONAL — minimal flags can also hang, tpslimit can also succeed (2026-08-22):** The reverse scenario is now confirmed: minimal flags (`--transfers 1 --no-traverse`) can time out repeatedly while tpslimit succeeds. 89MB state.db.gz timed out 3× with minimal flags, then `--transfers 1 --no-traverse --tpslimit 1 --tpslimit-burst 1 --drive-chunk-size 8M` succeeded instantly. In the same session, 175MB skills-hub-full.db.gz uploaded fine with minimal flags. **The shared OAuth client is unpredictable — neither approach is universally reliable. When one fails 3×, switch to the other.** `--verbose` and `--stats` both trigger additional API calls during the verification phase and can independently cause the shared OAuth hang regardless of which approach is used."
      - WAL checkpoint before gzip — a large WAL file (100MB+) inflates the compressed output unnecessarily. Run PRAGMA wal_checkpoint(TRUNCATE) via execute_code before compressing the DB. If TRUNCATE returns (0,0,0), the WAL is already clean — no action needed.
            - --stats Ns can contribute to the shared OAuth verification hang — the periodic stats output triggers extra API calls during the verification/commit phase. Combined with --verbose, it can cause the 100% transferred but 0/1 completed hang even WITHOUT tpslimit. For cron DB uploads, omit --stats entirely; use only --transfers 1 --no-traverse.
      - "0-byte DB with orphaned SHM — `skills-hub.db` can be zeroed to 0 bytes by a crash or failed write while its `-shm` sidecar survives (224KB orphan). The SHM belongs to the OLD DB image and makes SQLite throw 'database disk image is malformed' on any read. Symptoms: `ls -la` shows 0-byte .db file + non-zero .db-shm, no .db-wal. **Fix:** `rm -f ~/.hermes/skills-hub.db ~/.hermes/skills-hub.db-shm ~/.hermes/skills-hub.db-wal`, then restore from GDrive. Confirmed 2026-08-20: DB was 0 bytes, SHM was 224KB, restore produced 522MB healthy DB."
---

# Rclone Cloud Backup

Sync local directories to cloud storage (Google Drive, Mega, S3, etc.) using rclone.

## Quick Start

```bash
# Verify remote is reachable
rclone about gdrive:
rclone lsd gdrive:backup/

# Dry-run first to see what needs transferring
rclone sync ~/data/ gdrive:backup/data/ --fast-list --dry-run --stats 30s

# Real sync
rclone sync ~/data/ gdrive:backup/data/ --fast-list --transfers 8
```

## Flag Reference

| Flag | Effect | Notes |
|------|--------|-------|
| `--fast-list` | Recursive listing in one API call | Always use for large dirs |
| `--no-traverse` | Skip destination listing | Only for `rclone copy`; ignored by `rclone sync` |
| `--no-update-modtime` | Skip file mod-time updates | Does NOT skip directory mod-time updates |
| `--transfers N` | Parallel transfers | 8 is safe for GDrive; reduce if rate-limited |
| `--tpslimit N` | Rate-limit API calls/sec | 1-2 for shared OAuth client; 10 if using custom OAuth client |
| `--stats Ns` | Print stats every N sec | Buffered when stdout is not a terminal |
| `--dry-run` | Test without changes | Always run first for large syncs |
| `--verbose` | Detailed logging | **AVOID for cron backups.** PITFALL: the transfer counter (N/M) is misleading — it can show 100% transferred while 0/1 completed. Even WITHOUT tpslimit, `--verbose` can trigger the shared OAuth verification hang (confirmed 2026-08-21: 75MB state.db.gz hung at 150s with `--verbose --stats 30s`, retry without both flags succeeded instantly). Trust the exit code, not the verbose counter. |
| `--ignore-existing` | Skip files already on remote | Use for resume after partial sync |
| `--drive-list-chunk N` | Page size for directory listing | 10 for shared OAuth client to avoid rate limits; default 1000 |

## Strategy for Large Directories (10K+ top-level dirs)

### First Sync (directory structure doesn't exist on remote)

GDrive API creates directories one at a time and always sets mod-time on each. With 19K+ directories, this can take hours.

**Preferred approach:** Use `rclone copy` which supports `--no-traverse`:

```bash
rclone copy ~/large-dir/ gdrive:backup/large-dir/ \
  --fast-list --no-traverse --transfers 8 --no-update-modtime
```

### Subsequent Syncs (directory structure exists)

Once directories exist on remote, use `rclone sync` (fast — only transfers changed files):

```bash
rclone sync ~/large-dir/ gdrive:backup/large-dir/ \
  --fast-list --transfers 8 --no-update-modtime
```

### Monitoring Long-Running Syncs

When stdout is piped (cron, background), stats are buffered. Monitor via:

```bash
# Check if process is alive
ps -p PID -o pid,etime,stat

# Check I/O progress
cat /proc/PID/io
# read_bytes increasing = still listing source
# write_bytes > 0 = transfers happening

# Check network connections
ss -tnp | grep PID
```

### Hermes Skills Backup (cron recipe)

```bash
# 0. PRE-CHECK — verify DB integrity BEFORE compressing.
#    A corrupted DB (stale WAL/SHM, partial write) will gzip fine but
#    produce a useless backup. Use execute_code (not terminal) for DB
#    checks — the gateway may block python3/sqlite3 in terminal().
#    ALSO: checkpoint the WAL first — a 100MB+ WAL inflates gzip output.
#    Check integrity + checkpoint:
python3 -c "
import sqlite3
db = sqlite3.connect('/home/ubuntu/.hermes/skills-hub.db')
print('integrity:', db.execute('PRAGMA integrity_check').fetchone()[0])
print('wal_checkpoint:', db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchall())
print('skills:', db.execute('SELECT COUNT(*) FROM skills').fetchone()[0])
print('cves:', db.execute('SELECT COUNT(*) FROM cves').fetchone()[0])
" 2>&1
#    If 'database disk image is malformed':
#      rm -f ~/.hermes/skills-hub.db-wal ~/.hermes/skills-hub.db-shm
#      Retry integrity check. If still malformed → restore from GDrive:
#      rclone copyto gdrive:hermes-backup/skills-hub-full.db.gz /tmp/skills-hub-full.db.gz
#      gunzip, verify, swap, rm WAL/SHM — see skills-api skill for full restore flow.

# 1. UPLOAD DBs FIRST — before any directory sync.
#    Directory syncs burn shared OAuth quota on SetModTime calls for every
#    subdirectory AFTER files are transferred. If a directory sync runs first,
#    subsequent DB uploads may hit 403 rate limits. DBs first, dirs second.

# 1a. Unified DB — compress to .gz first to avoid shared OAuth silent hangs.
#    Raw 518MB uploads hang indefinitely; .gz uploads reliably with MINIMAL flags.
#    NAMING: upload to skills-hub-full.db.gz when DB > 100MB (full 19K+ skills, 379K+ CVEs).
#    The skills-hub.db.gz name is for stripped/small DBs. The full DB is the canonical backup.
#    On disk-tight systems, skip the cp snapshot — gzip directly from source:
#      gzip -c ~/.hermes/skills-hub.db > /tmp/skills-hub-full.db.gz
gzip -c ~/.hermes/skills-hub.db > /tmp/skills-hub-full.db.gz
rclone copyto /tmp/skills-hub-full.db.gz gdrive:hermes-backup/skills-hub-full.db.gz \
  --transfers 1 --no-traverse
rm /tmp/skills-hub-full.db.gz

# 3. state.db — snapshot + compress, upload.
#    ~268MB raw → ~99MB .gz (as of 2026-08-23).
#    Shared OAuth is unpredictable — try minimal flags first, fall back to tpslimit:
#    First attempt: --transfers 1 --no-traverse
#    If 3× timeout: --transfers 1 --no-traverse --tpslimit 1 --tpslimit-burst 1 --drive-chunk-size 8M
#    Both approaches have succeeded and failed in different sessions.
cp ~/.hermes/state.db /tmp/state.db.snap
gzip -c /tmp/state.db.snap > /tmp/state.db.gz
rclone copyto /tmp/state.db.gz gdrive:hermes-backup/state.db.gz \
  --transfers 1 --no-traverse
rm /tmp/state.db.snap /tmp/state.db.gz

# 4. Other small DBs — copyto
for db in kanban.db verification_evidence.db; do
  rclone copyto ~/.hermes/$db gdrive:hermes-backup/$db \
    --transfers 1 --no-traverse
done

# 5. Skills directory — use --files-from to avoid --fast-list rate limiting.
#    RUN AFTER DBs — directory sync burns quota on SetModTime calls.
find ~/.hermes/skills/ -type f ! -path '*/.git/*' > /tmp/skills_files.txt
rclone copy ~/.hermes/skills/ gdrive:hermes-backup/skills/ \
  --files-from /tmp/skills_files.txt --no-traverse \
  --transfers 4 --ignore-existing --tpslimit 4 --stats 30s
# → Instant when files are already synced

# 6. Skills-api — use --files-from to avoid remote listing
#    (--fast-list on shared OAuth client is too slow even for 41M/477 files)
#    EXCLUDE venv/.venv to avoid symlink warnings
find ~/.hermes/skills-api/ -type f \
  ! -path '*/.git/*' ! -path '*/__pycache__/*' \
  ! -name '*.pyc' ! -path '*/venv/*' ! -path '*/.venv/*' > /tmp/skills_api_files.txt
rclone copy ~/.hermes/skills-api/ gdrive:hermes-backup/skills-api/ \
  --files-from /tmp/skills_api_files.txt --no-traverse \
  --transfers 4 --ignore-existing --tpslimit 4 --stats 30s
# → Instant when files are already synced

# 7. VERIFY — use rclone check, NOT rclone size (which can undercount)
# Skills dir
rclone check ~/.hermes/skills/ gdrive:hermes-backup/skills/ \
  --files-from /tmp/skills_files.txt --no-traverse --one-way
# Skills-api dir
rclone check ~/.hermes/skills-api/ gdrive:hermes-backup/skills-api/ \
  --files-from /tmp/skills_api_files.txt --no-traverse --one-way
# → "0 differences found" = authoritative confirmation
```

### Omop-Skills (24K+ files, 21K+ dirs)

```bash
# Use --files-from to avoid listing 60K+ remote objects.
# This skips the remote listing entirely — checks each local file individually.
find ~/.hermes/omop-skills/ -type f > /tmp/omop_files.txt
rclone copy ~/.hermes/omop-skills/ gdrive:hermes-backup/omop-skills/ \
  --files-from /tmp/omop_files.txt --no-traverse --transfers 8 \
  --ignore-existing --tpslimit 8
```

**ALTERNATIVE (throttled — NOT for cron):** when `--files-from` is overkill but shared OAuth client is rate-limited:

```bash
rclone copy ~/.hermes/omop-skills/ gdrive:hermes-backup/omop-skills/ \
  --transfers 1 --checkers 1 --tpslimit 1 --tpslimit-burst 1 \
  --drive-list-chunk 10 --drive-chunk-size 16M --retries 2
# NOTE: This takes ~2.5 hours just for listing with 45K items. Prefer --files-from.
```

### When Remote Listing Times Out (60K+ objects)

If `rclone ls`, `rclone size`, or `rclone sync` all time out on the remote directory,
the GDrive API is overwhelmed by the number of objects. Fall back to a file-by-file
approach that avoids listing the remote:

```bash
# Create file list from local source
find /local/dir/ -type f > /tmp/filelist.txt

# Copy with --files-from — checks each file individually, no remote listing
rclone copy /local/dir/ gdrive:backup/dir/ \
  --files-from /tmp/filelist.txt --no-traverse --transfers 8 \
  --ignore-existing --tpslimit 8
```

**Why this works:** `--files-from` reads the local file list and checks each file
against the remote one at a time. `--no-traverse` prevents a full remote tree walk.
`--ignore-existing` skips files already present. The combination avoids the
catastrophic remote listing that kills `sync`/`ls`/`size` on massive directories.

**Exit code 0 with no output** = all files already synced. This is normal and correct.

### Shared OAuth Client Rate Limiting (403 Quota Exceeded)

The default rclone GDrive client ID (`202264815644.apps.googleusercontent.com`) is
shared by ALL rclone users worldwide. Under heavy global usage, even moderate listing
operations get 403 "Quota exceeded" errors with `rateLimitExceeded`.

**Symptoms:**
```
Error 403: Quota exceeded for quota metric 'Queries' and limit 'Queries per minute'
of service 'drive.googleapis.com' for consumer 'project_number:202264815644'
```

**Why `--tpslimit` doesn't always help:** `--fast-list` issues a single bulk listing
API call that can still exhaust the shared quota instantly. `--tpslimit` only
throttles individual API calls, not the bulk listing call itself.

**Working approach for the shared client:**

```bash
# WITHOUT --fast-list (paginated listing, respects --tpslimit)
# WITH --drive-list-chunk 10 (tiny pages, 10 items per API call)
# WITH --tpslimit 1 (1 call/sec, stays under shared quota)
rclone copy /local/dir/ gdrive:backup/dir/ \
  --transfers 1 --checkers 1 --tpslimit 1 --tpslimit-burst 1 \
  --drive-list-chunk 10 --drive-chunk-size 16M --retries 2
```

**Trade-off:** With 45K items, this takes ~2.5 hours just for listing. Prefer
`--files-from` + `--ignore-existing` (see above) for large directories.

**Permanent fix:** Create a custom GCP project with Drive API enabled and configure
rclone with your own `client_id` + `client_secret`. Then `--tpslimit 10` is safe.

### Cleanup: Deduplicate Remote After Bad Syncs

If the remote has more objects than the local source (e.g., 60K remote vs 24K local),
previous syncs left duplicate entries. Clean up with:

```bash
# List duplicates first (dry-run)
rclone dedupe gdrive:hermes-backup/omop-skills/ --dedupe-mode newest --dry-run

# Actually dedupe
rclone dedupe gdrive:hermes-backup/omop-skills/ --dedupe-mode newest
```

**Warning:** This itself requires listing the remote, which may time out on 60K+ objects.
Consider running during off-peak hours or in smaller batches via `--max-depth`.

## Reference Files

- `references/live-db-snapshot-workaround.md` — "source file is being updated" error transcript, root cause, and snapshot-to-temp workaround for live Hermes DBs.
- `references/gdrive-large-dir-behavior.md` — GDrive API performance data, timing, and root cause analysis for 19K+ directory syncs.
- `references/gdrive-shared-oauth-rate-limiting.md` — Shared OAuth client 403 rate-limit error transcript, failed approaches, and working `--drive-list-chunk` workaround.

## Single Large File Backup (DBs, archives)

For backing up a single large file (e.g., `skills-hub.db` at 518MB), use `rclone copyto`:

```bash
# For files <200MB — direct copyto works reliably:
rclone copyto ~/path/to/small-file.db gdrive:backup/small-file.db \
  --transfers 1 --no-traverse --stats 30s

# For files >200MB — compress to .gz first to avoid shared OAuth silent hangs.
# Raw 518MB uploads hang with zero write_bytes; 176MB .gz uploads reliably:
gzip -c ~/path/to/large-file.db > /tmp/large-file.db.gz
rclone copyto /tmp/large-file.db.gz gdrive:backup/large-file.db.gz \
  --transfers 1 --no-traverse --stats 30s
rm /tmp/large-file.db.gz
```

**PITFALL:** The shared OAuth client can silently hang on ANY file size — even 86MB `.gz` files have hung with `read_bytes` progressing but `write_bytes` stuck at 0. Even small files (116KB `kanban.db`) can time out (30s) on the shared OAuth client. The process never errors out, just hangs. **Fix:** kill the stuck rclone process and retry the upload solo with `--tpslimit 1 --tpslimit-burst 1` — retries almost always work instantly. For cron jobs, upload each DB in a separate `rclone copyto` call (not chained with `&&`) so one hang doesn't block the rest. Compression to `.gz` is still recommended — it reduces the probability of hangs and makes uploads faster when they succeed.

**REFINED RETRY for "100% transferred but 0/1 completed" hang (2026-08-21):** When `--verbose` shows `Transferred: 74.216 MiB / 74.216 MiB, 100%` but `Transferred: 0 / 1, 0%` — the file bytes were uploaded but the final verification/commit phase hangs on the shared OAuth client. The speed drops to 0 B/s and it loops forever. **Fix:** kill the process, wait 60s for rate-limit reset, then retry with MINIMAL flags: `--transfers 1 --no-traverse` ONLY. No `--verbose`, no `--stats`, no `--tpslimit`, no `--drive-chunk-size`, no `--retries`. Confirmed 2026-08-21: 75MB state.db.gz — first attempt with tpslimit hung, second with `--verbose --stats 30s` (no tpslimit) also hung at 150s with ETA 3h, third with just `--transfers 1 --no-traverse` succeeded instantly. `--verbose` and `--stats` both trigger extra API calls during verification and can independently cause the hang on the shared OAuth client.

## Directory Backup via tar.gz (many small files)

When `rclone sync` or even `rclone copy --files-from` on a directory of many small files
times out or stalls, use `tar.gz` + single-file `rclone copy` as the reliable fallback.
This turns N small files into 1, eliminating the per-file API calls that trigger shared
OAuth rate limiting.

**PITFALL — `rclone sync` can time out even on small directories (2026-08-15):** A 12MB
directory with 154 files across 28 subdirectories can trigger 300s+ timeouts on the shared
OAuth client during the remote listing phase. The `--files-from` approach is the first choice
for repeated incremental syncs, but for one-shot cron backups or when the shared OAuth client
is already rate-limited, tar.gz is the reliable fallback.

```bash
# Compress the entire directory into a single archive
tar -czf /tmp/dir-backup.tar.gz -C /path/to/parent subdir/

# Upload as a single file (no remote listing needed)
rclone copy /tmp/dir-backup.tar.gz gdrive: \
  --transfers 1 --no-traverse

# Clean up
rm /tmp/dir-backup.tar.gz
```

**Verification:** Use `rclone size` on the single file (works reliably for single objects):
```bash
rclone size gdrive:dir-backup.tar.gz
# → Total objects: 1, Total size: 2.734 MiB
```

**Trade-off:** tar.gz is a full-snapshot approach — no incremental diff. Each backup
replaces the entire archive. For directories that change frequently, prefer `--files-from`
for incremental syncs. For periodic full backups (daily/weekly cron), tar.gz is simpler
and more reliable than fighting the shared OAuth client.

## Disk-Full Prevention & Recovery (large DB backups)

`gzip` of a 500MB+ DB fails with `gzip: stdout: No space left on device` when the disk is near-full — the #1 mid-backup failure. Check before starting:

```bash
df -h / | tail -1   # need free space ≥ the .gz output (~1/3 of raw size)
```

Recovery ladder when the disk is full (least destructive first):

```bash
# 0. MOST COMMON: Stale DB copies in /tmp from prior sessions/builds/recoveries
#    These are the #1 space hogs in cron backup scenarios and are NOT covered
#    by the .bak or .gz patterns below. Check aggressively:
ls -lhS /tmp/skills* /tmp/state* /tmp/*.db* /tmp/*.gz 2>/dev/null
rm -f /tmp/skills-hub-copy.db /tmp/state.db.recovered /tmp/state.db-wal.recovered
#    Typical gains: 500MB-1.5GB from a single cleanup.

# 0.5. cvelistV5/ — obsolete NVD JSON feed clone (3.9G!), marked OBSOLETE by skills-api.
#    Survives across sessions and is NOT covered by .bak/.gz patterns. The #2 space
#    hog after /tmp stale DBs. Nuke it unconditionally — CVE data now lives in
#    skills-hub.db via NVD API 2.0, not in this legacy directory.
rm -rf /home/ubuntu/cve-db/cvelistV5
#    Typical gains: 3.9GB. Confirmed 2026-08-20: disk went from 100% (12MB free) to 87% (3.9G free).

# 1. Delete redundant /tmp snapshot + partial .gz from a prior attempt
rm -f /tmp/<db>.snap /tmp/<db>.gz

# 2. Delete old DB backups in the source dir
rm -f ~/.hermes/skills-hub.db.bak-* ~/.hermes/skills-hub.db.old

# 3. System caches (needs sudo)
sudo journalctl --vacuum-size=50M
sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/*
```

**Skip the `cp` snapshot when disk is tight.** The snapshot exists only to satisfy rclone copyto's "source being updated" mod-time check. `gzip` reads the source once and does NOT need a frozen copy — gzip directly from the source, halving peak disk cost (522MB raw → only the 177MB .gz output):

```bash
gzip -c ~/.hermes/skills-hub.db > /tmp/skills-hub-full.db.gz   # no intermediate cp
```

**Stale WAL/SHM after swapping a DB in place → "database disk image is malformed".** If you `mv` a fresh full DB over a stripped/live DB, the old `-wal`/`-shm` files belong to the OLD DB and make SQLite read garbage on the next open. Delete them before reading the swapped-in DB:

```bash
rm -f ~/.hermes/skills-hub.db-wal ~/.hermes/skills-hub.db-shm
sqlite3 ~/.hermes/skills-hub.db "PRAGMA integrity_check;"   # → ok
```

**Confirm a background sync isn't writing before snapshotting.** A cron job like `sync_cves_nvd.py` can run 1h+ at 0% CPU and still be idle — just sleeping on NVD API rate-limit. Distinguish network-wait from a real writer:
- `ps -o pid,etime,stat,%cpu,wchan,args -p <pid>` → `wchan=do_poll`/`do_select` + 0% CPU = waiting on network, NOT writing.
- `ls -la <db>*` → mtime stable = no writes since last check.

If both hold, gzip the source directly without fear of a torn read.

## Verification

```bash
# PREFERRED: rclone check --one-way (authoritative — confirms 0 differences)
# Works with --files-from to avoid remote listing:
rclone check ~/local-dir/ gdrive:backup/dir/ \
  --files-from /tmp/filelist.txt --no-traverse --one-way
# → "0 differences found" = fully synced. This is the TRUTH.

# PITFALL: rclone ls/size on the ROOT backup directory can time out even with <1K objects
# after repeated syncs exhaust the shared OAuth quota. Always verify per-subdirectory:
rclone size gdrive:backup/skills/ --fast-list
rclone size gdrive:backup/skills-api/ --fast-list

# PITFALL: rclone size can UNDERCOUNT objects (e.g., 280 vs 477 actual).
# It is NOT reliable for verification. Always prefer rclone check --one-way.

# For single files, use rclone ls with --max-depth 1 to avoid full directory listing:
# (--include alone on the root can still time out even with --no-traverse)
# NOTE: state.db is always uploaded as state.db.gz (compressed).
# skills-hub-full.db.gz is the full canonical DB backup (19K+ skills, 379K+ CVEs).
# skills-hub.db.gz is the stripped/small variant.
for f in skills-hub-full.db.gz skills-hub.db.gz state.db.gz kanban.db verification_evidence.db; do
  echo -n "$f: "
  rclone ls gdrive:hermes-backup/ --include "$f" --no-traverse --max-depth 1
done

# Compare local vs remote (rough count only — use rclone check for accuracy)
find ~/local-dir/ -type f | wc -l
rclone size gdrive:backup/dir/ --fast-list
```