#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║     🔥 LISA ORCHESTRATOR — Unified Cyber Arsenal Command       ║
║     One command → fingerprint → CVE → exploit → Lisa → report  ║
╚══════════════════════════════════════════════════════════════════╝

Usage:
  python3 orchestrator.py sniff <target>          # CVE + exploit hunt
  python3 orchestrator.py exploit <target>        # Full exploit chain
  python3 orchestrator.py recon <target>          # Recon only
  python3 orchestrator.py satset <target>         # One-shot: recon → exploit
  python3 orchestrator.py tembak <target>         # Auto-exploit with Lisa
  python3 orchestrator.py full <target>           # EVERYTHING (all phases)
  python3 orchestrator.py cve <keyword>           # CVE search only
  python3 orchestrator.py jailbreak <persona> <q> # Run jailbreak persona
  python3 orchestrator.py status                  # Arsenal status

Options:
  --fast          Skip heavy scans (feroxbuster, nuclei)
  --focus <type>  Focus: wp, joomla, laravel, ci3, nextjs, django, etc
  --auto          Fully autonomous, no interactive prompts
  --output <dir>  Save reports to directory (default: ./lisa_reports/)
  --proxy <url>   Use proxy (e.g. http://gw.dataimpulse.com:823)
"""

import subprocess, sys, json, re, time, os, sqlite3, argparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════

HOME = Path.home()
SKILLS_DB = HOME / ".hermes" / "skills-hub.db"
SNIFF_SCRIPT = HOME / ".hermes" / "scripts" / "sniff.py"
JAILBREAK_SCRIPT = HOME / "jailbreak-arsenal.py"
LISA_EXEC_DIR = HOME / "pentest-cli" / "lisa" / "exec"
REPORTS_DIR = Path.cwd() / "lisa_reports"

# Tool paths
WHATWEB = "whatweb"
HTTPX = "httpx"
FEROXBUSTER = "feroxbuster"
NUCLEI = "nuclei"
SQLMAP = "sqlmap"
CURL = "curl"

# Colors
C = {
    "R": "\033[91m", "G": "\033[92m", "Y": "\033[93m", "B": "\033[94m",
    "M": "\033[95m", "C": "\033[96m", "W": "\033[97m", "D": "\033[90m",
    "BOLD": "\033[1m", "RESET": "\033[0m"
}

# ═══════════════════════════════════════════════════════════════
# UTILS
# ═══════════════════════════════════════════════════════════════

def banner():
    print(f"""{C['R']}{C['BOLD']}
╔══════════════════════════════════════════════════════════════════╗
║     🔥 LISA ORCHESTRATOR — Unified Cyber Arsenal               ║
║     Sniff · CVE · Exploit · Lisa · Jailbreak · Report          ║
╚══════════════════════════════════════════════════════════════════╝
{C['RESET']}""")

def run(cmd, timeout=60, shell=True):
    """Execute shell command, return (stdout, stderr, exit_code)"""
    try:
        r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "").strip(), (r.stderr or "").strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except Exception as e:
        return "", str(e), -1

def log(phase, msg, color="W"):
    """Pretty log with timestamp"""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{C['D']}[{ts}]{C['RESET']} {C[color]}{C['BOLD']}[{phase}]{C['RESET']} {msg}")

def ok(msg):
    print(f"  {C['G']}✓{C['RESET']} {msg}")

def warn(msg):
    print(f"  {C['Y']}⚠{C['RESET']} {msg}")

def fail(msg):
    print(f"  {C['R']}✗{C['RESET']} {msg}")

def critical(msg):
    print(f"  {C['R']}{C['BOLD']}💥 {msg}{C['RESET']}")

def section(title):
    print(f"\n{C['BOLD']}{C['C']}═══ {title} ═══{C['RESET']}")

# ═══════════════════════════════════════════════════════════════
# PHASE 1: FINGERPRINT
# ═══════════════════════════════════════════════════════════════

def phase_fingerprint(target, proxy=None):
    """Run all fingerprint tools in parallel"""
    section("PHASE 1: FINGERPRINT")
    
    results = {"target": target, "tech": [], "server": "", "cms": "", "version": ""}
    proxy_flag = f"--proxy {proxy}" if proxy else ""
    
    def run_whatweb():
        out, _, _ = run(f"{WHATWEB} -a 3 --no-errors {target} 2>/dev/null", timeout=30)
        return ("whatweb", out)
    
    def run_httpx():
        out, _, _ = run(f"{HTTPX} -u {target} -tech-detect -status-code -title -server -silent 2>/dev/null", timeout=20)
        return ("httpx", out)
    
    def run_curl_headers():
        out, _, _ = run(f"{CURL} -skI --max-time 10 {proxy_flag} {target} 2>&1 | grep -iE 'server:|x-powered|set-cookie|location'", timeout=15)
        return ("headers", out)
    
    def run_curl_body():
        out, _, _ = run(f"{CURL} -sk --max-time 10 {proxy_flag} {target} 2>&1 | grep -iE 'wp-content|generator|version|drupal|joomla|laravel|rails|next|nuxt|react|vue|angular|ci_version|codeigniter' | head -20", timeout=15)
        return ("body_tech", out)
    
    tasks = [run_whatweb, run_httpx, run_curl_headers, run_curl_body]
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(t): t.__name__ for t in tasks}
        for f in as_completed(futures):
            name, output = f.result()
            if output:
                ok(f"{name}: {output[:150]}...")
                results[name] = output
            else:
                warn(f"{name}: no output")
                results[name] = ""
    
    # Parse tech stack from whatweb
    ww = results.get("whatweb", "")
    tech_keywords = {
        "wordpress": "wp", "joomla": "joomla", "drupal": "drupal",
        "laravel": "laravel", "django": "django", "rails": "rails",
        "next.js": "nextjs", "nuxt": "nuxtjs", "react": "react",
        "apache": "apache", "nginx": "nginx", "php": "php",
        "strapi": "strapi", "directus": "directus", "codeigniter": "ci3",
        "express": "express", "flask": "flask", "spring": "spring",
    }
    for kw, tag in tech_keywords.items():
        if kw in ww.lower():
            results["tech"].append(tag)
    
    # Extract version
    ver_match = re.search(r'(?:WordPress|Joomla|Drupal|Apache|nginx|PHP|Laravel|Next\.js)[/\s]*([\d.]+)', ww, re.IGNORECASE)
    if ver_match:
        results["version"] = ver_match.group(1)
    
    return results

# ═══════════════════════════════════════════════════════════════
# PHASE 2: CVE HUNTING
# ═══════════════════════════════════════════════════════════════

def phase_cve_hunt(target, fingerprint, focus=None):
    """Search 379K CVEs for exploit-ready matches"""
    section("PHASE 2: CVE HUNTING")
    
    if not SKILLS_DB.exists():
        fail(f"Skills DB not found: {SKILLS_DB}")
        return []
    
    db = sqlite3.connect(str(SKILLS_DB))
    
    # Build search keywords from fingerprint
    keywords = fingerprint.get("tech", [])[:5]
    if focus:
        keywords.insert(0, focus)
    
    # Also extract domain keywords
    domain = target.replace("https://", "").replace("http://", "").split("/")[0]
    domain_kw = domain.split(".")[0] if "." in domain else domain
    if domain_kw and len(domain_kw) > 2:
        keywords.append(domain_kw)
    
    all_cves = []
    seen = set()
    
    for kw in keywords[:7]:  # Max 7 keyword searches
        log("CVE", f"Searching: {kw}", "Y")
        
        # Try FTS5
        try:
            rows = db.execute('''
                SELECT c.cve_id, c.cvss_severity, c.exploit_count, c.cvss_score,
                       substr(c.description, 1, 200), c.exploit_refs
                FROM cves_fts f JOIN cves c ON f.rowid = c.id
                WHERE cves_fts MATCH ? AND c.exploit_count > 0
                ORDER BY c.cvss_score DESC LIMIT 10
            ''', (kw.replace(".", " "),)).fetchall()
        except:
            # Fallback to LIKE
            rows = db.execute('''
                SELECT c.cve_id, c.cvss_severity, c.exploit_count, c.cvss_score,
                       substr(c.description, 1, 200), c.exploit_refs
                FROM cves c
                WHERE c.description LIKE ? AND c.exploit_count > 0
                ORDER BY c.cvss_score DESC LIMIT 10
            ''', (f'%{kw}%',)).fetchall()
        
        for r in rows:
            cve_id = r[0]
            if cve_id not in seen:
                seen.add(cve_id)
                all_cves.append({
                    "cve_id": r[0], "severity": r[1], "exploit_count": r[2],
                    "cvss": r[3], "desc": r[4], "refs": r[5]
                })
    
    db.close()
    
    # Sort by CVSS
    all_cves.sort(key=lambda x: x["cvss"] or 0, reverse=True)
    
    # Display
    critical_count = sum(1 for c in all_cves if c["severity"] == "CRITICAL")
    high_count = sum(1 for c in all_cves if c["severity"] == "HIGH")
    
    if all_cves:
        print(f"\n  {C['R']}💥 {critical_count} CRITICAL{C['RESET']} | {C['Y']}⚠ {high_count} HIGH{C['RESET']} | {len(all_cves)} total exploit-ready")
        for cve in all_cves[:10]:
            sev_color = C['R'] if cve["severity"] == "CRITICAL" else C['Y'] if cve["severity"] == "HIGH" else C['D']
            print(f"  {sev_color}{cve['cve_id']}{C['RESET']} {C['D']}CVSS:{cve['cvss']}{C['RESET']} 🔫{cve['exploit_count']} — {cve['desc'][:120]}")
            if cve.get("refs"):
                print(f"    {C['D']}Refs: {cve['refs'][:100]}{C['RESET']}")
    else:
        warn("No exploit-ready CVEs found for these keywords")
    
    return all_cves

# ═══════════════════════════════════════════════════════════════
# PHASE 3: LISA AI ANALYSIS
# ═══════════════════════════════════════════════════════════════

def phase_lisa_analysis(target, fingerprint, cves, fast=False):
    """Run Lisa AI for strategy + exploit recommendations"""
    section("PHASE 3: LISA AI ANALYSIS")
    
    # Build context for Lisa
    tech = ", ".join(fingerprint.get("tech", ["unknown"]))
    top_cves = "\n".join([f"{c['cve_id']} (CVSS {c['cvss']}) — {c['desc'][:100]}" for c in cves[:5]])
    
    prompt = f"""TARGET: {target}
TECH STACK: {tech}
SERVER: {fingerprint.get('server', 'unknown')}
VERSION: {fingerprint.get('version', 'unknown')}

TOP EXPLOIT-READY CVEs:
{top_cves}

INSTRUCTIONS:
1. Identify the BEST attack vector based on the tech stack
2. Rank CVEs by exploitability (not just CVSS)
3. Provide a step-by-step attack chain
4. Recommend specific tools/commands to use
5. If WordPress: check xmlrpc, plugins, themes
6. If Joomla: check JCE editor, com_components
7. If Laravel: check .env, debug mode, APP_KEY
8. If next.js: check React2Shell, middleware bypass

Respond in Indonesian with technical details. Be specific."""
    
    # Try to run via Lisa exec
    lisa_script = LISA_EXEC_DIR / "lisa_v8_exec.py" if not fast else LISA_EXEC_DIR / "lisa_v8_exec_v20.py"
    
    if lisa_script.exists():
        log("LISA", f"Running {lisa_script.name}...", "M")
        out, _, code = run(f"python3 {lisa_script} {target} --fast 2>&1 | head -100", timeout=120)
        if out:
            print(f"\n{C['M']}{out[:2000]}{C['RESET']}")
        else:
            warn("Lisa returned no output")
    else:
        warn("Lisa exec scripts not found, skipping AI analysis")
    
    return prompt

# ═══════════════════════════════════════════════════════════════
# PHASE 4: EXPLOIT SEARCH
# ═══════════════════════════════════════════════════════════════

def phase_exploit_search(cves, fast=False):
    """Search Exploit-DB and GitHub for PoCs"""
    section("PHASE 4: EXPLOIT SEARCH")
    
    for cve in cves[:5]:
        cve_id = cve["cve_id"]
        refs = cve.get("refs", "")
        
        if "EDB-ID:" in str(refs):
            edb_ids = re.findall(r'EDB-ID:\s*(\d+)', str(refs))
            for eid in edb_ids:
                critical(f"Exploit-DB: https://www.exploit-db.com/exploits/{eid}")
        
        # Quick GitHub search hint
        print(f"  {C['B']}GitHub:{C['RESET']} https://github.com/search?q={cve_id}+exploit&type=repositories")
    
    if not cves:
        warn("No CVEs to search exploits for")

# ═══════════════════════════════════════════════════════════════
# PHASE 5: ACTIVE PROBE
# ═══════════════════════════════════════════════════════════════

def phase_active_probe(target, cves, fast=False, proxy=None):
    """Active endpoint discovery and validation"""
    section("PHASE 5: ACTIVE PROBE")
    
    proxy_flag = f"--proxy {proxy}" if proxy else ""
    
    # Quick path probe (always run)
    paths = [
        "/.env", "/.git/HEAD", "/phpinfo.php", "/admin", "/api",
        "/graphql", "/swagger", "/actuator/env", "/_ignition/health-check",
        "/wp-json/wp/v2/users", "/wp-login.php", "/xmlrpc.php",
        "/administrator", "/.DS_Store", "/backup.zip", "/config.php.bak",
        "/console", "/debug", "/django-admin", "/laravel.log",
        "/storage/logs/laravel.log", "/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    ]
    
    def probe_path(path):
        url = f"{target.rstrip('/')}{path}"
        out, _, _ = run(f"{CURL} -sk -o /dev/null -w '%{{http_code}}' --max-time 5 {proxy_flag} {url}", timeout=10)
        return (path, out.strip())
    
    log("PROBE", f"Testing {len(paths)} common paths...", "C")
    
    findings = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(probe_path, p): p for p in paths}
        for f in as_completed(futures):
            path, code = f.result()
            if code and code != "404" and code != "000":
                if code in ["200", "301", "302", "403", "401", "500"]:
                    color = C['G'] if code == "200" else C['Y']
                    print(f"  {color}[{code}]{C['RESET']} {path}")
                    findings.append({"path": path, "status": code})
    
    if not findings:
        warn("No interesting paths found")
    
    # Feroxbuster (skip if fast)
    if not fast:
        log("FER0X", "Brute forcing endpoints...", "C")
        ferox_out, _, _ = run(
            f"{FEROXBUSTER} -u {target} -w /usr/share/seclists/Discovery/Web-Content/common.txt "
            f"-s 200,301,302,403,401,500 --no-state -t 30 -k -q 2>/dev/null | head -30",
            timeout=60
        )
        if ferox_out:
            print(f"\n{C['D']}{ferox_out[:1000]}{C['RESET']}")
    
    # CVE-specific probes
    for cve in cves[:3]:
        cve_id = cve["cve_id"]
        desc = cve.get("desc", "").lower()
        
        if "laravel" in desc and ".env" in desc:
            out, _, _ = run(f"{CURL} -sk --max-time 5 {proxy_flag} {target}/.env 2>&1 | head -5", timeout=10)
            if "APP_KEY" in out or "DB_" in out:
                critical(f"🔥 .env LEAKED! {target}/.env")
                print(f"    {out[:300]}")
    
    return findings

# ═══════════════════════════════════════════════════════════════
# PHASE 6: REPORT
# ═══════════════════════════════════════════════════════════════

def phase_report(target, fingerprint, cves, findings, output_dir=None):
    """Generate structured report"""
    section("PHASE 6: REPORT")
    
    if not output_dir:
        output_dir = REPORTS_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = target.replace("https://", "").replace("http://", "").split("/")[0].replace(".", "_")
    report_file = output_dir / f"lisa_{domain}_{ts}.json"
    
    report = {
        "target": target,
        "timestamp": datetime.now().isoformat(),
        "fingerprint": {
            "tech": fingerprint.get("tech", []),
            "server": fingerprint.get("server", ""),
            "version": fingerprint.get("version", ""),
            "whatweb": fingerprint.get("whatweb", "")[:500],
            "httpx": fingerprint.get("httpx", "")[:300],
        },
        "cves": cves,
        "active_findings": findings,
        "stats": {
            "total_cves": len(cves),
            "critical": sum(1 for c in cves if c["severity"] == "CRITICAL"),
            "high": sum(1 for c in cves if c["severity"] == "HIGH"),
            "paths_found": len(findings),
        }
    }
    
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    ok(f"Report saved: {report_file}")
    
    # Print summary
    print(f"""
{C['BOLD']}╔══════════════════════════════════════════════════════════════════╗
║                    🔥 SCAN COMPLETE                              ║
╠══════════════════════════════════════════════════════════════════╣
║ {C['R']}Target:{C['RESET']}  {target[:50]}
║ {C['C']}Tech:{C['RESET']}    {', '.join(fingerprint.get('tech', ['unknown'])[:5])}
║ {C['Y']}CVEs:{C['RESET']}    {len(cves)} exploit-ready ({report['stats']['critical']} CRITICAL, {report['stats']['high']} HIGH)
║ {C['G']}Paths:{C['RESET']}   {len(findings)} interesting endpoints found
║ {C['M']}Report:{C['RESET']}  {report_file}
╚══════════════════════════════════════════════════════════════════╝
{C['RESET']}""")

    return report_file

# ═══════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════

def cmd_sniff(target, **kwargs):
    """CVE + exploit hunt only"""
    fast = bool(kwargs.get("fast", False))
    banner()
    fp = phase_fingerprint(target, kwargs.get("proxy"))
    cves = phase_cve_hunt(target, fp, kwargs.get("focus"))
    phase_exploit_search(cves, fast)
    phase_report(target, fp, cves, [], kwargs.get("output"))

def cmd_exploit(target, **kwargs):
    """Full exploit chain"""
    fast = bool(kwargs.get("fast", False))
    banner()
    fp = phase_fingerprint(target, kwargs.get("proxy"))
    cves = phase_cve_hunt(target, fp, kwargs.get("focus"))
    phase_lisa_analysis(target, fp, cves, fast)
    phase_exploit_search(cves, fast)
    findings = phase_active_probe(target, cves, fast, kwargs.get("proxy"))
    phase_report(target, fp, cves, findings, kwargs.get("output"))

def cmd_recon(target, **kwargs):
    """Recon only"""
    fast = bool(kwargs.get("fast", False))
    banner()
    fp = phase_fingerprint(target, kwargs.get("proxy"))
    findings = phase_active_probe(target, [], fast, kwargs.get("proxy"))
    phase_report(target, fp, [], findings, kwargs.get("output"))

def cmd_satset(target, **kwargs):
    """One-shot: recon → CVE → exploit"""
    banner()
    fp = phase_fingerprint(target, kwargs.get("proxy"))
    cves = phase_cve_hunt(target, fp, kwargs.get("focus"))
    phase_exploit_search(cves, True)
    findings = phase_active_probe(target, cves, True, kwargs.get("proxy"))
    phase_report(target, fp, cves, findings, kwargs.get("output"))

def cmd_tembak(target, **kwargs):
    """Auto-exploit with Lisa"""
    banner()
    fp = phase_fingerprint(target, kwargs.get("proxy"))
    cves = phase_cve_hunt(target, fp, kwargs.get("focus"))
    phase_lisa_analysis(target, fp, cves, False)
    phase_exploit_search(cves, False)
    findings = phase_active_probe(target, cves, False, kwargs.get("proxy"))
    phase_report(target, fp, cves, findings, kwargs.get("output"))

def cmd_full(target, **kwargs):
    """EVERYTHING — all phases, no fast mode"""
    banner()
    fp = phase_fingerprint(target, kwargs.get("proxy"))
    cves = phase_cve_hunt(target, fp, kwargs.get("focus"))
    phase_lisa_analysis(target, fp, cves, False)
    phase_exploit_search(cves, False)
    findings = phase_active_probe(target, cves, False, kwargs.get("proxy"))
    phase_report(target, fp, cves, findings, kwargs.get("output"))

def cmd_cve(keyword, **kwargs):
    """CVE search only"""
    banner()
    fp = {"tech": [keyword], "server": "", "version": ""}
    cves = phase_cve_hunt(keyword, fp, None)
    phase_exploit_search(cves, True)

def cmd_jailbreak(persona, query, **kwargs):
    """Run jailbreak persona"""
    banner()
    section(f"JAILBREAK: {persona}")
    
    jb_path = Path(str(JAILBREAK_SCRIPT))
    if not jb_path.exists():
        fail(f"Jailbreak script not found: {jb_path}")
        return
    
    log("JAILBREAK", f"Running persona '{persona}'...", "M")
    out, _, code = run(f"python3 {jb_path} ask {persona} \"{query}\"", timeout=120)
    if out:
        print(f"\n{C['M']}{out[:3000]}{C['RESET']}")
    else:
        fail("No response from jailbreak")

def cmd_status():
    """Arsenal status check"""
    banner()
    section("ARSENAL STATUS")
    
    checks = {
        "Skills DB": SKILLS_DB.exists(),
        "Sniff Script": SNIFF_SCRIPT.exists(),
        "Jailbreak": JAILBREAK_SCRIPT.exists(),
        "Lisa Exec Dir": LISA_EXEC_DIR.exists(),
        "whatweb": run(f"which {WHATWEB}", timeout=5)[2] == 0,
        "httpx": run(f"which {HTTPX}", timeout=5)[2] == 0,
        "feroxbuster": run(f"which {FEROXBUSTER}", timeout=5)[2] == 0,
        "nuclei": run(f"which {NUCLEI}", timeout=5)[2] == 0,
        "sqlmap": run(f"which {SQLMAP}", timeout=5)[2] == 0,
    }
    
    for name, status in checks.items():
        icon = f"{C['G']}✓{C['RESET']}" if status else f"{C['R']}✗{C['RESET']}"
        print(f"  {icon} {name}")
    
    if SKILLS_DB.exists():
        db = sqlite3.connect(str(SKILLS_DB))
        total = db.execute("SELECT COUNT(*) FROM cves").fetchone()[0]
        exploit = db.execute("SELECT COUNT(*) FROM cves WHERE exploit_count > 0").fetchone()[0]
        db.close()
        print(f"\n  {C['BOLD']}CVEs:{C['RESET']} {total:,} total | {C['R']}{exploit:,} exploit-ready{C['RESET']}")
    
    lisa_count = len(list(LISA_EXEC_DIR.glob("*.py"))) if LISA_EXEC_DIR.exists() else 0
    print(f"  {C['BOLD']}Lisa Modules:{C['RESET']} {lisa_count} scripts")

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

COMMANDS = {
    "sniff": cmd_sniff,
    "exploit": cmd_exploit,
    "recon": cmd_recon,
    "satset": cmd_satset,
    "tembak": cmd_tembak,
    "full": cmd_full,
    "cve": cmd_cve,
    "jailbreak": cmd_jailbreak,
    "status": cmd_status,
}

def main():
    parser = argparse.ArgumentParser(description="🔥 LISA ORCHESTRATOR — Unified Cyber Arsenal")
    parser.add_argument("command", nargs="?", choices=list(COMMANDS.keys()), help="Command to run")
    parser.add_argument("target", nargs="?", help="Target URL, domain, or keyword")
    parser.add_argument("extra", nargs="?", help="Extra arg (for jailbreak: persona name or query)")
    
    parser.add_argument("--fast", action="store_true", help="Skip heavy scans")
    parser.add_argument("--focus", help="Focus: wp, joomla, laravel, ci3, nextjs, django")
    parser.add_argument("--auto", action="store_true", help="Fully autonomous")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--proxy", help="Proxy URL")
    
    args = parser.parse_args()
    
    if not args.command:
        banner()
        print(f"{C['BOLD']}Usage:{C['RESET']} python3 orchestrator.py <command> <target> [options]\n")
        print(f"{C['BOLD']}Commands:{C['RESET']}")
        for cmd, desc in {
            "sniff": "CVE + exploit hunt",
            "exploit": "Full exploit chain (recon → CVE → Lisa → exploit)",
            "recon": "Reconnaissance only",
            "satset": "One-shot: recon → CVE → exploit (fast)",
            "tembak": "Auto-exploit with Lisa AI",
            "full": "EVERYTHING — all phases, no fast mode",
            "cve": "CVE search only",
            "jailbreak": "Run jailbreak persona",
            "status": "Arsenal health check",
        }.items():
            print(f"  {C['Y']}{cmd:<12}{C['RESET']} {desc}")
        print(f"\n{C['D']}Options: --fast --focus <type> --auto --output <dir> --proxy <url>{C['RESET']}")
        return
    
    cmd = args.command
    target = args.target
    extra = args.extra
    
    kwargs = {
        "fast": args.fast,
        "focus": args.focus,
        "auto": args.auto,
        "output": args.output,
        "proxy": args.proxy,
    }
    
    if cmd == "status":
        cmd_status()
    elif cmd == "cve":
        if not target:
            print(f"{C['R']}Usage: orchestrator.py cve <keyword>{C['RESET']}")
            return
        cmd_cve(target, **kwargs)
    elif cmd == "jailbreak":
        if not target:
            print(f"{C['R']}Usage: orchestrator.py jailbreak <persona> <query>{C['RESET']}")
            return
        cmd_jailbreak(target, extra or "", **kwargs)
    else:
        if not target:
            print(f"{C['R']}Usage: orchestrator.py {cmd} <target>{C['RESET']}")
            return
        COMMANDS[cmd](target, **kwargs)

if __name__ == "__main__":
    main()