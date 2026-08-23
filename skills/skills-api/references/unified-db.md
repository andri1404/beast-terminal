# Unified DB Architecture

Single SQLite database replacing 19,482 individual SKILL.md files + separate CVE DB.

## Schema

```sql
-- Skills
CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    tags TEXT,              -- JSON array
    content TEXT NOT NULL,  -- full markdown body
    source TEXT,
    original_path TEXT,
    size_bytes INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

-- CVEs (with Exploit-DB columns)
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

-- FTS5 indexes
CREATE VIRTUAL TABLE skills_fts USING fts5(name, description, content, tags, content='skills', content_rowid='id');
CREATE VIRTUAL TABLE cves_fts USING fts5(cve_id, description, vendor, product, content='cves', content_rowid='id');
```

## Build Stats

| Metric | Value |
|---|---|
| Skills | 19,374 |
| CVEs | 374,319 |
| CVEs with Exploits | 25,012 (6.7%) |
| Total Exploit Refs | 30,587 |
| DB size | ~506 MB |
| Compressed (.gz) | ~173 MB |
| Build time | ~57 seconds |
| RAM usage | ~32 MB (SQLite cache) |

## Key Patterns

### FTS5 Search with JOIN
```sql
-- Search skills
SELECT s.name, s.description, s.category 
FROM skills_fts f JOIN skills s ON f.rowid = s.id 
WHERE skills_fts MATCH 'sql injection' 
ORDER BY rank LIMIT 10;

-- Search CVEs with severity + exploit filter
SELECT c.cve_id, c.description, c.cvss_score, c.exploit_count
FROM cves_fts f JOIN cves c ON f.rowid = c.id
WHERE cves_fts MATCH 'apache' AND c.cvss_severity='CRITICAL' AND c.exploit_count > 0
ORDER BY rank LIMIT 10;
```

### YAML Frontmatter Quirks
Some skills use list types for `category` or `description` fields. Always sanitize:
```python
def _str(val, default=''):
    if isinstance(val, list):
        return ', '.join(str(v) for v in val)
    return str(val) if val else default
```

## PITFALLS

1. **FTS5 column access:** FTS5 virtual tables only have indexed columns. Always JOIN with parent table for non-indexed columns.
2. **YAML list-type fields:** Some SKILL.md files use lists for `category`/`description`. Convert to string before INSERT.
3. **No auto-sync:** FTS5 tables don't auto-update when parent table changes. Use `INSERT INTO skills_fts(skills_fts) VALUES('rebuild')` after bulk inserts.
4. **WAL mode:** The DB uses WAL journal mode. Don't delete `.db-wal` or `.db-shm` files.

## File Locations

| File | Purpose |
|---|---|
| `~/.hermes/skills-hub.db` | Unified database |
| `~/.hermes/skills-api/build_hub.py` | Rebuild script |
| `~/.hermes/skills-api/enrich_exploitdb.py` | Exploit-DB enrichment script |
| `~/.hermes/skills-api/mcp_server_v2.py` | Lightweight MCP server (v2) |
| `~/.hermes/skills-api/mcp_server.py` | Legacy MCP server (v1) |
| `~/.hermes/skills-api/server.py` | Legacy HTTP API (v1) |

## GDrive Download

`skills-hub.db.gz` (173MB): https://drive.google.com/uc?export=download&id=1zwDIHNj5kLsHU4jN6hYqEGSW0wVOFY9o