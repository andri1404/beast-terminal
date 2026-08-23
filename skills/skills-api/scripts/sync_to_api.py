#!/usr/bin/env python3
"""
sync_to_api.py — Push local skills-hub.db data to Cloudflare Workers API
Uses the /sync/cves and /sync/skills endpoints.
"""
import sqlite3
import json
import urllib.request
import ssl
import time
import sys

API_URL = "https://skills-api.anzanesia.uk"
API_KEY = "hermes-logs-2026"
DB_PATH = "/home/ubuntu/.hermes/skills-hub.db"

def api_post(endpoint: str, data: dict, timeout: int = 60) -> dict:
    """POST JSON to API."""
    url = f"{API_URL}{endpoint}"
    body = json.dumps(data).encode("utf-8")
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": API_KEY,
            "User-Agent": "Hermes-Sync/1.0",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode()[:200]}"}
    except Exception as e:
        return {"error": str(e)}

def api_get(endpoint: str) -> dict:
    """GET from API."""
    url = f"{API_URL}{endpoint}"
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Hermes-Sync/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def sync_cves(since_date: str = "2026-08-09", batch_size: int = 50):
    """Sync new CVEs from local DB to remote API."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT cve_id, year, description, vendor, product, cvss_score, cvss_severity, date_published, cwe
        FROM cves WHERE date_published >= ? ORDER BY date_published DESC
    """, (since_date,))
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        print("No new CVEs to sync")
        return
    
    cves = [{
        "cve_id": r[0], "year": r[1], "description": r[2], "vendor": r[3],
        "product": r[4], "cvss_score": r[5], "cvss_severity": r[6],
        "date_published": r[7], "cwe": r[8]
    } for r in rows]
    
    total = len(cves)
    print(f"Syncing {total} CVEs to {API_URL}/sync/cves...")
    
    sent = inserted = skipped = 0
    for i in range(0, total, batch_size):
        batch = cves[i:i + batch_size]
        result = api_post("/sync/cves", {"cves": batch, "batch_size": batch_size})
        if "error" in result:
            print(f"  Batch {i//batch_size + 1}: ERROR - {result['error']}")
            continue
        inserted += result.get("inserted", 0)
        skipped += result.get("skipped", 0)
        sent += len(batch)
        print(f"  Batch {i//batch_size + 1}: {result.get('inserted', 0)} ins, {result.get('skipped', 0)} skip ({sent/total*100:.0f}%)")
        if i + batch_size < total:
            time.sleep(0.5)
    
    print(f"Done: {sent}/{total} sent, {inserted} inserted, {skipped} skipped")

if __name__ == "__main__":
    print("Remote Stats:", api_get("/stats"))
    sync_cves()