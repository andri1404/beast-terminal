# GDrive Skills-Hub DB Restore

## Quick Restore

```bash
# Download from GDrive (183MB gzip → 514MB SQLite)
gdown "1zwDIHNj5kLsHU4jN6hYqEGSW0wVOFY9o" -O /tmp/skills-hub-dl.db

# Decompress — PITFALL: file is gzip, not raw SQLite
gunzip -c /tmp/skills-hub-dl.db > /tmp/skills-hub-full.db

# Verify — expect 19374 skills
python3 -c "import sqlite3; db=sqlite3.connect('/tmp/skills-hub-full.db'); print(db.execute('SELECT COUNT(*) FROM skills').fetchone()[0])"

# Backup current + swap
cp /home/ubuntu/.hermes/skills-hub.db /home/ubuntu/.hermes/skills-hub.db.bak-$(date +%Y%m%d-%H%M)
mv /tmp/skills-hub-full.db /home/ubuntu/.hermes/skills-hub.db
```

## Full DB Stats
- Size: ~514MB
- Skills: 19,374
- CVEs: 374,319
- CVEs with exploits: 25,012

## PITFALL — gzip compression
The GDrive file downloads as 183MB but is gzip compressed. Running `gdown` directly produces a `.db` file that fails `sqlite3.connect()` with `file is not a database`. Always decompress with `gunzip -c` before use.

## PITFALL — /tmp/skills-hub-copy.db may not exist
The `/tmp/skills-hub-copy.db` path is ephemeral. If missing, use the GDrive download above.