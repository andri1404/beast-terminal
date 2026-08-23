Run full reconnaissance on $ARGUMENTS:
1. DNS enumeration — dig ANY, MX, TXT (SPF), NS records
2. Subdomain discovery — check common subdomains (admin, api, dev, staging, mail, webmail, cpanel, etc.)
3. Technology fingerprinting — whatweb, header analysis
4. Port scanning — top 1000 ports with service detection
5. Directory enumeration — common paths (.git, .env, backups, admin panels)
6. JavaScript analysis — extract endpoints, API keys, secrets from page source
7. CVE matching — search CVEs for detected tech stack versions
8. WAF/CDN detection — check for Cloudflare, AWS WAF, etc.
9. SSL certificate analysis — check crt.sh for subdomains
10. Summary report — all findings with severity ratings

Use curl_cffi with TLS impersonation for Cloudflare-fronted targets. Use DataImpulse proxy if direct IP is blocked.