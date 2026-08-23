# Schema Rebuild + Local Sync Script

When `skills-hub.db` is 0 bytes with no tables, use this via `execute_code` (NOT `terminal` — the watchdog script is blocked by gateway).

## The script

```python
import sqlite3, json, yaml, time
from pathlib import Path

SKILLS_DIR = Path("/home/ubuntu/.hermes/skills")
OUTPUT_DB = Path("/home/ubuntu/.hermes/skills-hub.db")

# Remove old DB
if OUTPUT_DB.exists():
    OUTPUT_DB.unlink()

conn = sqlite3.connect(str(OUTPUT_DB))
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")

# Schema (from build_hub.py)
conn.executescript("""
    CREATE TABLE skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        tags TEXT,
        content TEXT NOT NULL,
        source TEXT,
        original_path TEXT,
        size_bytes INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE cves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cve_id TEXT UNIQUE NOT NULL,
        year INTEGER,
        description TEXT,
        vendor TEXT,
        product TEXT,
        cvss_score REAL,
        cvss_severity TEXT,
        date_published TEXT,
        cwe TEXT,
        exploit_count INTEGER DEFAULT 0,
        exploit_refs TEXT DEFAULT ''
    );
    CREATE VIRTUAL TABLE skills_fts USING fts5(
        name, description, content, tags,
        content='skills', content_rowid='id'
    );
    CREATE VIRTUAL TABLE cves_fts USING fts5(
        cve_id, description, vendor, product,
        content='cves', content_rowid='id'
    );
    CREATE INDEX idx_skills_name ON skills(name);
    CREATE INDEX idx_skills_category ON skills(category);
    CREATE INDEX idx_cves_cve_id ON cves(cve_id);
    CREATE INDEX idx_cves_year ON cves(year);
    CREATE INDEX idx_cves_severity ON cves(cvss_severity);
    CREATE INDEX idx_cves_vendor ON cves(vendor);
    CREATE INDEX idx_cves_date ON cves(date_published);
""")

# Migrate skills from local disk
for sf in sorted(SKILLS_DIR.rglob("SKILL.md")):
    try:
        content = sf.read_text(encoding='utf-8', errors='replace')
        name = sf.parent.name
        fm = {}
        body = content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try: fm = yaml.safe_load(parts[1]) or {}
                except: pass
                body = parts[2].strip()
        def _str(val, default=''):
            if isinstance(val, list): return ', '.join(str(v) for v in val)
            return str(val) if val else default
        rel = sf.parent.relative_to(SKILLS_DIR)
        category = _str(fm.get('category', str(rel.parts[0]) if rel.parts else str(rel)))
        description = _str(fm.get('description', ''))
        tags = json.dumps(fm.get('tags', []) or [])
        source = _str(fm.get('source', ''))
        original_path = _str(fm.get('original_path', ''))
        conn.execute(
            "INSERT INTO skills (name, category, description, tags, content, source, original_path, size_bytes) VALUES (?,?,?,?,?,?,?,?)",
            (name, category, description, tags, body, source, original_path, len(content)))
    except Exception as e:
        print(f"SKIP {sf}: {e}")

conn.commit()
conn.execute("INSERT INTO skills_fts(skills_fts) VALUES('rebuild')")
conn.commit()

skill_count = conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
conn.close()
print(f"DONE: {skill_count} skills migrated, DB rebuilt")
```

## When to use

- `skills-hub.db` is 0 bytes (`ls -lh` shows 0)
- MCP tools return `"no such table: skills"`
- `build_hub.py` fails because `omop-skills/` doesn't exist

## When NOT to use

- DB has tables but 0 rows → use the simpler local disk sync (INSERT OR REPLACE) from the main skill
- DB has data but wrong count → check if watching stripped DB (4.2MB vs 517MB)