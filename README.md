# BEAST Terminal 🔥

**Multi-Gateway AI Pentest CLI** — Claude Code-style terminal untuk penetration testing, exploit development, dan vulnerability research.

Powered by **TokenRouter DeepSeek V4 Pro** · GLM-5.2 · BlockRun Nemotron 120B

## Quick Start

```bash
# Install
git clone https://github.com/andri1404/beast-terminal.git
cd beast-terminal
pip install --break-system-packages rich prompt_toolkit

# Run
python3 beast.py                    # Interactive mode
python3 beast.py "recon target.com" # One-shot
python3 beast.py -l                 # List gateways
python3 beast.py --probe            # Test all gateways
python3 beast.py --auto target.com  # Autonomous pentest
python3 beast.py --parallel "query" # Ask all gateways

# Symlink to PATH
sudo ln -sf $(pwd)/beast /usr/local/bin/beast
beast
```

## Features

- 🔴 **Streaming** — Real-time token output
- ⚡ **Parallel** — Ask 3+ gateways simultaneously
- 🤖 **Auto Pentest** — Recon → Vuln → Exploit → Report
- 💾 **Session** — Auto-save, resume, export
- 🎨 **Rich TUI** — Claude Code-style terminal UI
- 🔧 **Config** — Toggle streaming, autosave
- 🛠️ **Shell** — Execute commands directly

## Slash Commands

```
/recon <target>      /exploit <target>    /cve <software>
/bypass <target>     /chain <target>      /auto <target>
/sqlmap <url>        /fuzz <endpoint>     /parallel <q>
/model <id>          /gateways            /probe
/status              /clear               /save
/export              /config              /system
/! <cmd>             /help
```

## Gateways

| ID | Gateway | Model | Status |
|----|---------|-------|--------|
| `tr` | TokenRouter | DeepSeek V4 Pro | ✅ Primary |
| `tr-glm` | TokenRouter | GLM-5.2 | ✅ |
| `tr-free` | TokenRouter | DSv4Pro Free | ⚠️ |
| `blockrun` | BlockRun | Nemotron 120B | ✅ Free |

## Requirements

- Python 3.10+
- `rich` — Terminal UI
- `prompt_toolkit` — Interactive input
- TokenRouter API key (env: `HERMES_CUSTOM_API_TOKENROUTER_COM_API_KEY`)

## License

MIT — For authorized security testing only.