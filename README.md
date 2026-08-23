# BEAST Terminal 🔥

**Multi-Gateway AI Pentest + Coding Agent Workspace** — Claude Code-style TUI + web terminal untuk penetration testing, exploit development, coding, dan vulnerability research.

Powered by **TokenRouter DeepSeek V4 Pro** · GLM-5.2 · BlockRun Nemotron 120B

---

## 📦 Install

### 1. Clone repo

```bash
git clone https://github.com/andri1404/beast-terminal.git
cd beast-terminal
```

### 2. Install dependencies

```bash
pip install --break-system-packages -r requirements.txt
```

> Pake `--break-system-packages` buat bypass PEP 668 (Ubuntu/Debian). Kalo di venv, ga perlu.

### 3. Set API key

```bash
export HERMES_CUSTOM_API_TOKENROUTER_COM_API_KEY="sk-crcrQ..."
```

> Tambahkan ke `~/.bashrc` biar permanen:
> ```bash
> echo 'export HERMES_CUSTOM_API_TOKENROUTER_COM_API_KEY="sk-..."' >> ~/.bashrc
> source ~/.bashrc
> ```

### 4. Verifikasi

```bash
python3 beast.py --probe    # test semua gateway (harus ALIVE)
```

---

## 🚀 Run

### Mode CLI (Claude Code-style TUI)

```bash
python3 beast.py                          # interactive
python3 beast.py "recon target.com"       # one-shot
python3 beast.py -m tr-glm "jelasin XSS"  # pilih gateway
python3 beast.py --auto target.com        # auto pentest
python3 beast.py --probe                  # test gateway
python3 beast.py -l                       # list gateway
```

### Mode Web Terminal (browser + HP)

```bash
python3 web/server.py                     # serve di http://localhost:5000
```

Akses dari browser manapun. Buat public URL:

```bash
ngrok http 5000                           # → https://xxx.ngrok-free.dev
```

### Symlink ke PATH (opsional)

```bash
sudo ln -sf $(pwd)/beast /usr/local/bin/beast
beast
```

---

## 🎯 Slash Commands

```
PENTEST:   /recon /exploit /cve /bypass /chain /auto /sqlmap /fuzz
INTEGRASI: /skill /search /cve-api /web
CODING:    /git /review /edit /! <cmd>
PARALLEL:  /parallel <q>
SESSION:   /model /gateways /tokens /cost /budget /history /report
           /permission /thinking /compact /clear /save /export
STATUS:    /status /probe /help /exit
```

---

## 🖥️ Deploy 24/7 di VPS

```bash
bash deploy/deploy.sh    # install deps + systemd service + cloudflared
```

Systemd service auto-restart kalo mati. Akses publik via tunnel.

---

## 🔌 Gateways

| ID | Gateway | Model | Status |
|----|---------|-------|--------|
| `tr` | TokenRouter | DeepSeek V4 Pro | ✅ Primary |
| `tr-glm` | TokenRouter | GLM-5.2 | ✅ |
| `tr-free` | TokenRouter | DSv4Pro Free | ⚠️ 503 |
| `blockrun` | BlockRun | Nemotron 120B | ✅ Free |

---

## 🔒 Env Variables

Copy `.env.example` → `.env`, isi, jangan commit:

```bash
cp .env.example .env
# edit .env sesuai credential lo
```

| Variable | Fungsi |
|----------|--------|
| `HERMES_CUSTOM_API_TOKENROUTER_COM_API_KEY` | TokenRouter key |
| `MCP_EXA_API_KEY` | Exa web search (opsional) |
| `DATAIMPULSE_AUTH` | Proxy (opsional) |

---

## 📦 Requirements

- Python 3.10+
- `rich` — TUI
- `prompt_toolkit` — interactive input
- `flask` + `flask-socketio` — web terminal
- `curl_cffi` — TLS impersonation

---

## ⚠️ License

MIT — For **authorized security testing only**.