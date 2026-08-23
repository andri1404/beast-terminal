# BEAST Terminal 🔥

**Multi-Gateway AI Pentest CLI + Web Workspace** — Claude Code-style terminal untuk penetration testing, exploit development, coding, dan vulnerability research.

Powered by **TokenRouter DeepSeek V4 Pro** · GLM-5.2 · BlockRun Nemotron 120B

---

## 📦 Install

### 1. Clone repo (PRIVATE — perlu auth)

Repo ini **private**, jadi clone pakai salah satu cara:

```bash
# Cara A: pakai gh CLI (recommended)
gh auth login
gh repo clone andri1404/beast-terminal

# Cara B: pakai Personal Access Token
git clone https://TOKEN@github.com/andri1404/beast-terminal.git
cd beast-terminal
```

> Dapatkan PAT: GitHub → Settings → Developer settings → Personal access tokens → **repo** scope.

### 2. Install dependencies

```bash
cd beast-terminal
pip install --break-system-packages -r requirements.txt
```

### 3. Set API key

```bash
export HERMES_CUSTOM_API_TOKENROUTER_COM_API_KEY="sk-..."
```

> Tambahkan ke `~/.bashrc` atau `~/.zshrc` biar permanen.

---

## 🚀 Run

```bash
python3 beast.py                      # Interactive (Claude Code-style TUI)
python3 beast.py "recon target.com"   # One-shot
python3 beast.py -l                   # List gateways
python3 beast.py --probe              # Test semua gateway
python3 beast.py --auto target.com    # Auto pentest (recon→vuln→exploit→report)
python3 beast.py "/parallel SQLi vs XSS"  # Ask semua gateway

# Web terminal (browser + HP)
python3 web/server.py                 # lalu buka http://localhost:5000
```

---

## 🌐 Web Terminal (browser/mobile)

```bash
python3 web/server.py        # serve di localhost:5000
ngrok http 5000              # public URL (install ngrok dulu)
```

- 🌐 Akses dari browser/HP/laptop
- 📱 **PWA installable** — "Add to Home Screen"
- 📱 **Mobile key bar** — Tab, Esc, Ctrl+C, panah
- 💾 Session persist di tmux

---

## 🎯 Slash Commands

```
PENTEST:    /recon /exploit /cve /bypass /chain /auto /sqlmap /fuzz
INTEGRASI:  /skill /search /cve-api /web
CODING:     /git /review /edit /! <cmd>
PARALLEL:   /parallel <q>
SESSION:    /model /gateways /tokens /cost /budget /history /report
            /permission /thinking /compact /clear /save /export
STATUS:     /status /probe /help /exit
```

---

## 🔌 Gateways

| ID | Gateway | Model | Status |
|----|---------|-------|--------|
| `tr` | TokenRouter | DeepSeek V4 Pro | ✅ Primary |
| `tr-glm` | TokenRouter | GLM-5.2 | ✅ |
| `tr-free` | TokenRouter | DSv4Pro Free | ⚠️ 503 |
| `blockrun` | BlockRun | Nemotron 120B | ✅ Free |

---

## 📦 Requirements

- Python 3.10+
- `rich` — TUI
- `prompt_toolkit` — interactive input
- `flask` + `flask-socketio` — web terminal
- `curl_cffi` — TLS impersonation (bypass WAF)
- TokenRouter API key: `HERMES_CUSTOM_API_TOKENROUTER_COM_API_KEY`

---

## 🔒 Env Variables (di `.env`)

```bash
HERMES_CUSTOM_API_TOKENROUTER_COM_API_KEY=   # TokenRouter
MCP_EXA_API_KEY=                             # Exa web search (opsional)
DATAIMPULSE_AUTH=                            # Proxy (opsional)
```

> Copy `.env.example` → `.env`, isi, jangan commit.

---

## ⚠️ License

MIT — For **authorized security testing only**.