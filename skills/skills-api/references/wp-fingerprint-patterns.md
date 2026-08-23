# WordPress Fingerprinting — High-Yield Patterns

Compiled from live pentest sessions. These patterns reliably extract plugin/theme versions from WordPress page source without needing authenticated access.

## Source: HTML `<head>` + inline `<script>`

WordPress dumps plugin versions, REST API routes, and nonces directly into the page source. The `lpData` (LearnPress) and `revslider` (Slider Revolution) inline JS objects are gold mines.

## Key Patterns

### 1. LearnPress — `lpData` object
```bash
curl -sk "https://{target}" | grep -oP '"lp_version":"[^"]+"'
# → "lp_version":"4.2.8.7"
```
Also exposes: `lp_rest_url`, `ajaxUrl`, `nonce`, `site_url`, `user_id`

### 2. Slider Revolution — `revslider` references
```bash
curl -sk "https://{target}" | grep -oP 'revslider[^"]*ver=[0-9.]+'
# → revslider/sr6/assets/js/rs6.min.js?ver=6.7.23
```
Also check: `data-version="6.7.23"` in `<rs-module>` tags

### 3. WordPress Core — `<meta name="generator">`
```bash
curl -sk "https://{target}" | grep -oP 'meta name="generator"[^>]+content="[^"]+"'
# → content="WordPress 6.9.6"
```

### 4. Plugin versions from CSS/JS enqueues
```bash
curl -sk "https://{target}" | grep -oP 'wp-content/plugins/[^/]+/[^" ]+\?ver=[0-9.]+' | sort -u
```
Output example:
```
wp-content/plugins/contact-form-7/includes/css/styles.css?ver=6.0.6
wp-content/plugins/goodlayers-core/plugins/style.css?ver=1750423264
wp-content/plugins/learnpress/assets/js/dist/loadAJAX.min.js?ver=4.2.8.7
```

### 5. Theme version
```bash
curl -sk "https://{target}" | grep -oP 'wp-content/themes/[^/]+/[^" ]+\?ver=[0-9.]+' | sort -u
```

### 6. REST API namespace enumeration
```bash
curl -sk "https://{target}/wp-json/" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for ns in d.get('namespaces',[]):
    print(ns)
"
```
Output reveals ALL registered plugins with REST API endpoints.

### 7. User enumeration (unauthenticated)
```bash
curl -sk "https://{target}/wp-json/wp/v2/users"
# → Returns user list with IDs, slugs, names
```
If 200: user enumeration is possible. Map slugs to usernames for brute-force.

### 8. Plugin readme.txt (version + changelog)
```bash
curl -sk "https://{target}/wp-content/plugins/{plugin-slug}/readme.txt" | head -10
```
Works for most plugins. The `Stable tag:` line gives the exact version.

## Version → CVE Mapping (Quick Reference)

| WordPress | CVE | Impact |
|-----------|-----|--------|
| 6.9.0-6.9.4 | CVE-2026-63030 (wp2shell) | Pre-auth RCE via batch/v1 |
| 6.9.0-6.9.5 | CVE-2026-64638 | Pre-auth XSS on login |
| 6.9.6+ | — | Patched for both above |

| LearnPress | CVE | Impact |
|-----------|-----|--------|
| ≤ 4.2.7 | CVE-2024-8522 | Unauthenticated SQLi (c_only_fields) |
| ≤ 4.2.7 | CVE-2024-8529 | Unauthenticated SQLi (c_fields) |
| 4.2.7.1+ | — | Patched |

| Slider Revolution | CVE | Impact |
|------------------|-----|--------|
| ≤ 6.7.37 | CVE-2025-10249 | Contributor+ arbitrary file read |
| ≤ 6.7.36 | CVE-2025-9217 | Contributor+ path traversal |
| 6.7.38+ | — | Patched |