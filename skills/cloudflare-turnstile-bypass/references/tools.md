# Cloudflare Turnstile Bypass Tools

Curated list of GitHub tools for bypassing Cloudflare Turnstile, tested 2026-08-10.

## Tier 1: Proven Click Techniques

### Browser Snapshot Ref Click
- **Method:** Click checkbox via browser accessibility tree ref
- **Success:** Click works 100%, form appears, but server rejects token ~70% of time
- **Best for:** Sites that accept browser-generated tokens

### Capsolver API
- **Method:** AntiTurnstileTaskProxyLess — no proxy needed
- **Speed:** 3-7 seconds per token
- **Success:** Token generation 100%, server acceptance ~30%
- **Cost:** Pay per solve

## Tier 2: Advanced Techniques

### EzSolver
- **Repo:** https://github.com/ismoiloffS/EzSolver
- **Method:** Injects new Turnstile widget into page DOM, human-like mouse click
- **Language:** Python + nodriver
- **Pros:** Generates valid tokens, no paid APIs, Xvfb auto-start
- **Cons:** React forms don't appear (original Turnstile still blocks)
- **Tested:** 2026-08-10 — token generation works, form not triggered

### SeleniumBase UC Mode
- **Repo:** https://github.com/seleniumbase/SeleniumBase
- **Method:** `uc_gui_click_captcha()` — OS-level click via PyAutoGUI
- **Language:** Python
- **Pros:** Click works 100%, form appears
- **Cons:** Server still rejects token ("Bot check failed")
- **Requirements:** python3-tk, Xvfb on Linux

### cloudflare-bypass-2026
- **Repo:** https://github.com/1837620622/cloudflare-bypass-2026
- **Method:** Multi-strategy: SeleniumBase UC, nodriver CDP, curl_cffi
- **Language:** Python
- **Features:** Proxy rotation, cookie export, batch processing
- **Tested:** 2026-08-10 — UC mode click works, submit fails

## Tier 3: Not Fully Tested

### chaser-cf
- **Repo:** https://github.com/0xchasercat/chaser-cf
- **Method:** CDP shadow-root traversal + browser-level click
- **Language:** Rust with C FFI
- **Status:** Build failed (disk space, pkg-config issues)

### cloudflare-solver
- **Repo:** https://github.com/art3m4ik3/cloudflare-solver
- **Method:** Camoufox + BrowserForge stealth browser
- **Language:** Python + Playwright
- **Status:** Not tested (requires Camoufox setup)

### turnstile_solver
- **Repo:** https://github.com/hasnainshahidx/turnstile_solver
- **Method:** CDP + OpenCV template matching
- **Language:** Python + Selenium
- **Status:** Not tested

### nodriver-cf-bypass
- **Repo:** https://github.com/ganpei777/nodriver-cf-bypass
- **Method:** Iframe detection + click simulation
- **Language:** Python + nodriver
- **Status:** Not tested

### DrissionPage
- **Repo:** https://github.com/g1879/DrissionPage
- **Method:** Native shadow_root access, DOM traversal
- **Language:** Python
- **Status:** Can click checkbox, React callback not triggered

## Key Learnings

1. **No tool reliably bypasses server-side token validation** — Cloudflare Enterprise tier detects automated clicks regardless of method
2. **Browser compositor-level click** (browser snapshot ref) is the most reliable way to trigger the checkbox
3. **Capsolver tokens** are valid but often rejected by strict server-side checks
4. **React/Next.js forms** require the Turnstile callback to fire — injected widgets don't trigger it
5. **Only manual human click** consistently passes all validation layers