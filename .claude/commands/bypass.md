Bypass WAF/CDN on $ARGUMENTS:
1. Detect WAF/CDN type (Cloudflare, AWS WAF, Imperva, ModSecurity, etc.)
2. Try these techniques in order:
   a. Origin IP discovery — SPF records, DNS history, SSL certificates, subdomain brute force
   b. TLS fingerprint impersonation — curl_cffi with chrome124, safari17_0, edge101
   c. HTTP Request Smuggling — CL.TE, TE.CL variants
   d. Content-Type confusion — multipart boundary tricks, charset manipulation
   e. Header injection — X-Forwarded-For, X-Originating-IP, X-Real-IP
   f. Chunked transfer encoding — split payload across chunks
   g. Unicode normalization — bypass signature-based detection
   h. Parameter pollution — duplicate parameters, array notation
   i. Browser automation — Playwright to solve captcha, maintain session
3. For each successful bypass, document the exact technique
4. Test that the bypass allows exploitation to proceed
5. If all bypasses fail, suggest alternative attack surfaces (subdomains, APIs, mobile apps)