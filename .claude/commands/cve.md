Search CVEs for $ARGUMENTS (software name, version, or CVE ID):
1. If CVE ID provided (e.g., CVE-2021-44228):
   - Get full CVE details: description, CVSS score, affected versions
   - Search for public exploits (Exploit-DB, GitHub PoCs, Metasploit)
   - Provide exploitation steps with exact commands
2. If software name provided:
   - Search for all CVEs affecting that software
   - Sort by CVSS score (critical first)
   - Filter for CVEs with public exploits
   - For each critical CVE: provide exploitation steps
3. Generate working exploit code or curl commands
4. Include detection methods (how to verify if target is vulnerable)
5. Include bypass techniques if WAF/CDN is present

Use the local CVE database at ~/.hermes/skills-hub.db (377K+ CVEs) via sqlite3.