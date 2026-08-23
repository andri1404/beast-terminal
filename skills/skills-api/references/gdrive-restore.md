# GDrive DB Restore — Quick Reference

**GDrive File ID:** `1zwDIHNj5kLsHU4jN6hYqEGSW0wVOFY9o`
**Compressed:** 175MB (gzip) → **Extracted:** 514MB SQLite
**Contents:** 19,374 skills + 374,319 CVEs + 25,012 exploit-ready

## One-shot restore

```bash
# 1. Download (gdown handles GDrive confirm flow)
source /home/ubuntu/pentest-venv/bin/activate
pip install gdown -q 2>/dev/null
gdown "1zwDIHNj5kLsHU4jN6hYqEGSW0wVOFY9o" -O /tmp/skills-hub.db.gz

# 2. Verify compressed file
file /tmp/skills-hub.db.gz
# → gzip compressed data, was "skills-hub.db", original size 538800128

# 3. Backup current DB
cp ~/.hermes/skills-hub.db ~/.hermes/skills-hub.db.bak-$(date +%Y%m%d-%H%M)

# 4. Decompress & verify integrity
gunzip -c /tmp/skills-hub.db.gz > ~/.hermes/skills-hub.db.new
python3 -c "
import sqlite3
db = sqlite3.connect('$HOME/.hermes/skills-hub.db.new')
print('integrity:', db.execute('PRAGMA integrity_check').fetchone()[0])
s = db.execute('SELECT COUNT(*) FROM skills').fetchone()[0]
c = db.execute('SELECT COUNT(*) FROM cves').fetchone()[0]
e = db.execute('SELECT COUNT(*) FROM cves WHERE exploit_count>0').fetchone()[0]
print(f'skills:{s} cves:{c} exploits:{e}')
"
# Expected: integrity: ok, skills:19374, cves:374319, exploits:25012

# 5. Swap & restart
mv ~/.hermes/skills-hub.db.new ~/.hermes/skills-hub.db
fuser -k 8765/tcp 2>/dev/null; sleep 1
cd ~/.hermes/skills-api && bash start-all.sh

# 6. Cleanup
rm -f /tmp/skills-hub.db.gz
```

## Verification

```bash
# v1 HTTP API
curl -s http://127.0.0.1:8765/health

# v2 MCP (stdio test)
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_stats","arguments":{}}}\n' | python3 ~/.hermes/skills-api/mcp_server_v2.py 2>/dev/null
```

## Pitfalls

- **`curl -L` / `wget` fail** — Google Drive shows virus scan warning page. Must use `gdown`.
- **v1 server OOM** — v1 `server.py` loads 19K files into RAM (~1GB). On low-memory VMs (2GB), it may get OOM-killed. The DB swap is fine; v2 MCP reads from SQLite without loading.
- **v1 stats show ~100 skills** — expected. v1 reads from `~/.hermes/skills/` (file-based), not from the DB. Use v2 MCP for the full index.