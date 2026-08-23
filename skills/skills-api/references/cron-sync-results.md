# Cron CVE Sync — Verified Results

## 2026-08-15: Ultra-fast 2-day NVD API sync + Exploit-DB enrichment

### Sync timing
- **Runtime**: ~60s (2-day window via NVD API 2.0)
- **Start state**: 375,886 CVEs
- **End state**: 375,930 CVEs
- **New CVEs**: 44 (Aug 13-15, 2026)
- **Method**: Single `execute_code` script, `resultsPerPage=2000`, 1 page

### NVD JSON feed approach — FAILED
- **Annual feed URL**: `https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-{year}.json.gz` (200 OK)
- **Download speed**: ~64 KB/s from this server — too slow for cron (would take ~6 min for 23MB)
- **Modified/recent feeds**: `nvdcve-2.0-{year}-modified.json.gz` and `nvdcve-2.0-{year}-recent.json.gz` return 404
- **Verdict**: NOT viable for automated cron. Use NVD API 2.0 with small date windows instead.

### Enrichment
- Exploit-DB CSV: 9.8MB, 25,049 unique CVE-to-exploit mappings
- CVEs with exploits: 25,020 / 375,930 (6.66%)
- Total exploit refs: 30,595
- Runtime: ~1s

### Key takeaway
The 2-day NVD API window is the ONLY reliable approach for frequent cron. Full sync via `sync_cves_nvd.py` hits HTTP 503 rate limits and times out. JSON feed download is too slow at 64 KB/s. The ultra-fast approach (2-3 days) completes in ~20-60s reliably.

## 2026-08-14: Full sync_cves_nvd.py run

### Sync timing
- **Runtime**: 43.1 min (not the previously claimed 1.3h)
- **Start state**: 2,518 existing CVEs in DB
- **End state**: 66,688 CVEs
- **New CVEs**: 64,170

### Per-year breakdown

| Year | CVEs Added | Notes |
|------|-----------|-------|
| 2020 | 0 | Already had 2020 CVEs |
| 2021 | 6,960 | 4 pages (6,960 total) |
| 2022 | 8,377 | 5 pages (8,379 total) |
| 2023 | 10,185 | 6 pages (10,185 total) |
| 2024 | 0 | Already had 2024 CVEs |
| 2025 | 16,542 | 9 pages (16,554 total) |
| 2026 | 22,106 | 12 pages (22,140 total) |

### Key observations
- The script only covers 2020-2026 (hardcoded `range(2020, 2027)`)
- Pre-2020 CVEs are NOT pulled — this is why the DB has 67K, not 375K+
- 2024 had 0 new CVEs because the existing 2,518 already covered 2024
- NVD API pagination: 2000/page, 6.5s sleep between pages
- Fastest years: 2021 (4 pages), 2022 (5 pages)
- Slowest year: 2026 (12 pages, 22,140 CVEs in Q1 alone)

### Enrichment
- Exploit-DB CSV: 9.8MB, 25,049 unique CVE-to-exploit mappings
- Matched in DB: 456 CVEs (0.68% of 66,688)
- Total exploit refs: 494
- **Why so low**: Most Exploit-DB exploits are for pre-2020 CVEs, not in this DB
- Full GDrive DB has 25,020 CVEs with exploits (6.7% of 375K+)

### Exploit-DB CSV download
```bash
curl -skL "https://gitlab.com/exploit-database/exploitdb/-/raw/main/files_exploits.csv" -o /tmp/exploitdb.csv
```
- Confirmed working (2026-08-14)
- 9.8MB, downloads in ~2s

### `conn.total_changes` bug confirmed
The enrich script reported `Updated rows: 6,605,186` — this is `conn.total_changes` which counts ALL operations since DB open (including the recent sync's 64K INSERTs), not the actual UPDATE count. The real stats are correct: 456 CVEs with exploits, 494 total refs.

### Memory note
The in-session memory claims "374,000+ CVEs, 25,000+ with exploits" — this refers to the **GDrive backup** (`/tmp/skills-hub-copy.db`, 542MB), not the NVD sync output. The NVD sync only covers 2020-2026.