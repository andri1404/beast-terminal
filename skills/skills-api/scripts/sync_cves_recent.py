#!/usr/bin/env python3
"""Targeted sync: only pull recent CVEs (last 30 days)"""
import sqlite3, json, ssl, time, urllib.request, urllib.error
from datetime import datetime, timedelta

DB_PATH = "/home/ubuntu/.hermes/skills-hub.db"
NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
RESULTS_PER_PAGE = 500

def parse_cve(cve_data):
    cve_id = cve_data.get("id", "")
    year = int(cve_id.split("-")[1]) if cve_id.startswith("CVE-") else 0
    desc = ""
    for d in cve_data.get("descriptions", []):
        if d.get("lang") == "en": desc = d.get("value", ""); break
    if not desc: desc = cve_data.get("descriptions", [{}])[0].get("value", "")
    metrics = cve_data.get("metrics", {})
    cvss_score, cvss_severity = None, None
    for mt in ["cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
        ml = metrics.get(mt, [])
        if ml:
            cd = ml[0].get("cvssData", {})
            cvss_score = cd.get("baseScore")
            cvss_severity = (cd.get("baseSeverity", "") or "").upper()
            break
    cwe = ""
    try:
        w = cve_data.get("weaknesses", [])
        if w and w[0].get("description"): cwe = w[0]["description"][0].get("value", "")
    except: pass
    vendor, product = "", ""
    try:
        for config in cve_data.get("configurations", []):
            for node in config.get("nodes", []):
                for cpe_item in node.get("cpeMatch", []):
                    c = cpe_item.get("criteria", "")
                    if c.startswith("cpe:2.3:"):
                        parts = c.split(":")
                        if len(parts) >= 5:
                            vendor = parts[3] if parts[3] != "*" else vendor
                            product = parts[4] if parts[4] != "*" else product
                            if vendor and product: break
                if vendor: break
            if vendor: break
    except: pass
    date = cve_data.get("published", "")[:10]
    return (cve_id, year, desc, vendor, product, cvss_score, cvss_severity, date, cwe)

def pull_month(year, month):
    """Pull CVEs for a single month."""
    ctx = ssl.create_default_context()
    if month == 12:
        end_date = f"{year}-12-31T23:59:59.999"
    else:
        end_day = 31 if month in [1,3,5,7,8,10,12] else 30
        if month == 2:
            end_day = 29 if year % 4 == 0 else 28
        end_date = f"{year}-{month:02d}-{end_day}T23:59:59.999"
    
    start_date = f"{year}-{month:02d}-01T00:00:00.000"
    
    all_vulns = []
    start_index = 0
    pages = 0
    
    while True:
        params = (f"?pubStartDate={start_date}&pubEndDate={end_date}"
                  f"&resultsPerPage={RESULTS_PER_PAGE}&startIndex={start_index}")
        url = NVD_API + params
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Hermes-Pentest/1.0")
        
        try:
            resp = urllib.request.urlopen(req, timeout=90, context=ctx)
            data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 404: break
            print(f" HTTP{e.code}", end="", flush=True)
            time.sleep(10)
            continue
        except Exception as e:
            print(f" ERR", end="", flush=True)
            time.sleep(10)
            continue
        
        total = data.get("totalResults", 0)
        vulns = data.get("vulnerabilities", [])
        all_vulns.extend(vulns)
        pages += 1
        print(f"\r    page {pages}: {len(all_vulns)}/{total}", end="", flush=True)
        
        start_index += len(vulns)
        if start_index >= total or len(vulns) == 0:
            break
        time.sleep(6.5)
    
    print()
    return all_vulns

def main():
    start = time.time()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA cache_size=-128000")
    
    c = conn.cursor()
    c.execute("SELECT cve_id FROM cves")
    existing = set(row[0] for row in c.fetchall())
    print(f"Existing: {len(existing):,} CVEs")
    
    total_ins = 0
    
    # Sync last 3 months
    now = datetime.utcnow()
    months = []
    for i in range(3):
        d = now - timedelta(days=30 * i)
        yr, mo = d.year, d.month
        if (yr, mo) not in months:
            months.append((yr, mo))
    
    for year, month in sorted(months):
        print(f"  {year}-{month:02d}:", end="", flush=True)
        vulns = pull_month(year, month)
        
        batch = []
        for vuln in vulns:
            cve_data = vuln.get("cve", {})
            cve_id = cve_data.get("id", "")
            if cve_id in existing:
                continue
            row = parse_cve(cve_data)
            batch.append(row)
            existing.add(cve_id)
        
        if batch:
            conn.executemany(
                "INSERT INTO cves (cve_id, year, description, vendor, product, cvss_score, cvss_severity, date_published, cwe) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                batch
            )
            total_ins += len(batch)
        
        conn.commit()
        print(f"  +{len(batch)} inserted")
    
    if total_ins > 0:
        print("Rebuilding FTS5...")
        conn.execute("INSERT INTO cves_fts(cves_fts) VALUES('rebuild')")
        conn.commit()
    
    c.execute("SELECT COUNT(*) FROM cves")
    total = c.fetchone()[0]
    elapsed = time.time() - start
    
    print(f"\n{'='*60}")
    print(f"Sync complete! ({elapsed:.0f}s)")
    print(f"Total CVEs: {total:,} (new: {total_ins:,})")
    print(f"{'='*60}")
    conn.close()

if __name__ == "__main__":
    main()