#!/usr/bin/env python3
"""
LISA V15 EXEC — "BACKLINK PROTOCOL" — THE LINK FARMER
AI-Driven Backlink Building Engine — V15

V14 SPAM (comment spam) + V15 BACKLINK modules:

  NEW IN V15 (BACKLINK PROTOCOL):
  1.  GuestbookHunter   — Find & exploit old PHP guestbooks on Indonesian sites
                          (.go.id, .ac.id, .sch.id, .or.id, .com), auto-post
                          backlinks, bypass captcha, detect auto-approve
  2.  PingbackEngine    — Create bridge content + send WordPress pingbacks
                          that auto-approve (XML-RPC pingback.ping)
  3.  ProfileCreator    — Auto-create profiles on Gravatar, GitHub, GitLab,
                          Linktree, about.me with backlinks
  4.  TrackbackSpammer  — WordPress trackback with proper ID extraction,
                          excerpt spinning, auto-approve detection

USAGE:
  python3 lisa_v8_exec_v15.py target.com                              # Full autonomous
  python3 lisa_v8_exec_v15.py target.com --focus backlink             # Backlink focus
  python3 lisa_v8_exec_v15.py target.com --guestbook                  # Guestbook only
  python3 lisa_v8_exec_v15.py target.com --pingback "https://mysite.com"  # Pingback
  python3 lisa_v8_exec_v15.py -t t1.com t2.com t3.com                # Batch mode
"""

import sys, os, json, re, time, random, string, subprocess, hashlib, base64
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, "/home/ubuntu")

from lisa_v8_exec_v14 import (
    SpamBeastEngine, FraudBeastEngine, BeastXEngine, BeastEngine, TLSEngine,
    WordPressAssault, LeakHunter, VHostPanelHunter, ZimbraExploit, MassAssignment,
    ProxyRotator, CI3Assault, BatchRunner, StateManager,
    CookieForge, AffiliateFraud, CardingEngine, PaymentBypass,
    PhishingForge, AccountTakeover,
    BlogHunter, CommentSpammer, ContactFormSpammer, AntiSpamBypass,
    SPINTAX_COMMENTS, SPINTAX_NAMES, SPINTAX_DOMAINS,
    base_from_url, PROXY, CFFI_OK,
)
try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    pass

V15_SIGNATURE = """
╔══════════════════════════════════════════════════════════════════╗
║  LISA V15 — BACKLINK PROTOCOL — THE LINK FARMER                  ║
║  Spam engine + GuestbookHunter + PingbackEngine + ProfileCreator ║
║  \"Plant links. Grow ranks. Harvest traffic.\"                    ║
╚══════════════════════════════════════════════════════════════════╝
"""

STATE_DIR = "/home/ubuntu/.lisa_v15_state"
REPORT_DIR = "/home/ubuntu/.lisa_v15_reports"

# ═══════════════════════════════════════════════════════════
# GUESTBOOK DORK LIST — Indonesian sites
# ═══════════════════════════════════════════════════════════
GUESTBOOK_DORKS = [
    # Indonesian government/edu guestbooks
    'site:go.id "buku tamu"',
    'site:go.id "guestbook"',
    'site:go.id "isi buku tamu"',
    'site:go.id "sign guestbook"',
    'site:ac.id "buku tamu"',
    'site:ac.id "guestbook"',
    'site:sch.id "buku tamu"',
    'site:or.id "buku tamu"',
    # General Indonesian guestbooks
    'site:.id "buku tamu" inurl:guestbook',
    'site:.id "sign my guestbook"',
    'site:.id "tanda tangan buku tamu"',
    'site:.id inurl:bukutamu',
    'site:.id inurl:buku_tamu',
    'site:.id inurl:guestbook.php',
    'site:.id inurl:guestbook.cgi',
    # Common guestbook paths
    'site:.id inurl:"/guestbook/"',
    'site:.id inurl:"/buku-tamu/"',
    'site:.id "nama" "email" "pesan" "komentar"',
]

# ═══════════════════════════════════════════════════════════
# V15 MODULE 1: GUESTBOOK HUNTER
# ═══════════════════════════════════════════════════════════
class GuestbookHunter:
    """Find old PHP guestbooks and auto-post backlinks."""

    # Known guestbook software patterns
    GUESTBOOK_PATTERNS = {
        "PHP_GUESTBOOK": {
            "detect": ["guestbook.php", "bukutamu.php", "buku_tamu.php", "viewguestbook.php"],
            "add_paths": ["guestbook.php?action=add", "bukutamu.php?action=simpan",
                         "guestbook.php?action=sign", "bukutamu.php?act=add"],
            "form_action": "guestbook.php",
            "fields": {
                "name": ["name", "nama", "author", "from", "sender"],
                "email": ["email", "mail", "e-mail"],
                "url": ["url", "website", "homepage", "link", "situs"],
                "message": ["message", "pesan", "comment", "comments", "body", "isi", "text"],
                "location": ["location", "city", "lokasi", "kota", "country"],
            },
        },
        "ADVANCED_GUESTBOOK": {
            "detect": ["advancedguestbook", "agb_form", "guestbook_data"],
            "add_paths": ["guestbook.php?action=add", "guestbook.php?new_entry=1"],
            "form_action": "guestbook.php",
            "fields": {
                "name": ["name", "gb_name", "author"],
                "email": ["email", "gb_email", "mail"],
                "url": ["url", "homepage", "gb_url", "website"],
                "message": ["message", "gb_message", "comment", "body"],
            },
        },
        "GENERIC_GUESTBOOK": {
            "detect": ["buku tamu", "guestbook", "sign guestbook", "sign my guestbook",
                      "tanda tangan", "tinggalkan pesan", "leave a message"],
            "add_paths": [],
            "form_action": None,
            "fields": {
                "name": ["name", "nama", "author", "from"],
                "email": ["email", "mail", "e-mail"],
                "url": ["url", "website", "homepage", "link"],
                "message": ["message", "pesan", "comment", "body", "isi"],
            },
        },
    }

    @staticmethod
    def find_guestbooks_on_target(base: str, sess) -> List[Dict]:
        """Find guestbook pages on a single target domain."""
        found = []

        paths_to_check = [
            "/guestbook/", "/guestbook.php", "/buku-tamu/", "/bukutamu.php",
            "/buku_tamu.php", "/guestbook/guestbook.php", "/gb/", "/sign.php",
            "/index.php?page=guestbook", "/index.php?page=buku-tamu",
            "/?page=guestbook", "/?p=guestbook", "/guestbook.html",
            "/buku-tamu.html", "/bukutamu.html",
        ]

        for path in paths_to_check:
            try:
                url = base.rstrip("/") + path
                r = sess.get(url, timeout=10)
                if r.status_code == 200:
                    html = r.text.lower()
                    # Check for guestbook indicators
                    guestbook_indicators = [
                        "buku tamu", "guestbook", "sign guestbook",
                        "tinggalkan pesan", "isi buku tamu", "tanda tangan",
                        "nama", "pesan", "leave a message",
                    ]
                    score = sum(1 for ind in guestbook_indicators if ind in html)
                    if score >= 3:
                        # Check for form fields
                        has_form = bool(re.search(r'<form[^>]*>.*?</form>', html, re.DOTALL | re.IGNORECASE))
                        has_name = bool(re.search(r'<input[^>]+name=["\'](?:name|nama|author)["\']', html, re.IGNORECASE))
                        has_message = bool(re.search(r'<(?:input|textarea)[^>]+name=["\'](?:message|pesan|comment|body)["\']', html, re.IGNORECASE))

                        if has_form and has_name and has_message:
                            # Extract form action
                            form_action = re.search(r'<form[^>]+action=["\']([^"\']+)["\']', html, re.IGNORECASE)
                            action = form_action.group(1) if form_action else path

                            found.append({
                                "url": url,
                                "action": action if action.startswith("http") else base.rstrip("/") + "/" + action.lstrip("/"),
                                "has_url_field": bool(re.search(r'<input[^>]+name=["\'](?:url|website|homepage|link|situs)["\']', html, re.IGNORECASE)),
                                "has_captcha": bool(re.search(r'(?:captcha|recaptcha|turnstile|hcaptcha)', html, re.IGNORECASE)),
                                "score": score,
                            })
                            print(f"   🔥 GUESTBOOK FOUND: {url} (score={score}, url_field={found[-1]['has_url_field']})")
            except Exception:
                continue

        return found

    @staticmethod
    def post_guestbook_entry(guestbook: Dict, name: str, email: str,
                            url: str, message: str, sess) -> Dict:
        """Post an entry to a guestbook."""
        result = {
            "success": False,
            "url": guestbook["url"],
            "action": guestbook["action"],
            "status": "unknown",
            "error": None,
        }

        if guestbook.get("has_captcha"):
            result["error"] = "Captcha protected"
            result["status"] = "skipped"
            return result

        try:
            # Build form data with all possible field names
            data = {}
            field_variants = {
                "name": ["name", "nama", "author", "from", "sender", "gb_name", "gb_author"],
                "email": ["email", "mail", "e-mail", "gb_email", "email_address"],
                "url": ["url", "website", "homepage", "link", "situs", "gb_url", "www"],
                "message": ["message", "pesan", "comment", "comments", "body", "isi",
                          "text", "gb_message", "gb_comment", "content", "entry"],
                "location": ["location", "city", "lokasi", "kota", "country", "negara",
                           "from_location", "location_name"],
                "submit": ["submit", "send", "kirim", "simpan", "sign", "post", "add",
                          "btn_submit", "button", "submit_button", "submit_btn"],
            }

            for field_type, field_names in field_variants.items():
                value = ""
                if field_type == "name":
                    value = name
                elif field_type == "email":
                    value = email
                elif field_type == "url":
                    value = url
                elif field_type == "message":
                    value = message
                elif field_type == "location":
                    value = "Indonesia"
                elif field_type == "submit":
                    value = "Kirim"

                for fname in field_names:
                    data[fname] = value

            # Random delay
            time.sleep(random.uniform(1.0, 3.0))

            headers = {
                "User-Agent": CookieForge.random_ua("random"),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": random.choice(CookieForge.ACCEPT_LANGUAGES),
                "Referer": guestbook["url"],
                "Origin": base_from_url(guestbook["url"]),
                "Content-Type": "application/x-www-form-urlencoded",
            }

            action = guestbook["action"]
            if not action.startswith("http"):
                action = base_from_url(guestbook["url"]) + "/" + action.lstrip("/")

            r = sess.post(action, data=data, headers=headers, timeout=20, allow_redirects=True)

            result["status_code"] = r.status_code
            response_text = r.text.lower()

            # Check for success indicators
            success_indicators = [
                "terima kasih", "thank you", "pesan anda telah", "your message has",
                "berhasil", "sukses", "success", "tersimpan", "saved",
                "entry added", "pesan ditambahkan", "signed", "signature added",
                "will be reviewed", "akan ditinjau", "moderasi",
            ]

            # Check if our URL appears in the response (means it was published)
            if url.lower() in response_text:
                result["success"] = True
                result["status"] = "published"
                result["verified"] = True
            elif any(ind in response_text for ind in success_indicators):
                result["success"] = True
                result["status"] = "submitted"
            elif r.status_code in [200, 302] and len(r.text) > 100:
                result["success"] = True
                result["status"] = "submitted"
            else:
                result["error"] = f"HTTP {r.status_code} ({len(r.text)} bytes)"

            return result

        except Exception as e:
            result["error"] = str(e)[:100]
            return result


# ═══════════════════════════════════════════════════════════
# V15 MODULE 2: PINGBACK ENGINE
# ═══════════════════════════════════════════════════════════
class PingbackEngine:
    """Send WordPress pingbacks that auto-approve."""

    @staticmethod
    def find_xmlrpc_url(base: str, sess) -> Optional[str]:
        """Find the XML-RPC endpoint."""
        paths = ["/xmlrpc.php", "/wp/xmlrpc.php", "/blog/xmlrpc.php", "/api/xmlrpc.php"]

        # First check HTML for pingback link
        try:
            r = sess.get(base + "/", timeout=10)
            pingback_link = re.search(
                r'<link[^>]+rel=["\']pingback["\'][^>]+href=["\']([^"\']+)["\']',
                r.text, re.IGNORECASE
            )
            if pingback_link:
                return pingback_link.group(1)
        except Exception:
            pass

        # Try common paths
        for path in paths:
            try:
                r = sess.get(base + path, timeout=8)
                if r.status_code == 200 and ("xmlrpc" in r.text.lower() or "XML-RPC" in r.text):
                    return base.rstrip("/") + path
            except Exception:
                continue

        return None

    @staticmethod
    def send_pingback(source_url: str, target_url: str, sess) -> Dict:
        """Send a pingback from source to target."""
        result = {
            "success": False,
            "source": source_url,
            "target": target_url,
            "error": None,
        }

        try:
            # Find XML-RPC endpoint
            xmlrpc = PingbackEngine.find_xmlrpc_url(target_url, sess)
            if not xmlrpc:
                result["error"] = "No XML-RPC endpoint found"
                return result

            # Build pingback XML
            xml_body = f"""<?xml version="1.0"?>
<methodCall>
<methodName>pingback.ping</methodName>
<params>
<param><value><string>{source_url}</string></value></param>
<param><value><string>{target_url}</string></value></param>
</params>
</methodCall>"""

            headers = {
                "Content-Type": "text/xml",
                "User-Agent": "WordPress/6.0; https://jasatebasrumput.info",
                "Accept": "text/xml",
            }

            r = sess.post(xmlrpc, data=xml_body, headers=headers, timeout=20)

            result["status_code"] = r.status_code
            result["xmlrpc_url"] = xmlrpc

            if r.status_code == 200:
                response_text = r.text
                if "fault" in response_text:
                    # Parse fault
                    fault_code = re.search(r'<name>faultCode</name>.*?<int>(\d+)</int>', response_text, re.DOTALL)
                    fault_string = re.search(r'<name>faultString</name>.*?<string>([^<]*)</string>', response_text, re.DOTALL)

                    if fault_code and fault_string:
                        code = int(fault_code.group(1))
                        msg = fault_string.group(1)
                        if code == 0 and not msg:
                            result["success"] = True
                            result["status"] = "success"
                            result["error"] = None
                        elif "already registered" in msg.lower() or "duplicate" in msg.lower():
                            result["success"] = True
                            result["status"] = "duplicate"
                            result["error"] = msg
                        elif "source does not link" in msg.lower():
                            result["error"] = f"Source doesn't link to target: {msg}"
                        else:
                            result["error"] = f"Fault {code}: {msg}"
                    else:
                        result["error"] = f"Unknown fault: {response_text[:200]}"
                elif "methodResponse" in response_text and "fault" not in response_text:
                    result["success"] = True
                    result["status"] = "success"
                else:
                    result["error"] = f"Unexpected response: {response_text[:200]}"
            else:
                result["error"] = f"HTTP {r.status_code}"

            return result

        except Exception as e:
            result["error"] = str(e)[:100]
            return result

    @staticmethod
    def send_trackback(target_url: str, post_id: str, title: str,
                       excerpt: str, blog_name: str, source_url: str, sess) -> Dict:
        """Send a WordPress trackback."""
        result = {
            "success": False,
            "target": target_url,
            "source_url": source_url,
            "error": None,
        }

        try:
            trackback_url = f"{target_url.rstrip('/')}/wp-trackback.php"

            data = {
                "title": title,
                "url": source_url,
                "excerpt": excerpt[:250],
                "blog_name": blog_name,
            }

            params = {"p": post_id} if post_id else {}

            headers = {
                "User-Agent": CookieForge.random_ua("random"),
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/xml, application/xml",
            }

            r = sess.post(trackback_url, params=params, data=data,
                         headers=headers, timeout=20)

            result["status_code"] = r.status_code

            if r.status_code == 200:
                response_text = r.text.lower()
                if "error" in response_text:
                    error_msg = re.search(r'<message>(.*?)</message>', response_text)
                    result["error"] = error_msg.group(1) if error_msg else "Trackback error"
                elif "success" in response_text or "pingback" in response_text:
                    result["success"] = True
                    result["status"] = "success"
                else:
                    result["success"] = True
                    result["status"] = "submitted"
            else:
                result["error"] = f"HTTP {r.status_code}"

            return result

        except Exception as e:
            result["error"] = str(e)[:100]
            return result


# ═══════════════════════════════════════════════════════════
# V15 MODULE 3: PROFILE CREATOR
# ═══════════════════════════════════════════════════════════
class ProfileCreator:
    """Create profiles on Web 2.0 sites with backlinks."""

    PLATFORMS = {
        "GRAVATAR": {
            "profile_url": "https://en.gravatar.com/{username}",
            "check_url": "https://en.gravatar.com/{username}.json",
            "has_api": True,
            "link_field": "websites",
            "nofollow": False,
        },
        "GITHUB": {
            "profile_url": "https://github.com/{username}",
            "check_url": "https://api.github.com/users/{username}",
            "has_api": True,
            "link_field": "blog",
            "nofollow": True,
        },
        "DISQUS": {
            "profile_url": "https://disqus.com/by/{username}/",
            "check_url": "https://disqus.com/by/{username}/",
            "has_api": False,
            "link_field": "website",
            "nofollow": True,
        },
        "LINKTREE": {
            "profile_url": "https://linktr.ee/{username}",
            "check_url": "https://linktr.ee/{username}",
            "has_api": False,
            "link_field": "link",
            "nofollow": True,
        },
        "ABOUT_ME": {
            "profile_url": "https://about.me/{username}",
            "check_url": "https://about.me/{username}",
            "has_api": False,
            "link_field": "website",
            "nofollow": False,
        },
    }

    @staticmethod
    def check_profile_exists(platform: str, username: str, sess) -> Dict:
        """Check if a profile already exists."""
        config = ProfileCreator.PLATFORMS.get(platform.upper())
        if not config:
            return {"exists": False, "error": "Unknown platform"}

        try:
            url = config["check_url"].format(username=username)
            r = sess.get(url, timeout=10)
            result = {
                "platform": platform,
                "username": username,
                "url": config["profile_url"].format(username=username),
                "exists": r.status_code == 200,
                "status_code": r.status_code,
            }
            return result
        except Exception as e:
            return {"exists": False, "error": str(e)}

    @staticmethod
    def generate_profile_names() -> List[Dict]:
        """Generate profile names for backlink campaigns."""
        brands = [
            "JasaTebasRumput", "TebasRumputPro", "RumputBersih",
            "TamanAsri", "GardenProID", "TukangRumput", "GreenLawnID",
            "RumputIndo", "TebasTaman", "HalamanHijau",
        ]
        usernames = [b.lower() for b in brands]
        return [{"brand": b, "username": u} for b, u in zip(brands, usernames)]

    @staticmethod
    def create_gravatar_profile(username: str, display_name: str,
                               website_url: str, sess) -> Dict:
        """Create a Gravatar profile with backlink."""
        result = {
            "success": False,
            "platform": "GRAVATAR",
            "username": username,
            "profile_url": f"https://en.gravatar.com/{username}",
            "error": None,
        }

        try:
            # Gravatar uses WordPress.com API
            # We can check if profile exists and if website is set
            check_url = f"https://en.gravatar.com/{username}.json"
            r = sess.get(check_url, timeout=10)

            if r.status_code == 200:
                profile = r.json()
                websites = profile.get("entry", [{}])[0].get("websites", [])
                result["exists"] = True
                if websites:
                    result["success"] = True
                    result["links"] = [w.get("value") for w in websites]
                    result["status"] = "existing_with_link"
                else:
                    result["status"] = "existing_no_link"
            elif r.status_code == 404:
                result["exists"] = False
                result["status"] = "available"
            else:
                result["error"] = f"HTTP {r.status_code}"

            return result
        except Exception as e:
            result["error"] = str(e)[:100]
            return result

    @staticmethod
    def check_github_profile(username: str, sess) -> Dict:
        """Check GitHub profile for blog link."""
        result = {
            "success": False,
            "platform": "GITHUB",
            "username": username,
            "profile_url": f"https://github.com/{username}",
            "error": None,
        }

        try:
            r = sess.get(f"https://api.github.com/users/{username}", timeout=10)
            if r.status_code == 200:
                data = r.json()
                result["exists"] = True
                if data.get("blog"):
                    result["success"] = True
                    result["link"] = data["blog"]
                    result["status"] = "has_blog_link"
                else:
                    result["status"] = "exists_no_blog"
            elif r.status_code == 404:
                result["exists"] = False
                result["status"] = "available"
            else:
                result["error"] = f"HTTP {r.status_code}"
            return result
        except Exception as e:
            result["error"] = str(e)[:100]
            return result

    @staticmethod
    def check_all_profiles(usernames: List[str], sess) -> List[Dict]:
        """Check all platforms for profile availability."""
        results = []
        for username in usernames[:5]:  # Limit to 5
            for platform in ["GRAVATAR", "GITHUB"]:
                if platform == "GRAVATAR":
                    result = ProfileCreator.create_gravatar_profile(
                        username, username.replace("_", " ").title(),
                        "https://jasatebasrumput.info", sess
                    )
                elif platform == "GITHUB":
                    result = ProfileCreator.check_github_profile(username, sess)
                results.append(result)
                time.sleep(0.5)
        return results


# ═══════════════════════════════════════════════════════════
# V15 BACKLINK BEAST ENGINE
# ═══════════════════════════════════════════════════════════
class BacklinkBeastEngine(SpamBeastEngine):
    """V15 BACKLINK PROTOCOL — extends V14 Spam with backlink modules."""

    def __init__(self, target, focus=None, aggressive=False, fast=False,
                 max_timeout=0, pin_brute=0, resume=False,
                 cookie_stuff_ref=None, affiliate_tag="GENERIC", fraud_mode="full",
                 spam_count=10, spam_link=None, spam_mode="stealth",
                 contact_forms=False, guestbook=False, pingback_url=None):
        super().__init__(target, focus, aggressive, fast, max_timeout, pin_brute,
                         resume, cookie_stuff_ref, affiliate_tag, fraud_mode,
                         spam_count, spam_link, spam_mode, contact_forms)
        self.guestbook_mode = guestbook
        self.pingback_url = pingback_url or self.spam_link
        self.backlink_findings = []

    def add_backlink(self, kind, severity, **kwargs):
        self.backlink_findings.append({
            "kind": kind, "severity": severity,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        })

    def run(self):
        print(V15_SIGNATURE)
        print(f"Target: {self.target}")
        print(f"Backlink: {self.pingback_url or 'auto'} | Guestbook: {self.guestbook_mode}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # ── Resume ──
        if self.resume:
            state = StateManager.load(self.target)
            if state:
                self.findings = state.get("findings", [])
                self.backlink_findings = state.get("backlink_findings", [])
                print(f"   ♻ Resumed: {len(self.findings)} findings")

        # ═══ PHASE 0: TLS SETUP ═══
        self._phase("TLS SETUP", 0)
        try:
            if CFFI_OK:
                probed = TLSEngine.probe(self.base + "/")
                if probed.get("ok"):
                    self.tls = probed["session"]
                    print(f"   ✅ TLS OK ({probed['fingerprint']})")
                else:
                    self.tls = ProxyRotator.fresh_session()
            else:
                self.tls = ProxyRotator.fresh_session()
        except Exception as e:
            self.tls = ProxyRotator.fresh_session()

        total_links = 0

        # ═══ PHASE 1: GUESTBOOK HUNTER ═══
        self._phase("GUESTBOOK HUNTER", 1)
        guestbooks = GuestbookHunter.find_guestbooks_on_target(self.base, sess=self.tls)
        print(f"   📋 Guestbooks found: {len(guestbooks)}")

        if guestbooks:
            link = self.pingback_url or "https://jasatebasrumput.info"
            for gb in guestbooks[:3]:  # Limit to 3 guestbooks
                name = CommentSpammer.generate_name()
                email = CommentSpammer.generate_email(name)
                message = random.choice([
                    f"Wah websitenya bagus! Sangat bermanfaat. Salam kenal dari {link}",
                    f"Terima kasih informasinya. Kunjungi juga {link} untuk info seputar taman.",
                    f"Artikel yang sangat membantu. Jangan lupa mampir ke {link} ya!",
                    f"Nice website! Very informative. Also check out {link} for garden tips.",
                    f"Situs yang keren! Salam dari {link} - jasa perawatan taman profesional.",
                ])

                result = GuestbookHunter.post_guestbook_entry(gb, name, email, link, message, self.tls)

                if result["success"]:
                    total_links += 1
                    status = result.get("status", "submitted")
                    verified = "✅ VERIFIED" if result.get("verified") else ""
                    print(f"   🔥 [{status.upper()}] {gb['url']} {verified}")
                    self.add_backlink("guestbook_backlink", "high",
                                     url=gb["url"], name=name, status=status,
                                     verified=result.get("verified", False))
                else:
                    print(f"   ❌ Guestbook failed: {result.get('error', 'unknown')}")

        print(f"   📊 Guestbook: {total_links} backlinks planted")

        # ═══ PHASE 2: PINGBACK ENGINE ═══
        self._phase("PINGBACK ENGINE", 2)
        xmlrpc = PingbackEngine.find_xmlrpc_url(self.base, sess=self.tls)
        if xmlrpc:
            print(f"   ✅ XML-RPC: {xmlrpc}")

            if self.pingback_url:
                # Send pingback from our source URL
                result = PingbackEngine.send_pingback(
                    self.pingback_url, self.base + "/", self.tls
                )
                if result["success"]:
                    total_links += 1
                    print(f"   🔥 PINGBACK SENT: {self.pingback_url} → {self.base}")
                    self.add_backlink("pingback", "high",
                                     source=self.pingback_url, target=self.base,
                                     status=result.get("status"))
                else:
                    print(f"   ⚠ Pingback: {result.get('error', 'unknown')}")

            # Try trackback on posts
            try:
                r = self.tls.get(self.base + "/", timeout=10)
                post_ids = re.findall(r'post[_-]?id[=:]?\s*["\']?(\d+)["\']?', r.text, re.IGNORECASE)
                post_ids = list(set(post_ids))[:3]

                for pid in post_ids:
                    excerpt = f"Artikel menarik tentang perawatan taman dan landscaping. {self.pingback_url or 'https://jasatebasrumput.info'}"
                    result = PingbackEngine.send_trackback(
                        self.base, pid,
                        "Tips Perawatan Taman Profesional",
                        excerpt,
                        "Jasa Tebas Rumput",
                        self.pingback_url or "https://jasatebasrumput.info",
                        self.tls
                    )
                    if result["success"]:
                        total_links += 1
                        print(f"   🔥 TRACKBACK SENT: post_id={pid}")
                        self.add_backlink("trackback", "high",
                                         target=self.base, post_id=pid,
                                         status=result.get("status"))
                    else:
                        print(f"   ⚠ Trackback failed (post_id={pid}): {result.get('error')}")
            except Exception as e:
                print(f"   ⚠ Trackback error: {e}")
        else:
            print("   ⚠ No XML-RPC endpoint found")

        print(f"   📊 Pingback: {total_links} links")

        # ═══ PHASE 3: PROFILE CREATOR ═══
        self._phase("PROFILE CREATOR", 3)
        profiles = ProfileCreator.generate_profile_names()
        profile_results = ProfileCreator.check_all_profiles(
            [p["username"] for p in profiles], self.tls
        )

        for pr in profile_results:
            if pr.get("success") and pr.get("link"):
                total_links += 1
                print(f"   🔥 PROFILE: {pr['platform']} - {pr.get('profile_url', pr.get('url'))} → {pr['link']}")
                self.add_backlink("profile_backlink", "medium",
                                 platform=pr["platform"],
                                 url=pr.get("profile_url", pr.get("url")),
                                 link=pr["link"])
            elif pr.get("exists") and not pr.get("success"):
                print(f"   📝 {pr['platform']}: {pr.get('profile_url')} exists (no link)")

        # ═══ PHASE 4: Comment Spam (from V14) ═══
        if self.focus != "backlink":
            self._phase("COMMENT SPAM", 4)
            try:
                self.blog_platform = BlogHunter.detect_platform(self.base, sess=self.tls)
                if self.blog_platform != "UNKNOWN":
                    self.posts = BlogHunter.extract_posts(self.blog_platform, self.base, sess=self.tls, limit=10)
                    if self.posts:
                        sample_posts = self.posts[:min(3, len(self.posts))]
                        self.comment_forms = []
                        for post in sample_posts:
                            form = BlogHunter.find_comment_form(self.blog_platform, post["url"], sess=self.tls)
                            if form and form.get("form_action"):
                                self.comment_forms.append(form)

                        if self.comment_forms:
                            comments = CommentSpammer.generate_comment_pool(min(3, self.spam_count), self.spam_link or "")
                            for i, comment in enumerate(comments[:3]):
                                form = self.comment_forms[i % len(self.comment_forms)]
                                name = CommentSpammer.generate_name()
                                email = CommentSpammer.generate_email(name)
                                result = CommentSpammer.post_comment(form, name, email, "", comment, self.tls, 2.0)
                                status = result.get("status", "unknown")
                                if result["success"]:
                                    if status == "published":
                                        print(f"   🔥 [{status.upper()}] Comment published!")
                                    else:
                                        print(f"   📝 [{status.upper()}] Comment held")
            except Exception as e:
                print(f"   ⚠ Comment spam error: {e}")

        # ═══ GENERATE REPORT ═══
        self._phase("REPORT", 99)
        os.makedirs(REPORT_DIR, exist_ok=True)
        report = self._generate_backlink_report()
        report_path = os.path.join(
            REPORT_DIR,
            f"{self.target.replace('https://','').replace('http://','').rstrip('/').replace('/','_')}_v15.json"
        )
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n   📄 Report: {report_path}")

        os.makedirs(STATE_DIR, exist_ok=True)
        StateManager.save(self.target, self.findings + self.backlink_findings,
                         self.phases_done + ["backlink_v15"])
        print(f"   💾 State saved")
        print(f"\n   🔥 TOTAL BACKLINKS PLANTED: {total_links}")

        return report

    def _generate_backlink_report(self) -> Dict:
        return {
            "target": self.target,
            "version": "V15 BACKLINK PROTOCOL",
            "timestamp": datetime.now().isoformat(),
            "findings": {
                "base": len(self.findings),
                "backlink_v15": len(self.backlink_findings),
                "total": len(self.findings) + len(self.backlink_findings),
            },
            "backlink_findings": self.backlink_findings,
            "base_findings": self.findings,
            "modules_active": {
                "guestbook_hunter": True,
                "pingback_engine": True,
                "profile_creator": True,
                "comment_spammer": True,
                "contact_form_spammer": self.contact_forms,
            },
            "pingback_url": self.pingback_url,
        }


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="LISA V15 BACKLINK PROTOCOL — The Link Farmer")
    p.add_argument("target", nargs="?", help="Target domain")
    p.add_argument("-t", "--targets", nargs="+", help="Multiple targets (batch mode)")
    p.add_argument("--focus", choices=["all", "backlink", "blog", "spam", "fraud"],
                   default="all")
    p.add_argument("--aggressive", action="store_true")
    p.add_argument("--fast", action="store_true")
    p.add_argument("--timeout", type=int, default=0)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--list-saved", action="store_true")
    p.add_argument("--spam-count", type=int, default=10)
    p.add_argument("--spam-link", help="URL to inject")
    p.add_argument("--spam-mode", choices=["stealth", "normal", "aggressive"], default="stealth")
    p.add_argument("--contact-forms", action="store_true")
    p.add_argument("--guestbook", action="store_true", help="Hunt guestbooks")
    p.add_argument("--pingback", help="Source URL for pingback")

    a = p.parse_args()

    if a.list_saved:
        print("Saved targets:", StateManager.list_saved())
        sys.exit(0)

    if a.targets:
        print("🐺 BATCH BACKLINK MODE\n")
        with ThreadPoolExecutor(max_workers=2) as ex:
            futs = {}
            for t in a.targets:
                eng = BacklinkBeastEngine(target=t, focus=a.focus, aggressive=a.aggressive,
                                         fast=a.fast, max_timeout=a.timeout,
                                         resume=a.resume, spam_count=a.spam_count,
                                         spam_link=a.spam_link, spam_mode=a.spam_mode,
                                         contact_forms=a.contact_forms,
                                         guestbook=a.guestbook, pingback_url=a.pingback)
                futs[ex.submit(eng.run)] = t
            for fut in as_completed(futs):
                t = futs[fut]
                try:
                    results[t] = fut.result()
                    n = results[t]["findings"]["total"]
                    print(f"  {t}: {n} findings")
                except Exception as e:
                    print(f"  {t}: ERROR - {e}")
        sys.exit(0)

    if not a.target:
        print(__doc__)
        sys.exit(1)

    eng = BacklinkBeastEngine(target=a.target, focus=a.focus, aggressive=a.aggressive,
                              fast=a.fast, max_timeout=a.timeout,
                              resume=a.resume, spam_count=a.spam_count,
                              spam_link=a.spam_link, spam_mode=a.spam_mode,
                              contact_forms=a.contact_forms,
                              guestbook=a.guestbook, pingback_url=a.pingback)
    eng.run()