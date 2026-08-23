#!/usr/bin/env python3
"""
update_cves.py — Pull latest CVEs from NVD API 2.0 and insert into skills-hub.db
No external cve.db needed — works directly against the unified hub.

Usage:
    python3 ~/.hermes/skills-api/scripts/update_cves.py

Then follow with:
    curl -skL "https://gitlab.com/exploit-database/exploitdb/-/raw/main/files_exploits.csv" -o /tmp/exploitdb.csv
    python3 ~/.hermes/skills-api/enrich_exploitdb.py
"""
import sqlite3
import json
import ssl
import time
import urllib.request
import os

DB_PATH = os.path.expanduser("~/.hermes/skills-hub.db")
NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
RESULTS_PER_PAGE = 2000

def pull_and_insert():
    start = time.time()
    
    # 1. Get latest date from DB
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")
    
    c = conn.cursor()
    c.execute("SELECT MAX(date_published) FROM cves")
    latest = c.fetchone()[0]
    print(f"Latest CVE in DB: {latest}")
    
    # 2. Pull from NVD API (from latest date to 2 days ahead)
    from datetime import datetime, timedelta
    start_date = f"{latest}T00:00:00.000" if latest else "2026-01-01T00:00:00.000"
    end_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT00:00:00.000")
    params = f"?pubStartDate={start_date}&pubEndDate={end_date}&resultsPerPage={RESULTS_PER_PAGE}"
    
    ctx = ssl.create_default_context()
    req = urllib.request.Request(NVD_API + params)
    req.add_header("User-Agent", "Hermes-Pentest/1.0")
    
    print(f"Pulling NVD API: {start_date} -> {end_date}")
    resp = urllib.request.urlopen(req, timeout=60, context=ctx)
    data = json.loads(resp.read())
    
    total = data.get("totalResults", 0)
    print(f"  {total} CVEs returned")
    
    # 3. Get existing CVE IDs to skip duplicates
    c.execute("SELECT cve_id FROM cves")
    existing = set(row[0] for row in c.fetchall())
    
    # 4. Parse and insert
    inserted = 0
    skipped = 0
    vulns = data.get("vulnerabilities", [])
    
    for vuln in vulns:
        cve_data = vuln.get("cve", {})
        cve_id = cve_data.get("id", "")
        
        if cve_id in existing:
            skipped += 1
            continue
        
        year = int(cve_id.split("-")[1]) if cve_id.startswith("CVE-") else 0
        
        # Description
        descriptions = cve_data.get("descriptions", [])
        desc = ""
        for d in descriptions:
            if d.get("lang") == "en":
                desc = d.get("value", "")
                break
        if not desc and descriptions:
            desc = descriptions[0].get("value", "")[:500]
        
        # CVSS
        metrics = cve_data.get("metrics", {})
        cvss_score = None
        cvss_severity = None
        
        for metric_type in ["cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
            metric_list = metrics.get(metric_type, [])
            if metric_list:
                cvss_data = metric_list[0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                cvss_severity = cvss_data.get("baseSeverity", "")
                if cvss_severity:
                    cvss_severity = cvss_severity.upper()
                break
        
        # CWE
        weaknesses = cve_data.get("weaknesses", [])
        cwe = ""
        if weaknesses:
            desc_list = weaknesses[0].get("description", [])
            if desc_list:
                cwe = desc_list[0].get("value", "")
        
        # Vendor/Product from CPE
        vendor = ""
        product = ""
        cpe = cve_data.get("configurations", [])
        try:
            for config in cpe:
                nodes = config.get("nodes", [])
                for node in nodes:
                    cpe_list = node.get("cpeMatch", [])
                    for cpe_item in cpe_list:
                        criteria = cpe_item.get("criteria", "")
                        if criteria.startswith("cpe:2.3:"):
                            parts = criteria.split(":")
                            if len(parts) >= 5:
                                vendor = parts[3] if parts[3] != "*" else vendor
                                product = parts[4] if parts[4] != "*" else product
                                if vendor and product:
                                    break
                    if vendor:
                        break
                if vendor:
                    break
        except:
            pass
        
        date_published = cve_data.get("published", "")[:10]
        
        try:
            conn.execute(
                """INSERT INTO cves (cve_id, year, description, vendor, product, cvss_score, cvss_severity, date_published, cwe)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (cve_id, year, desc, vendor, product, cvss_score, cvss_severity, date_published, cwe)
            )
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1
    
    conn.commit()
    
    # 5. Rebuild FTS5
    print(f"\nInserted: {inserted} | Skipped: {skipped}")
    print("Rebuilding FTS5 indexes...")
    conn.execute("INSERT INTO cves_fts(cves_fts) VALUES('rebuild')")
    conn.execute("INSERT INTO skills_fts(skills_fts) VALUES('rebuild')")
    conn.commit()
    
    # 6. Final stats
    c.execute("SELECT COUNT(*) FROM cves")
    total_cves = c.fetchone()[0]
    c.execute("SELECT MAX(date_published) FROM cves")
    new_latest = c.fetchone()[0]
    
    elapsed = time.time() - start
    print(f"\n{'='*50}")
    print(f"CVE update complete ({elapsed:.0f}s)")
    print(f"   Total CVEs: {total_cves:,}")
    print(f"   New: {inserted} | Latest: {new_latest}")
    print(f"{'='*50}")
    
    conn.close()
    return inserted

if __name__ == "__main__":
    pull_and_insert()