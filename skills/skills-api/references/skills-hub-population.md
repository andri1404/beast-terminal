# Skills-Hub DB Population from Local Files

When `skills-hub.db` is empty (0 skills, 0 CVEs) but the local `~/.hermes/skills/` directory has skill files, the MCP server v2 won't find any skills. The v1 REST API server loads from files directly, but the v2 MCP server reads from the SQLite DB.

## Quick Population Script

```python
import sqlite3, yaml
from pathlib import Path

DB_PATH = "/home/ubuntu/.hermes/skills-hub.db"
SKILLS_DIR = "/home/ubuntu/.hermes/skills"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")

skill_files = list(Path(SKILLS_DIR).rglob("SKILL.md"))
count = 0

for md_file in skill_files:
    try:
        with open(md_file) as f:
            content = f.read()
        
        name = md_file.parent.name
        category = md_file.parent.parent.name if md_file.parent.parent != Path(SKILLS_DIR) else name
        
        description = ""
        tags = ""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    fm = yaml.safe_load(parts[1])
                    description = fm.get('description', '')[:500] if fm else ''
                    tags = ','.join(fm.get('tags', [])) if fm and fm.get('tags') else ''
                except:
                    pass
        
        conn.execute(
            "INSERT OR REPLACE INTO skills (name, category, description, tags, content, size_bytes) VALUES (?,?,?,?,?,?)",
            (name, category, description, tags, content, len(content))
        )
        count += 1
    except Exception as e:
        print(f"Error {name}: {e}")

conn.commit()
conn.close()
print(f"Synced {count} skills to DB")
```

## When to Run

- After `start-all.sh` has the v1 API running with 89 skills but MCP v2 returns 0 results
- After fresh clone/restore where `skills-hub.db` was deleted or replaced
- When `python3 -c "import sqlite3; conn=sqlite3.connect('$HOME/.hermes/skills-hub.db'); print(conn.execute('SELECT COUNT(*) FROM skills').fetchone()[0])"` returns 0

## Verification

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('$HOME/.hermes/skills-hub.db')
print(f'skills: {conn.execute(\"SELECT COUNT(*) FROM skills\").fetchone()[0]}')
print(f'cves: {conn.execute(\"SELECT COUNT(*) FROM cves\").fetchone()[0]}')
conn.close()
"
```

## Notes

- This only populates skills, not CVEs. For CVEs, use `scripts/update_cves.py` from the NVD API.
- The v1 REST API (`server.py`) loads from files directly and doesn't need the DB — it's only the MCP v2 server that reads from SQLite.
- Run this via `execute_code` tool, not `terminal()` — Hermes gateway may block SQLite access from terminal.