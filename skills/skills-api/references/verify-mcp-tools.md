# MCP Tools Verification Checklist

Run after restarting the API to verify all 10 MCP tools are operational.

## Prerequisites

API must be running on `http://127.0.0.1:8765`. Verify:

```bash
curl -sk --connect-timeout 3 -H "X-API-Key: hermes-logs-2026" "http://127.0.0.1:8765/stats" | python3 -m json.tool
```

Expected: `{"total_skills": 19455, "total_categories": ..., "total_tags": ...}`

## Skills Tools (6)

| # | Tool | Test Call | Expected |
|---|------|-----------|----------|
| 1 | `get_stats` | `{}` | total_skills, total_categories, total_tags, last_reload |
| 2 | `list_skills` | `{"limit": 5}` | 5 results with name, description, tags |
| 3 | `search_skills` | `{"query": "sql injection", "limit": 3}` | Returns matching skills |
| 4 | `get_skill` | `{"name": "payloads-sql-injection-sqlmap"}` | Full content with frontmatter, size_bytes |
| 5 | `get_categories` | `{}` | categories dict with counts |
| 6 | `search_by_tag` | `{"tag": "sqli", "limit": 3}` | Skills tagged "sqli" |

## CVE Tools (4)

| # | Tool | Test Call | Expected |
|---|------|-----------|----------|
| 7 | `cve_stats` | `{}` | total, by_year, by_severity, top_vendors |
| 8 | `cve_recent` | `{"days": 3}` | Recent CVEs with descriptions, scores |
| 9 | `search_cve` | `{"query": "apache", "limit": 3}` | CVEs matching query |
| 10 | `get_cve` | `{"cve_id": "CVE-2026-33453"}` | Full CVE details |

## Quick Smoke Test (all 4 in parallel)

```
mcp__skills_api__get_stats: {}
mcp__skills_api__list_skills: {"limit": 5}
mcp__skills_api__cve_stats: {}
mcp__skills_api__cve_recent: {"days": 1}
```

All 4 should return data, not connection-refused errors.