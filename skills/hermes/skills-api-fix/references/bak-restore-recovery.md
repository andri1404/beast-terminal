# Quick Recovery: Restore from .bak File

When `skills-hub.db` has 0 rows in both `skills` and `cves` tables but the schema is intact (tables exist, FTS indexes exist), the `.bak` file is the fastest recovery path — no GDrive download needed.

## Symptoms
- `SELECT COUNT(*) FROM skills` → 0
- `SELECT COUNT(*) FROM cves` → 0
- Tables exist, schema intact
- `skills-hub.db.bak` exists (2.2MB typical)

## Two-DB Architecture
Both these files must be checked — they can diverge:
- `/home/ubuntu/.hermes/skills-hub.db` — primary DB, used by MCP v2
- `/home/ubuntu/.hermes/skills-api/skills_hub.db` — secondary DB, used by v1 API server

## Recovery Flow

### Step 1: Check both DBs
```python
import sqlite3
for p in ['/home/ubuntu/.hermes/skills-hub.db', '/home/ubuntu/.hermes/skills-api/skills_hub.db']:
    db = sqlite3.connect(p)
    skills = db.execute('SELECT COUNT(*) FROM skills').fetchone()[0]
    cves = db.execute('SELECT COUNT(*) FROM cves').fetchone()[0]
    db.close()
    print(f"{p}: skills={skills}, cves={cves}")
```

### Step 2: Check .bak file
```python
import sqlite3, os
bak = '/home/ubuntu/.hermes/skills-hub.db.bak'
if os.path.exists(bak):
    db = sqlite3.connect(bak)
    skills = db.execute('SELECT COUNT(*) FROM skills').fetchone()[0]
    cves = db.execute('SELECT COUNT(*) FROM cves').fetchone()[0]
    db.close()
    print(f".bak: skills={skills}, cves={cves}, size={os.path.getsize(bak):,} bytes")
```

### Step 3: Restore from .bak (if skills > 0)
```python
import shutil
# Keep a safety copy of the empty DB
shutil.copy('/home/ubuntu/.hermes/skills-hub.db', '/home/ubuntu/.hermes/skills-hub.db.empty_bak')
# Restore
shutil.copy('/home/ubuntu/.hermes/skills-hub.db.bak', '/home/ubuntu/.hermes/skills-hub.db')
```

### Step 4: Sync from local disk (catch any new skills not in .bak)
Use the local disk sync from the main skill (INSERT OR REPLACE loop over `~/.hermes/skills/*/SKILL.md`).

### Step 5: Copy to secondary DB if needed
If `skills-api/skills_hub.db` is also empty:
```python
shutil.copy('/home/ubuntu/.hermes/skills-hub.db', '/home/ubuntu/.hermes/skills-api/skills_hub.db')
```

### Step 6: Verify
```python
# Both should show skills > 0
for p in ['/home/ubuntu/.hermes/skills-hub.db', '/home/ubuntu/.hermes/skills-api/skills_hub.db']:
    db = sqlite3.connect(p)
    print(f"{p}: skills={db.execute('SELECT COUNT(*) FROM skills').fetchone()[0]}")
    db.close()
```

## Pitfalls
- **The .bak file is typically skills-only**: It won't have CVE data (0 CVEs). CVE recovery needs the GDrive path or NVD sync.
- **The .bak may be stale**: Check the count vs. local disk SKILL.md files. If .bak has 170 and local has 171, sync after restore.
- **Both DBs can go empty simultaneously**: Always check both files.
- **.bak is 2.2MB vs full DB 500MB+**: The .bak was created from a stripped DB — it only has skills, no CVEs. It's a quick skills recovery, not a full DB replacement.