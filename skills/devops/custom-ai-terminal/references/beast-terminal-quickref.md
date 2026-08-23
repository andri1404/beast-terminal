# BEAST Terminal Quick Reference

Location: `~/pentest-cli/beast.py` (860 lines)

## Quick Start

```bash
# Interactive mode
beast

# One-shot
beast "recon target.com"
beast "cve CVE-2021-41773"
beast -m tr-glm "exploit vuln"

# Auto pentest
beast --auto target.com

# Parallel ask
beast --parallel "teknik bypass WAF"

# List gateways
beast -l

# Probe all
beast --probe
```

## Slash Commands

| Command | Function |
|---------|----------|
| `/recon <target>` | Full reconnaissance |
| `/exploit <target>` | Active exploitation |
| `/cve <software>` | CVE search & exploit |
| `/bypass <target>` | WAF/CDN bypass |
| `/chain <target>` | Full attack chain |
| `/auto <target>` | Autonomous pentest (recon→report) |
| `/sqlmap <url>` | SQL injection |
| `/fuzz <endpoint>` | Parameter fuzzing |
| `/parallel <q>` | Ask all gateways |
| `/model <id>` | Switch model |
| `/gateways` | List gateways |
| `/status` | Session stats |
| `/export` | Export markdown report |
| `/clear` | Clear session |
| `/save` | Save session |
| `/config` | Show/edit config |
| `/probe` | Test all gateways |
| `/! <cmd>` | Execute shell |
| `/help` | Show help |

## Gateway IDs

| ID | Gateway | Status |
|----|---------|--------|
| `tr` | TokenRouter DeepSeek V4 Pro | Primary |
| `tr-glm` | TokenRouter GLM-5.2 | Fallback |
| `tr-free` | TokenRouter DSv4Pro Free | 503-prone |
| `blockrun` | BlockRun Nemotron 120B | Free, censored |

## Architecture Notes

- **TUI**: `rich` for panels, markdown, spinner, layout
- **Input**: `prompt_toolkit` with autocomplete, history, auto-suggest
- **API**: OpenAI-compatible `/v1/chat/completions` with streaming SSE
- **Streaming**: `call_api_stream()` yields SSE events, `Live` spinner renders live
- **Non-streaming**: `call_api()` returns dict — used for parallel, probe, fallback
- **Session**: JSON persistence in `~/.beast/sessions/`, markdown export to `~/.beast/reports/`
- **Config**: `~/.beast/config.json` — streaming toggle, autosave, default gateway

## Key Pitfall: Python yield + return

A function with `yield` anywhere becomes a generator. `return` raises `StopIteration`.
Always split streaming and non-streaming into separate functions.