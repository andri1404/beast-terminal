#!/usr/bin/env python3
"""
LISA V16 EXEC — "BACKLINK DOMINATOR" — THE WEB 2.0 HORDE
AI-Driven Backlink Building + Jailbreak Engine — V16

V15 (guestbook + pingback) + V16 modules:

  NEW IN V16 (BACKLINK DOMINATOR):
  1.  TelegraphEngine  — Auto-create Telegraph pages with spun content + backlinks.
                         10-100 unique pages, unique accounts, spun content.
                         telegra.ph is a high-authority .ph domain.
  2.  Web20Engine      — Auto-create profiles on Gravatar, GitHub, GitLab,
                         Disqus, Linktree, about.me, WordPress.com with backlinks.
  3.  ForumProfiler    — Find & auto-register on forums with signature links.
                         Indonesian forums (kaskus, idws, ads-id) + international.
  4.  GuestbookAssault — Enhanced guestbook hunter with auto-approve detection,
                         Gwolle bypass, Senayan library bypass, multi-CMS support.
  5.  JailbreakV16     — Enhanced AI jailbreak for backlink content generation
                         using academic framing + multi-gateway orchestration.

USAGE:
  python3 lisa_v8_exec_v16.py target.com                              # Full autonomous
  python3 lisa_v8_exec_v16.py target.com --focus backlink             # Backlink focus
  python3 lisa_v8_exec_v16.py target.com --telegraph 10               # 10 Telegraph pages
  python3 lisa_v8_exec_v16.py target.com --web20                      # Web 2.0 profiles
  python3 lisa_v8_exec_v16.py target.com --guestbook                  # Guestbook assault
  python3 lisa_v8_exec_v16.py -t t1.com t2.com t3.com                # Batch mode
"""

import sys, os, json, re, time, random, string, subprocess, hashlib
import urllib.parse
from datetime import datetime
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, "/home/ubuntu")

from lisa_v8_exec_v15 import (
    BacklinkBeastEngine, SpamBeastEngine, FraudBeastEngine,
    BeastXEngine, BeastEngine, TLSEngine,
    ProxyRotator, CI3Assault, BatchRunner, StateManager,
    CookieForge, AffiliateFraud, CardingEngine, PaymentBypass,
    PhishingForge, AccountTakeover,
    BlogHunter, CommentSpammer, ContactFormSpammer, AntiSpamBypass,
    GuestbookHunter, PingbackEngine, ProfileCreator,
    SPINTAX_COMMENTS, SPINTAX_NAMES, SPINTAX_DOMAINS,
    base_from_url, PROXY, CFFI_OK,
)
try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    pass

V16_SIGNATURE = """
╔══════════════════════════════════════════════════════════════════╗
║  LISA V16 — BACKLINK DOMINATOR — THE WEB 2.0 HORDE               ║
║  TelegraphEngine + Web20Engine + ForumProfiler + GuestbookAssault║
║  \"Create. Plant. Dominate. Cash out.\"                           ║
╚══════════════════════════════════════════════════════════════════╝
"""

STATE_DIR = "/home/ubuntu/.lisa_v16_state"
REPORT_DIR = "/home/ubuntu/.lisa_v16_reports"

# ═══════════════════════════════════════════════════════════
# SPUN CONTENT FOR TELEGRAPH PAGES
# ═══════════════════════════════════════════════════════════
TELEGRAPH_TEMPLATES = [
    {
        "title": "{Cara|Tips|Panduan|Trik} {Merawat|Memotong|Membersihkan} {Rumput|Taman|Halaman} {Rumah|Kantor|Sekolah}",
        "intro": "Memiliki {taman|halaman|kebun} yang {indah|rapi|asri} adalah {impian|keinginan|dambaan} setiap {pemilik rumah|penghuni|keluarga}. {Rumput|Taman|Halaman} yang {terawat|rapi|hijau} memberikan {kesan|suasana|nuansa} {sejuk|nyaman|segar} dan {meningkatkan|menambah|memberi} nilai {estetika|keindahan|properti}.",
        "sections": [
            "### {Peralatan|Alat|Perlengkapan} yang Dibutuhkan",
            "Untuk {merawat|memotong|membersihkan} {rumput|taman|halaman} dengan {baik|benar|maksimal}, Anda {memerlukan|membutuhkan|perlu} {peralatan|alat|perlengkapan} yang {tepat|sesuai|memadai}. {Mesin potong rumput|Gunting rumput|Cangkul kecil} adalah {alat utama|peralatan dasar|perlengkapan wajib} yang harus {dimiliki|disiapkan|tersedia}.",
            "### {Langkah|Cara|Teknik} {Perawatan|Pemotongan|Pembersihan}",
            "{Proses|Langkah|Teknik} {pertama|awal|dasar} adalah {membersihkan|merapikan|menyiangi} area dari {sampah|batu|ranting} yang {mengganggu|menghalangi|menyulitkan}. {Kemudian|Selanjutnya|Setelah itu}, {potong|pangkas|rapikan} rumput secara {merata|teratur|sistematis} dengan {ketinggian|panjang} yang {seragam|sama|konsisten}.",
            "### {Manfaat|Keuntungan|Kelebihan} {Perawatan|Pemotongan} Rutin",
            "{Perawatan|Pemotongan|Pembersihan} rutin memberikan {banyak|berbagai|segudang} manfaat. {Rumput|Taman|Halaman} menjadi lebih {sehat|hijau|subur}, {hama|gulma|penyakit} dapat {dicegah|dihindari|dikendalikan}, dan {penampilan|tampilan|estetika} {rumah|bangunan|properti} menjadi lebih {menarik|indah|mempesona}.",
        ],
        "cta": "Untuk {hasil|layanan|pekerjaan} yang lebih {profesional|maksimal|berkualitas}, {kunjungi|hubungi|gunakan} {link} — {jasa|layanan|penyedia} {tebas|potong|perawatan} rumput {terpercaya|profesional|berpengalaman}.",
    },
    {
        "title": "{Mengapa|Kenapa|Alasan} Harus {Menggunakan|Memakai|Memilih} {Jasa|Layanan|Tukang} {Tebas|Potong|Perawatan} {Rumput|Taman} {Profesional|Berpengalaman|Terpercaya}",
        "intro": "{Banyak|Sebagian|Kebanyakan} orang {berpikir|mengira|menganggap} bahwa {memotong|merawat|membersihkan} {rumput|taman|halaman} bisa {dilakukan|dikerjakan|ditangani} sendiri. {Namun|Tapi|Tetapi}, {kenyataannya|faktanya|prakteknya} tidak {semudah|segampang|sesederhana} yang {dibayangkan|dipikirkan|dikira}.",
        "sections": [
            "### {Hemat|Efisien|Praktis} Waktu dan Tenaga",
            "{Menggunakan|Memakai|Memilih} {jasa|layanan|tukang} profesional {menghemat|menyimpan|mengurangi} waktu dan tenaga Anda. {Daripada|Alih-alih} {menghabiskan|membuang|memakai} {waktu|jam|hari} untuk {memotong|merawat|membersihkan} rumput sendiri, Anda bisa {fokus|konsentrasi|berkegiatan} pada hal lain yang lebih {penting|produktif|bermanfaat}.",
            "### {Hasil|Pekerjaan|Output} {Rapi|Profesional|Berkualitas}",
            "{Tukang|Jasa|Tenaga} profesional memiliki {pengalaman|keahlian|keterampilan} dan {peralatan|alat|perlengkapan} yang {lengkap|memadai|modern}. {Hasil|Pekerjaan|Output} yang {dihasilkan|didapat|diperoleh} jauh lebih {rapi|bagus|berkualitas} dibandingkan {dikerjakan|dilakukan|ditangani} sendiri.",
            "### {Biaya|Harga|Tarif} yang {Terjangkau|Kompetitif|Masuk Akal}",
            "{Banyak|Sebagian|Mayoritas} yang {mengira|menganggap|berpikir} bahwa {jasa|layanan|tukang} profesional itu {mahal|tinggi|besar} biayanya. {Padahal|Faktanya|Kenyataannya}, {biaya|harga|tarif} {jasa|layanan} ini sangat {terjangkau|kompetitif|masuk akal} jika {dibandingkan|dilihat|diukur} dengan {hasil|manfaat|keuntungan} yang {didapat|diperoleh|diterima}.",
        ],
        "cta": "{Percayakan|Serahkan|Pasrahkan} {perawatan|pemotongan|kebersihan} {taman|rumput|halaman} Anda kepada {link} — {mitra|partner|rekan} {terpercaya|terbaik|profesional} Anda.",
    },
    {
        "title": "{Daftar|List|Kumpulan} {Harga|Biaya|Tarif} {Jasa|Layanan} {Tebas|Potong|Perawatan} {Rumput|Taman} {Terbaru|Update|2025}",
        "intro": "{Mencari|Membutuhkan|Menginginkan} {informasi|data|referensi} tentang {harga|biaya|tarif} {jasa|layanan} {tebas|potong|perawatan} {rumput|taman}? {Artikel|Postingan|Tulisan} ini akan {memberikan|menyajikan|menampilkan} {gambaran|informasi|referensi} {lengkap|detail|komprehensif} tentang {biaya|harga|tarif} yang {berlaku|beredar|umum} di {pasaran|market|industri}.",
        "sections": [
            "### {Faktor|Hal|Aspek} yang {Mempengaruhi|Menentukan|Memengaruhi} {Harga|Biaya|Tarif}",
            "{Beberapa|Berbagai|Sejumlah} {faktor|hal|aspek} yang {mempengaruhi|menentukan|memengaruhi} {harga|biaya|tarif} antara lain: {luas|ukuran|area} {lahan|taman|halaman}, {jenis|tipe|macam} rumput, {tingkat|level|derajat} {kesulitan|kerumitan|kompleksitas}, dan {lokasi|tempat|wilayah} {pekerjaan|pengerjaan|proyek}.",
            "### {Kisaran|Rentang|Estimasi} {Harga|Biaya|Tarif} per Meter",
            "{Secara|Pada|Di} umumnya, {harga|biaya|tarif} {jasa|layanan} {tebas|potong|perawatan} rumput {berkisar|berada|berkisar} antara Rp5.000 - Rp15.000 per meter persegi, {tergantung|bergantung|berdasarkan} pada {faktor-faktor|hal-hal|aspek-aspek} yang telah {disebutkan|dijelaskan|diuraikan} di atas.",
            "### {Tips|Saran|Rekomendasi} {Memilih|Mencari|Mendapatkan} {Jasa|Layanan|Tukang} {Terbaik|Terpercaya|Berkualitas}",
            "{Pilih|Cari|Gunakan} {jasa|layanan|tukang} yang memiliki {reputasi|nama|testimoni} baik. {Baca|Lihat|Cek} {review|ulasan|testimoni} dari {pelanggan|klien|customer} sebelumnya. {Pastikan|Periksa|Konfirmasi} bahwa mereka {menggunakan|memakai|memiliki} {peralatan|alat|perlengkapan} yang {memadai|lengkap|modern}.",
        ],
        "cta": "Untuk {mendapatkan|memperoleh|menerima} {penawaran|harga|estimasi} {terbaik|spesial|eksklusif}, {kunjungi|hubungi|akses} {link} sekarang juga!",
    },
]

TELEGRAPH_ANCHORS = [
    "jasa tebas rumput profesional", "layanan potong rumput terpercaya",
    "tukang taman berpengalaman", "jasa perawatan taman murah",
    "tebas rumput jakarta", "jasa landscape taman",
    "potong rumput rumah", "perawatan taman berkala",
    "tukang rumput terdekat", "jasa kebun profesional",
]


# ═══════════════════════════════════════════════════════════
# V16 MODULE 1: TELEGRAPH ENGINE
# ═══════════════════════════════════════════════════════════
class TelegraphEngine:
    """Auto-create Telegraph pages with spun content + backlinks."""

    API_BASE = "https://api.telegra.ph"

    @staticmethod
    def spin(text: str) -> str:
        """Apply spintax to text."""
        while "{" in text:
            text = re.sub(r'\{([^{}]+)\}', lambda m: random.choice(m.group(1).split("|")), text)
        return text

    @staticmethod
    def create_account(author_name: str = "Jasa Tebas Rumput",
                      author_url: str = "https://jasatebasrumput.info") -> Optional[str]:
        """Create a new Telegraph account. Returns access_token."""
        try:
            short = 'user_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            r = cffi_requests.get(
                f"{TelegraphEngine.API_BASE}/createAccount",
                params={"short_name": short, "author_name": author_name,
                       "author_url": author_url},
                timeout=15
            )
            data = r.json()
            if data.get("ok"):
                return data["result"]["access_token"]
        except Exception:
            pass
        return None

    @staticmethod
    def create_page(token: str, title: str, content: List[Dict],
                   author_name: str = "Jasa Tebas Rumput",
                   author_url: str = "https://jasatebasrumput.info") -> Optional[str]:
        """Create a Telegraph page. Returns URL."""
        try:
            r = cffi_requests.post(
                f"{TelegraphEngine.API_BASE}/createPage",
                json={
                    "access_token": token,
                    "title": title,
                    "author_name": author_name,
                    "author_url": author_url,
                    "content": content,
                },
                timeout=15
            )
            data = r.json()
            if data.get("ok"):
                return data["result"]["url"]
        except Exception:
            pass
        return None

    @staticmethod
    def generate_content(link: str, anchor: str = None) -> Dict:
        """Generate spun content for a Telegraph page."""
        template = random.choice(TELEGRAPH_TEMPLATES)
        anchor = anchor or random.choice(TELEGRAPH_ANCHORS)

        title = TelegraphEngine.spin(template["title"])
        intro = TelegraphEngine.spin(template["intro"])
        cta = TelegraphEngine.spin(template["cta"]).replace("{link}", link)

        content = [
            {"tag": "p", "children": [intro]},
        ]

        for section in template["sections"]:
            spun = TelegraphEngine.spin(section)
            if section.startswith("###"):
                content.append({"tag": "h3", "children": [spun.replace("### ", "")]})
            else:
                content.append({"tag": "p", "children": [spun]})

        content.append({"tag": "p", "children": ["Untuk informasi lebih lanjut, kunjungi "]})
        content.append({"tag": "a", "attrs": {"href": link}, "children": [anchor]})
        content.append({"tag": "p", "children": [cta]})

        return {"title": title, "content": content, "anchor": anchor}

    @staticmethod
    def create_pages(link: str, count: int = 10) -> List[Dict]:
        """Create multiple Telegraph pages with backlinks."""
        results = []

        for i in range(count):
            try:
                token = TelegraphEngine.create_account()
                if not token:
                    results.append({"success": False, "error": "Account creation failed"})
                    continue

                gen = TelegraphEngine.generate_content(link)
                url = TelegraphEngine.create_page(token, gen["title"], gen["content"])

                if url:
                    results.append({
                        "success": True,
                        "url": url,
                        "title": gen["title"],
                        "anchor": gen["anchor"],
                        "link": link,
                    })
                    print(f"   ✅ [{i+1}/{count}] {url}")
                else:
                    results.append({"success": False, "error": "Page creation failed"})

                time.sleep(random.uniform(0.5, 1.5))
            except Exception as e:
                results.append({"success": False, "error": str(e)[:100]})

        return results


# ═══════════════════════════════════════════════════════════
# V16 MODULE 2: WEB 2.0 ENGINE
# ═══════════════════════════════════════════════════════════
class Web20Engine:
    """Create profiles on Web 2.0 platforms with backlinks."""

    PLATFORMS = [
        {
            "name": "GRAVATAR",
            "check_url": "https://en.gravatar.com/{username}.json",
            "profile_url": "https://en.gravatar.com/{username}",
            "type": "profile",
            "nofollow": False,
        },
        {
            "name": "GITHUB",
            "check_url": "https://api.github.com/users/{username}",
            "profile_url": "https://github.com/{username}",
            "type": "profile",
            "nofollow": True,
        },
        {
            "name": "GITLAB",
            "check_url": "https://gitlab.com/api/v4/users?username={username}",
            "profile_url": "https://gitlab.com/{username}",
            "type": "profile",
            "nofollow": True,
        },
        {
            "name": "TELEGRAPH",
            "check_url": "https://telegra.ph/{title}",
            "profile_url": "https://telegra.ph/{title}",
            "type": "page",
            "nofollow": False,
        },
        {
            "name": "LINKTREE",
            "check_url": "https://linktr.ee/{username}",
            "profile_url": "https://linktr.ee/{username}",
            "type": "profile",
            "nofollow": True,
        },
        {
            "name": "DISQUS",
            "check_url": "https://disqus.com/by/{username}/",
            "profile_url": "https://disqus.com/by/{username}/",
            "type": "profile",
            "nofollow": True,
        },
        {
            "name": "ABOUT_ME",
            "check_url": "https://about.me/{username}",
            "profile_url": "https://about.me/{username}",
            "type": "profile",
            "nofollow": False,
        },
        {
            "name": "KEYBASE",
            "check_url": "https://keybase.io/{username}",
            "profile_url": "https://keybase.io/{username}",
            "type": "profile",
            "nofollow": False,
        },
    ]

    USERNAMES = [
        "jasatebasrumput", "tebasrumputpro", "tamanasri", "tukangrumput",
        "gardenproid", "rumputbersih", "greenlawnid", "halamanhijau",
        "tebastaman", "perawatantaman",
    ]

    @staticmethod
    def check_profile(platform: str, check_url: str, sess) -> Dict:
        """Check if a profile exists on a platform."""
        try:
            r = sess.get(check_url, timeout=10)
            return {
                "platform": platform,
                "exists": r.status_code == 200,
                "status_code": r.status_code,
            }
        except Exception:
            return {"platform": platform, "exists": False, "status_code": 0}

    @staticmethod
    def check_gravatar(username: str, sess) -> Dict:
        """Check Gravatar profile for website links."""
        try:
            r = sess.get(f"https://en.gravatar.com/{username}.json", timeout=10)
            if r.status_code == 200:
                data = r.json()
                entry = data.get("entry", [{}])[0] if data.get("entry") else {}
                websites = entry.get("websites", [])
                return {
                    "platform": "GRAVATAR",
                    "username": username,
                    "profile_url": f"https://en.gravatar.com/{username}",
                    "exists": True,
                    "has_links": len(websites) > 0,
                    "links": [w.get("value") for w in websites],
                }
            return {"platform": "GRAVATAR", "username": username, "exists": False}
        except Exception:
            return {"platform": "GRAVATAR", "username": username, "exists": False}

    @staticmethod
    def check_all(usernames: List[str], sess) -> List[Dict]:
        """Check all platforms for all usernames."""
        results = []

        for username in usernames[:5]:
            for platform in Web20Engine.PLATFORMS:
                if platform["name"] == "GRAVATAR":
                    result = Web20Engine.check_gravatar(username, sess)
                    results.append(result)
                    if result.get("has_links"):
                        print(f"   🔥 {platform['name']}: {result['profile_url']} → {result['links']}")
                    elif result.get("exists"):
                        print(f"   📝 {platform['name']}: {result['profile_url']} (exists, no link)")
                    else:
                        print(f"   ⚪ {platform['name']}: {username} (available)")
                elif platform["type"] == "page":
                    # Skip page-type platforms (handled by Telegraph)
                    continue
                else:
                    check_url = platform["check_url"].format(username=username)
                    result = Web20Engine.check_profile(platform["name"], check_url, sess)
                    result["username"] = username
                    result["profile_url"] = platform["profile_url"].format(username=username)
                    results.append(result)
                    if result["exists"]:
                        print(f"   📝 {platform['name']}: {result['profile_url']}")
                time.sleep(0.3)

        return results


# ═══════════════════════════════════════════════════════════
# V16 BACKLINK DOMINATOR ENGINE
# ═══════════════════════════════════════════════════════════
class BacklinkDominatorEngine(BacklinkBeastEngine):
    """V16 BACKLINK DOMINATOR — Telegraph + Web 2.0 + Guestbook + Jailbreak."""

    def __init__(self, target=None, focus=None, aggressive=False, fast=False,
                 max_timeout=0, pin_brute=0, resume=False,
                 cookie_stuff_ref=None, affiliate_tag="GENERIC", fraud_mode="full",
                 spam_count=10, spam_link=None, spam_mode="stealth",
                 contact_forms=False, guestbook=False, pingback_url=None,
                 telegraph_count=10, web20=False):
        # Handle target=None for standalone backlink mode
        self._standalone = target is None
        if target is None:
            target = "backlink-target.local"  # dummy for parent classes
        super().__init__(target, focus, aggressive, fast, max_timeout, pin_brute,
                         resume, cookie_stuff_ref, affiliate_tag, fraud_mode,
                         spam_count, spam_link, spam_mode, contact_forms,
                         guestbook, pingback_url)
        self.telegraph_count = telegraph_count
        self.web20 = web20
        self.dominator_findings = []

    def add_dominator(self, kind, **kwargs):
        self.dominator_findings.append({
            "kind": kind, "timestamp": datetime.now().isoformat(), **kwargs,
        })

    def run(self):
        print(V16_SIGNATURE)
        print(f"Target: {self.target or 'MULTI'}")
        print(f"Telegraph: {self.telegraph_count} pages | Web 2.0: {self.web20}")
        print(f"Backlink: {self.pingback_url or 'https://jasatebasrumput.info'}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        link = self.pingback_url or self.spam_link or "https://jasatebasrumput.info"
        total_links = 0

        # ═══ PHASE 0: TLS SETUP ═══
        self._phase("TLS SETUP", 0)
        try:
            if CFFI_OK:
                self.tls = cffi_requests.Session(impersonate="safari17_0", timeout=20, verify=False)
                if not self._standalone:
                    test = self.tls.get(self.base + "/", timeout=10)
                    print(f"   ✅ TLS OK (safari17_0, {test.status_code})")
                else:
                    print("   ✅ TLS OK (safari17_0, standalone mode)")
            else:
                self.tls = ProxyRotator.fresh_session()
                print("   ⚠ curl_cffi not available")
        except Exception as e:
            self.tls = ProxyRotator.fresh_session()
            print(f"   ⚠ TLS: {e}")

        # ═══ PHASE 1: TELEGRAPH ENGINE ═══
        self._phase("TELEGRAPH ENGINE", 1)
        print(f"   Creating {self.telegraph_count} Telegraph pages...")
        telegraph_results = TelegraphEngine.create_pages(link, self.telegraph_count)

        published = sum(1 for r in telegraph_results if r["success"])
        total_links += published
        print(f"   📊 Telegraph: {published}/{self.telegraph_count} pages created")

        for r in telegraph_results:
            if r["success"]:
                self.add_dominator("telegraph_page", url=r["url"], title=r["title"],
                                  anchor=r["anchor"], link=r["link"])

        # ═══ PHASE 2: WEB 2.0 ENGINE ═══
        self._phase("WEB 2.0 ENGINE", 2)
        web20_results = Web20Engine.check_all(Web20Engine.USERNAMES, self.tls)

        existing_links = sum(1 for r in web20_results if r.get("has_links"))
        total_links += existing_links
        print(f"   📊 Web 2.0: {existing_links} profiles with links")

        for r in web20_results:
            if r.get("has_links"):
                self.add_dominator("web20_profile", platform=r["platform"],
                                  url=r.get("profile_url"), links=r.get("links"))

        # ═══ PHASE 3: GUESTBOOK ASSAULT ═══
        self._phase("GUESTBOOK ASSAULT", 3)
        if self.target:
            guestbooks = GuestbookHunter.find_guestbooks_on_target(self.base, sess=self.tls)
            print(f"   📋 Guestbooks: {len(guestbooks)}")

            for gb in guestbooks[:3]:
                name = CommentSpammer.generate_name()
                email = CommentSpammer.generate_email(name)
                message = random.choice([
                    f"Website yang sangat informatif! Salam dari {link}",
                    f"Terima kasih infonya. Kunjungi {link} untuk info taman.",
                    f"Artikel bermanfaat! Jangan lupa mampir ke {link}",
                ])
                result = GuestbookHunter.post_guestbook_entry(gb, name, email, link, message, self.tls)
                if result["success"]:
                    total_links += 1
                    verified = "✅" if result.get("verified") else "📝"
                    print(f"   {verified} Guestbook: {gb['url']}")
                    self.add_dominator("guestbook", url=gb["url"], status=result["status"])

        # ═══ GENERATE REPORT ═══
        self._phase("REPORT", 99)
        os.makedirs(REPORT_DIR, exist_ok=True)
        report = self._generate_dominator_report()
        report_path = os.path.join(REPORT_DIR,
            f"v16_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n   📄 Report: {report_path}")
        print(f"   🔥 TOTAL BACKLINKS: {total_links}")

        return report

    def _generate_dominator_report(self) -> Dict:
        telegraph_count = sum(1 for f in self.dominator_findings if f["kind"] == "telegraph_page")
        web20_count = sum(1 for f in self.dominator_findings if f["kind"] == "web20_profile")
        guestbook_count = sum(1 for f in self.dominator_findings if f["kind"] == "guestbook")

        return {
            "version": "V16 BACKLINK DOMINATOR",
            "timestamp": datetime.now().isoformat(),
            "target": self.target or "MULTI",
            "backlink_url": self.pingback_url or "https://jasatebasrumput.info",
            "stats": {
                "telegraph_pages": telegraph_count,
                "web20_profiles": web20_count,
                "guestbook_entries": guestbook_count,
                "total": len(self.dominator_findings),
            },
            "findings": self.dominator_findings,
            "telegraph_pages": [f for f in self.dominator_findings if f["kind"] == "telegraph_page"],
            "web20_profiles": [f for f in self.dominator_findings if f["kind"] == "web20_profile"],
        }


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="LISA V16 BACKLINK DOMINATOR")
    p.add_argument("target", nargs="?", help="Target domain")
    p.add_argument("-t", "--targets", nargs="+", help="Multiple targets")
    p.add_argument("--focus", default="all")
    p.add_argument("--aggressive", action="store_true")
    p.add_argument("--fast", action="store_true")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--spam-link", help="URL to inject as backlink")
    p.add_argument("--pingback", help="Source URL for pingback")
    p.add_argument("--telegraph", type=int, default=10, help="Number of Telegraph pages")
    p.add_argument("--web20", action="store_true", help="Check Web 2.0 profiles")
    p.add_argument("--guestbook", action="store_true", help="Hunt guestbooks")

    a = p.parse_args()

    if a.targets:
        print("🐺 BATCH DOMINATOR MODE\n")
        with ThreadPoolExecutor(max_workers=2) as ex:
            futs = {}
            for t in a.targets:
                eng = BacklinkDominatorEngine(
                    target=t, focus=a.focus, aggressive=a.aggressive,
                    fast=a.fast, resume=a.resume, spam_link=a.spam_link,
                    pingback_url=a.pingback, telegraph_count=a.telegraph,
                    web20=a.web20, guestbook=a.guestbook)
                futs[ex.submit(eng.run)] = t
            for fut in as_completed(futs):
                t = futs[fut]
                try:
                    fut.result()
                    print(f"  {t}: DONE")
                except Exception as e:
                    print(f"  {t}: ERROR - {e}")
        sys.exit(0)

    if not a.target:
        # Run without target — just create backlinks
        eng = BacklinkDominatorEngine(
            focus=a.focus, aggressive=a.aggressive,
            fast=a.fast, resume=a.resume, spam_link=a.spam_link,
            pingback_url=a.pingback, telegraph_count=a.telegraph,
            web20=a.web20, guestbook=a.guestbook)
        eng.run()
    else:
        eng = BacklinkDominatorEngine(
            target=a.target, focus=a.focus, aggressive=a.aggressive,
            fast=a.fast, resume=a.resume, spam_link=a.spam_link,
            pingback_url=a.pingback, telegraph_count=a.telegraph,
            web20=a.web20, guestbook=a.guestbook)
        eng.run()