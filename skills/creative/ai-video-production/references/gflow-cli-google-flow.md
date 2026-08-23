# gflow-cli & Google Flow API Deep Dive

## gflow-cli v0.53.1 Command Inventory

```
gflow auth          — Manage Google sessions (login, logout, list, status, use)
gflow video         — T2V, I2V, R2V, chain video generation
gflow image         — T2I, I2I via Nano Banana / Imagen
gflow movie         — Multi-scene movie from TOML project file
gflow character     — Manage persistent character entities
gflow scene         — Compose ordered video clips into Flow Scene
gflow project       — Manage Google Flow projects
gflow models        — List available image + video models and their caps
gflow data          — Read local gflow media history
gflow run           — Execute JSON-described batch of generations
gflow serve         — Start MCP server over HTTP
gflow mcp           — MCP server for IDE/agent integration
gflow tools         — Discover and run prompt tools
gflow instructions  — Manage Agent-Mode brief for a project
```

### Quick Health Check

```bash
gflow auth status              # Check if profile has valid cookies
gflow models                   # List available models and their ref caps
gflow auth list --json         # Machine-readable profile inventory
```

1. `gflow auth login --browser chrome` opens a plain Chrome (no remote-debugging)
2. User signs in with Google (including 2FA)
3. User navigates to Flow editor (labs.google/fx/tools/flow)
4. User closes the browser
5. gflow verifies the Flow session and saves the Playwright persistent context
6. Profile stored at `~/.local/share/gflow-cli/profile_default/`

Subsequent commands launch headless Playwright using the saved profile, calling REST endpoints via Playwright's HTTP client which auto-attaches cookies.

## Why Google Blocks Headless Sign-In

Google blocks sign-in in browsers with remote debugging enabled ("this browser or app may not be secure"). gflow's strategy:
1. Open plain Chrome for sign-in (no CDP flags)
2. After sign-in, reopen the same profile with CDP for automation
3. Automation only loads Flow with valid cookies, never the sign-in page

## Headless Server Auth — Pitfalls & Reliable Methods

### ⚠️ CRITICAL: Cross-Platform Chrome Profile Incompatibility

**Chrome encrypts cookies with OS-specific keys.** A profile created by `gflow auth login --browser chrome` on Windows stores encrypted cookies that CANNOT be decrypted on Linux. The `v10` prefix in `encrypted_value` indicates Chrome's OS-keychain-backed encryption. Chrome on Linux uses a different keychain (GNOME Keyring / KWallet / plaintext fallback), so the Windows profile's cookies are unreadable.

**Symptoms:**
- `gflow auth status` shows `cookies_present: True`
- The real Chrome on Linux can open the profile and shows the Flow landing page
- But `gflow video t2v` fails with `ProfileLockedError` or Playwright can't use the session
- The cookies DB has entries but the values are encrypted blobs

**Fix: Use Playwright Chromium for auth (portable), not real Chrome**
```bash
# On Windows — use internal browser (Playwright Chromium, NOT real Chrome)
gflow auth login --browser internal
# Playwright Chromium stores cookies in plaintext SQLite — cross-platform compatible
```

**Alternative: Export cookies from real Chrome on Windows**
1. Install a Chrome extension: "Export Cookies" or "EditThisCookie"
2. Export cookies for `labs.google.com` and `.google.com` as JSON
3. Transfer the JSON file to the server
4. Use a script to inject cookies into the Playwright Chromium profile

**Alternative: Re-auth on the Linux server itself**
If you can VNC into the server (x11vnc is installed), run `gflow auth login --browser chrome` directly on the server. The profile will be created with Linux-compatible encryption.

### ⚠️ Pitfall: gflow auth login --browser chrome vs --browser internal

| Flag | Browser | Google Accepts? | Cookies Portable? | Use Case |
|------|---------|----------------|-------------------|----------|
| `--browser chrome` | Real Chrome (no CDP) | ✅ Yes | ❌ OS-encrypted | Auth on same machine you'll use for generation |
| `--browser internal` | Playwright Chromium (CDP) | ❌ Blocked | ✅ Plaintext SQLite | Cross-platform profile transfer |

**The dilemma:** `--browser chrome` works for auth but produces non-portable cookies. `--browser internal` produces portable cookies but Google blocks the sign-in. There is no single flag that works for both cross-platform transfer AND Google sign-in.

### ✅ Recommended: Direct auth on the server (VNC)

The most reliable approach is to run `gflow auth login --browser chrome` directly on the Linux server via VNC. This produces a Linux-native profile with no encryption issues.

```bash
# On server: start Xvfb + x11vnc
Xvfb :99 -screen 0 1280x720x24 -ac &
DISPLAY=:99 gflow auth login --browser chrome &
x11vnc -display :99 -forever -nopw -listen 0.0.0.0 -rfbport 5900

# User connects VNC client → server_ip:5900 → signs in → closes browser
# Profile saved at ~/.local/share/gflow-cli/profile_default/ — ready to use
```

### ⚠️ Pitfall: xdotool does NOT work on bare Xvfb

`xdotool windowactivate` fails on Xvfb because there is no window manager (`_NET_ACTIVE_WINDOW` not supported). `xdotool click` and `xdotool key --window` are unreliable — clicks often don't register, keystrokes may go to the wrong window. Do NOT try to script the auth flow with xdotool on Xvfb.

### ⚠️ Pitfall: Playwright/CDP browsers blocked by Google

Google returns *"This browser or app may not be secure"* for any browser with remote debugging (CDP) enabled. This includes Playwright's Chromium, `browser_navigate` / `browser_click` tools, and `gflow auth login --browser internal`. Only `--browser chrome` (real Chrome without CDP flags) works for sign-in.

### ⚠️ Pitfall: DataImpulse residential proxy does NOT bypass Google's bot detection

Google blocks DataImpulse residential proxy IPs at the network level. `labs.google/fx/tools/flow` times out (60s+) when routed through DataImpulse. `google.com` times out. `accounts.google.com` times out. httpbin.org works fine — confirming the proxy itself is functional but Google-specific domains are blocked. Do NOT waste time trying proxy-based auth bypass.

`gflow auth login` opens Chrome and waits for the user to sign in manually. On a headless server, there is no way to interact with the browser unless you have VNC access. The process will sit forever waiting.

### ✅ Reliable Method: Auth on a real machine, copy profile

**Linux/macOS:**
```bash
pip install gflow-cli
playwright install chromium
gflow auth login --browser chrome
# Complete sign-in, close browser when Flow editor loads
tar -czf gflow-profile.tar.gz -C ~/.local/share/gflow-cli .
scp gflow-profile.tar.gz user@server:~
# On server: tar -xzf gflow-profile.tar.gz -C ~/.local/share/gflow-cli/
```

**Windows (PowerShell):**
```powershell
pip install gflow-cli
playwright install chromium
gflow auth login --browser chrome
# Complete sign-in, close browser when Flow editor loads

# Profile is at: $env:LOCALAPPDATA\ffroliva\gflow-cli\profile_default
cd $env:LOCALAPPDATA\ffroliva\gflow-cli
Compress-Archive -Path profile_default\* -DestinationPath $env:USERPROFILE\gflow-profile.zip -Force
```

**Google Drive Transfer (no SSH needed):**
1. Upload `gflow-profile.zip` to Google Drive
2. Right-click → Share → General access → "Anyone with the link"
3. Copy share link, extract file ID from URL (e.g., `17IfksxN5tZB_gD40GfKMmcnOGDS1aiyl`)
4. On server:
```bash
# Download (handles Google Drive virus scan warning for large files)
curl -L -o gflow-profile.zip "https://drive.usercontent.google.com/download?id=FILE_ID&export=download&confirm=t"
# Extract to gflow profile
rm -rf ~/.local/share/gflow-cli/profile_default
mkdir -p ~/.local/share/gflow-cli
unzip -o gflow-profile.zip -d ~/.local/share/gflow-cli/profile_default
# Verify
gflow auth status  # should show cookies_present: True
```

### ✅ Method: VNC into Xvfb (requires user interaction)

```bash
# Start Xvfb
Xvfb :99 -screen 0 1280x720x24 -ac &

# Start gflow auth
DISPLAY=:99 gflow auth login --browser chrome &

# Start x11vnc
x11vnc -display :99 -forever -nopw -listen 0.0.0.0 -rfbport 5900

# User connects via VNC client to server:5900, signs in manually, closes browser
```

### ✅ Method: `gflow_auto_login.py` (for reference, blocked by Google on headless)

A Playwright script that automates the Google sign-in flow exists at `scripts/gflow_auto_login.py`. It works on machines with a real display but is blocked by Google's bot detection on headless servers. Use it as a reference for the sign-in flow, not as a reliable headless solution.

## reCAPTCHA Enterprise

All generation endpoints require reCAPTCHA Enterprise tokens. The token is passed in the request body as `recaptchaContext.token`. gflow-cli solves this by:
- Injecting a script into the Flow page's MAIN world
- Calling `grecaptcha.enterprise.execute(SITE_KEY, { action })` where action is `IMAGE_GENERATION` or `VIDEO_GENERATION`
- Splicing the token into API requests

Without a real browser, reCAPTCHA tokens are rejected with 403.

## Model Capabilities

| Model | T2V | I2V | R2V | Max Duration | Max Refs |
|-------|-----|-----|-----|-------------|----------|
| omni-flash | ✅ | ✅ | ✅ | 10s | 7 |
| veo-lite | ✅ | ✅ | ✅ | 8s | 3 |
| veo-fast | ✅ | ✅ | ✅ | 8s | 3 |
| veo-lite-lp | ✅ | ✅ | ✅ | 8s | 3 |
| veo-quality | ✅ | ✅ | ❌ | 8s | 0 |

## gflow movie.toml Format

```toml
[project]
title = "My Short Film"

[[scenes]]
prompt = "Scene 1 description..."
duration = 8
model = "veo-fast"

[[scenes]]
prompt = "Scene 2 description..."
duration = 6
model = "veo-fast"
```

## Alternative Tools

**All tools face the same headless auth problem** — Google's reCAPTCHA Enterprise + bot detection means every tool requires a real browser session. None work on truly headless servers without manual auth on a display-equipped machine first.

| Tool | Lang | Auth Method | Key Features | Status |
|------|------|------------|-------------|--------|
| **gflow-cli** (ffroliva) | Python | Playwright + real Chrome | T2V, I2V, R2V, movie, character, MCP | ✅ Installed v0.53.1 |
| **flow-py** (eddie-fqh) | Python | Playwright + CDP attach | T2V, I2V, Extend, Upscale (free), Camera, Insert, Remove | ✅ Installed v0.1.0 |
| **flow-agent** (kodelyx) | Python/Go | Chrome Extension | OpenAI-compatible API, standalone binaries, MCP v2 | ❌ Needs Chrome Extension |
| **swissmarley/gflow-cli** | Node.js | Real Chrome only | `npm install -g`, T2V, I2V, batch, upscale 2K/4K | ❌ Not installed |
| **flow-google-captcha** (lugondev) | Chrome Ext | Bridges real Flow tab | reCAPTCHA solver, WS transport to local agent | ❌ Needs Chrome Extension |
| **Flow-Agent-Studio** (kodelyx) | Docker | Chrome Ext in container | Full OpenAI-compatible API, web UI, headless Chrome container | ❌ Heavy Docker setup |
| **glabs-sdk** (@getvrex) | TypeScript | Browser session | OpenAI-compatible server | ❌ Not explored |
| **flow-captcha-solver** (sonrasa2k) | Python | Playwright pool | Multi-browser reCAPTCHA v3 solver, auto-reset | ❌ Not explored |
| **useapi.net** | REST API | API token | Paid ($15/mo), no browser needed | ❌ Paid |

## n8n Community Nodes (OFFICIAL Gemini API — no browser auth!)

Unlike the reverse-engineered CLI tools above, n8n community nodes use the **official Google Gemini API** (API key from Google AI Studio) or **Vertex AI** (GCP Service Account). This completely bypasses the browser auth + reCAPTCHA problem.

| Node | Auth | Install |
|------|------|---------|
| `n8n-nodes-googleflow-ai` | Google Flow session | `npm install n8n-nodes-googleflow-ai` |
| `n8n-nodes-veo` (morekaccino) ⭐ | **Gemini API Key** | `npm install n8n-nodes-veo` |
| `n8n-nodes-google-vertex-ai` | GCP Service Account | `npm install n8n-nodes-google-vertex-ai` |
| `n8n-nodes-vertex-ai-full` (flavien317) | GCP Service Account | `npm install n8n-nodes-vertex-ai-full` |

**Direct curl via Gemini API (no n8n needed):**
```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-generate-preview:predictLongRunning" \
  -H "x-goog-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"instances":[{"prompt":"your video prompt"}]}'
```

API key from: https://aistudio.google.com/apikey

### flow-py Quick Reference

```bash
# Install from source (PyPI package is a gflow-cli alias)
git clone https://github.com/eddie-fqh/flow-py.git
cd flow-py && pip install -e ".[dev]"

# Key commands (same auth problem as gflow-cli)
python3 -m flow.cli.main video "prompt"        # T2V
python3 -m flow.cli.main extend <media_id>     # Extend video
python3 -m flow.cli.main upscale <media_id>    # FREE upscale to 1080p/4K
python3 -m flow.cli.main camera <media_id> --motion dolly-in
python3 -m flow.cli.main credits               # Check credits
python3 -m flow.cli.main models                # List models + costs
```

### CDP Attach (flow-py only)

flow-py can connect to an existing Chrome via CDP, avoiding the persistent profile lock issue:
```python
from flow._browser import BrowserManager
bm = BrowserManager.from_cdp("http://127.0.0.1:9222")
await bm.start()
```

### Debugging: Verify session validity via CDP

When a profile transfer fails, use CDP to check if the session is actually valid:

```bash
# 1. Start Chrome with the profile + CDP
google-chrome --user-data-dir=~/.local/share/gflow-cli/profile_default \
  --remote-debugging-port=9222 --no-first-run \
  "https://labs.google/fx/tools/flow" &

# 2. Check pages
curl -s http://localhost:9222/json | python3 -m json.tool

# 3. Check cookies in the profile
python3 -c "
import sqlite3
db = '$HOME/.local/share/gflow-cli/profile_default/Default/Network/Cookies'
conn = sqlite3.connect(db)
rows = conn.execute(\"SELECT host_key, name FROM cookies WHERE host_key LIKE '%google%'\").fetchall()
for r in rows: print(f'{r[0]}: {r[1]}')
conn.close()
"

# 4. Check if encrypted (v10 prefix = OS-keychain encrypted, cross-platform incompatible)
python3 -c "
import sqlite3
db = '$HOME/.local/share/gflow-cli/profile_default/Default/Network/Cookies'
conn = sqlite3.connect(db)
rows = conn.execute(\"SELECT host_key, name, hex(substr(encrypted_value,1,3)) FROM cookies WHERE host_key LIKE '%google%'\").fetchall()
for r in rows: print(f'{r[0]}:{r[1]} prefix={r[2]}')
conn.close()
"
# If prefix is '763130' (ASCII 'v10'), cookies are encrypted and NOT portable
```

### Verified: No Exploit / Auth Bypass Exists

- No CVEs for Google Flow API itself
- No working auth bypass — reCAPTCHA Enterprise is the hard gate
- Google API key leak vulnerability (Truffle Security, 2025-2026) affects Gemini API keys, not Flow auth
- All open-source tools rely on browser-based session capture