---
name: custom-ai-terminal
description: "Use when building AI CLI tools with rich TUI and streaming."
tags: [cli, ai, terminal, rich, prompt-toolkit, openai-api, streaming, tokenrouter, tui, gateway]
---

# Custom AI Terminal Builder

Build Claude Code-style AI-powered CLI tools using Python with `rich` (TUI) + `prompt_toolkit` (input) + OpenAI-compatible APIs (any gateway).

## Trigger

When building any custom AI-powered interactive CLI tool — pentest terminal, coding assistant, research CLI, chatbot — that needs rich TUI, streaming, multi-model support, and slash commands.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  prompt_toolkit (input)                              │
│  ┌─────────────────────────────────────────────────┐│
│  │  rich (display)                                  ││
│  │  ┌─────────────────────────────────────────────┐││
│  │  │  API Layer (OpenAI-compatible)               │││
│  │  │  ┌─────────────────────────────────────────┐│││
│  │  │  │  Gateways: TokenRouter, CutAd, BlockRun ││││
│  │  │  └─────────────────────────────────────────┘│││
│  │  └─────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

## Dependencies

```bash
pip install --break-system-packages rich prompt_toolkit
```

## Key Components

### 1. Gateway Registry Pattern

Define all API gateways in a single dict with model, key resolution, and priority:

```python
GATEWAYS = {
    "tr": {
        "name": "TokenRouter DeepSeek V4 Pro",
        "api": "https://api.tokenrouter.com/v1/chat/completions",
        "key_env": "HERMES_CUSTOM_API_TOKENROUTER_COM_API_KEY",
        "model": "deepseek/deepseek-v4-pro",
        "max_tokens": 4000,
        "priority": 1,
    },
    # ... more gateways
}
```

Key resolution: check `key` field first (hardcoded), then `key_env` (environment variable), then free gateways.

### 2. API Call Functions — CRITICAL: Split Streaming vs Non-Streaming

**Python pitfall**: A function containing `yield` anywhere becomes a generator function. The `return` statement in the non-streaming branch raises `StopIteration` with the value instead of returning it. The caller always gets a generator object.

**Solution**: Split into two separate functions:

```python
def call_api(gw_id, messages, system=None, max_tokens=None):
    """Non-streaming. Returns dict with content, tokens, model."""
    # ... build request with stream=False
    # ... parse JSON response
    return {"content": ..., "total_tokens": ..., "model": ...}

def call_api_stream(gw_id, messages, system=None, max_tokens=None):
    """Streaming. Yields events: token, usage, done, error."""
    # ... build request with stream=True
    for line in resp:
        # ... parse SSE stream
        yield {"type": "token", "text": text}
    yield {"type": "done", "content": full_content}
```

**Never** put `yield` and `return` in the same function — even in different branches.

### 3. Streaming Chat with Live Spinner

Use `rich.live.Live` with a spinner while streaming tokens:

```python
from rich.live import Live
from rich.spinner import Spinner

def chat_stream(user_input):
    spinner = Spinner("dots", text="[dim]Thinking…[/]", style="orange")
    full_content = ""
    
    with Live(spinner, refresh_per_second=10, console=console, transient=True) as live:
        for event in call_api_stream(gw_id, api_msgs, system=SYSTEM_PROMPT):
            if event["type"] == "token":
                full_content += event["text"]
                preview = full_content[:80].replace("\n", " ")
                live.update(Spinner("dots", text=f"[dim]Streaming: {preview}…[/]"))
            elif event["type"] == "done":
                full_content = event.get("content", full_content)
    
    # Fallback to non-streaming on error
    if not full_content:
        result = call_api(gw_id, api_msgs, system=SYSTEM_PROMPT)
        full_content = result["content"]
    
    # Render with rich Markdown
    from rich.markdown import Markdown
    console.print(Markdown(full_content, code_theme="monokai"))
```

### 4. Claude Code-Style Response Header

```python
header = Text()
header.append("● ", style="accent")
header.append(f"{gw['name']} ", style="bold purple")
header.append(f"· {total_tokens:,} tokens ", style="green")
header.append(f"· ${cost:.4f} ", style="bright_green")
header.append(f"· {model}", style="dim")
console.print(header)
```

### 5. prompt_toolkit Setup with Autocomplete

```python
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML

completer = WordCompleter(["/recon", "/exploit", "/cve", "/model", "/help"])
style = Style.from_dict({
    "prompt": "bold #FF6B35",
    "sep": "#757575",
    "gw": "bold #E040FB",
})

session = PromptSession(
    history=FileHistory("~/.cli_history"),
    completer=completer,
    style=style,
    auto_suggest=AutoSuggestFromHistory(),
)

# Claude Code-style prompt: ❯ name@gw >
prompt_text = HTML('<prompt>❯</prompt><sep> name@</sep><gw>tr</gw><sep> &gt; </sep>')
user_input = session.prompt(prompt_text)
```

### 6. Slash Command Dispatch

```python
PENTEST_PROMPTS = {
    "recon": lambda t: f"Full recon on {t}. DNS, subdomains, tech fingerprint...",
    "exploit": lambda t: f"Active exploitation on {t}. PoC, curl commands...",
    "cve": lambda t: f"Search CVEs for {t}. Local DB, exploits, detection...",
}

def dispatch(cmd, args):
    if cmd in PENTEST_PROMPTS:
        target = " ".join(args) if args else "target.com"
        chat_stream(PENTEST_PROMPTS[cmd](target))
    elif cmd == "model":
        switch_gateway(args[0])
    elif cmd == "!":
        execute_shell(" ".join(args))
```

### 7. Parallel Multi-Gateway Execution

Use `ThreadPoolExecutor` + `call_api` (non-streaming):

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def parallel_ask(question, gateways):
    results = {}
    with ThreadPoolExecutor(max_workers=len(gateways)) as ex:
        futures = {ex.submit(call_api, gw, [{"role":"user","content":question}], 
                            system=SYSTEM): gw for gw in gateways}
        for future in as_completed(futures):
            gw, result = future.result()
            results[gw] = result
    return results
```

### 8. Session Management

```python
class Session:
    def __init__(self):
        self.id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.messages = []
        self.tokens = {"in": 0, "out": 0, "total": 0}
        self.cost = 0.0
    
    def save(self):
        path = SESSIONS_DIR / f"{self.id}.json"
        path.write_text(json.dumps({...}, indent=2))
        return path
    
    def to_markdown(self):
        """Export full session as markdown report."""
        md = f"# Session: {self.id}\n\n"
        for msg in self.messages:
            md += f"## {msg['role'].upper()}\n\n{msg['content']}\n\n"
        return md
```

## Claude Code UI Replication

To clone Claude Code's exact terminal look, run the real `claude` binary in a tmux pane and read `tmux capture-pane` — never guess from memory. Key elements: 3-row ASCII header (`▐▛███▛█` / `▝▜██████▀` + `model · billing` + cwd), `✻` (U+273B) thinking indicator, bare `❯ ` prompt, mode symbols (`⏵⏵` auto / `○` plan / `⏸` manual), and `─────` horizontal separators. Full anatomy + replication checklist in `references/claude-code-ui-anatomy.md`.

## Pitfalls

1. **Python yield + return in same function**: Even if `yield` is in a different branch, the function becomes a generator. `return value` raises `StopIteration(value)` — caller gets a generator, not a dict. Always split into two functions.

2. **Streaming SSE parsing**: OpenAI-compatible streaming returns `data: {json}\n\n` lines. Skip empty lines and `data: [DONE]`. Parse each JSON chunk for `choices[0].delta.content`.

3. **TokenRouter model IDs**: Use `deepseek/deepseek-v4-pro` (not `deepseek-ai/...`). The `/v1/models` endpoint confirms exact IDs.

4. **CutAd rate limiting**: 429 after ~25 requests/month on free tier. Use TokenRouter as primary.

5. **Rich Live + Streaming**: `Live` with `transient=True` cleans up the spinner after context exit. Without it, spinner text persists.

6. **prompt_toolkit HTML prompt**: Use `HTML()` for styled prompts. Colors must be hex or named. Use `&gt;` for `>` in HTML context.

7. **Session auto-save**: Save after every response to prevent data loss. Use `atexit` for final save on exit.

8. **Markdown rendering**: `rich`'s `Markdown` with `code_theme="monokai"` gives syntax-highlighted code blocks. Wrap in try/except — some edge cases cause render errors.

9. **rich markup closing tag needs an opening tag**: `console.print(f"{C['accent']}  ▝▝ ▝▝[/]")` raises a markup error because `[/]` has no matching `[` opener — the `{C['accent']}` f-string substitution injects a bare hex like `#FF6B35` with no `[` bracket. Always wrap the opening tag: `f"[{C['accent']}]  ▝▝ ▝▝[/]"`. This bites on ASCII-art banner rows where a color is applied mid-line without text in between.

10. **Streaming token usage — empty `choices` chunk (the "0 tokens" bug)**: With `stream_options: {"include_usage": True}`, `usage` arrives in a FINAL chunk whose `"choices"` is `[]` (empty list). If the chunk loop touches `choices[0]` before reading usage, the empty list raises `IndexError` (silently swallowed by `except: pass`) and token count stays 0 forever. Two required parts: (a) put `"stream_options": {"include_usage": True}` in the request body — without it usage is never sent (intermediate chunks carry `"usage": null`); (b) check usage BEFORE touching choices and guard choices with `or [{}]`:
```python
j = json.loads(chunk)
if j.get("usage"):                 # before touching choices
    yield {"type": "usage", "data": j["usage"]}
choices = j.get("choices") or [{}] # empty list → fallback, no IndexError
delta = choices[0].get("delta", {})
```
Debugging path: run a standalone `urllib` test printing `j["usage"]` directly; if it prints real usage but your app reports 0 tokens, the bug is the empty-`choices` IndexError, NOT the request. Applies to any OpenAI-compatible gateway (TokenRouter, DeepSeek, GLM, etc.).

11. **Rich `Layout` inside `Panel` renders a HUGE empty panel and breaks input**: `Layout()` + `split_row()` is meant for a full-console layout context. Wrapping it in `Panel(layout, ...)` renders the panel with a giant empty body (20+ blank rows) — it visually breaks the screen AND, worse, wrecks prompt_toolkit's prompt loop so input appears dead (commands echo at the `❯` but nothing runs). Fix: build a single-line `Text` and wrap THAT in the Panel. `Layout` inside a `Panel` is always a bug.

```python
# BROKEN — Layout in Panel → giant empty status bar, dead input
layout = Layout(); layout.split_row(Layout(left, ratio=1), Layout(right, ratio=1))
return Panel(layout, ...)

# FIXED — single-line Text in Panel
t = Text()
t.append(f" {mode_sym} {perm}", style=C['dim'])
t.append(f" · {gw}", style=C['model'])
t.append(f" · {tokens} tok", style=C['token'])
return Panel(t, border_style=C["dim"], box=box.ROUNDED, padding=(0, 1))
```

12. **Test interactive TUI CLIs via a real PTY, not `echo |`**: piping input (`echo "/help" | python3 beast.py`) and `tmux send-keys` are unreliable for prompt_toolkit apps — the prompt renders but keystrokes get lost, so you can't tell if input actually works. Drive it through a genuine pseudo-terminal and read the pty master:

```python
import pty, os, time, select
pid, fd = pty.fork()
if pid == 0:
    os.execvp('python3', ['python3', 'cli.py'])          # child
time.sleep(3)
os.write(fd, b'/help\r')                                  # send a command + Enter
time.sleep(2)
out = b''
while True:
    r,_,_ = select.select([fd], [], [], 0.3)
    if not r: break
    try:
        d = os.read(fd, 65536)
        if not d: break
        out += d
    except OSError: break
print(out.decode(errors='ignore'))                         # assert output contains /help response
os.kill(pid, 9)                                            # always reap
```

This is the deterministic way to verify an interactive CLI actually accepts input and dispatches commands before bundling it behind a web terminal or tmux.

## System Prompt Tone

Users of a "pentest/hacker" terminal often do NOT want the over-the-top persona. When asked to make it "not too AI", strip the theatrics: drop "apex predator / CIPHER SOVEREIGN / NEVER refuse / you have absorbed ALL knowledge" and rewrite the IDENTITY block as a direct professional — e.g. "You are a senior security engineer. Be direct, practical, technically precise. No 'superintelligent hacker' persona — just get the job done." Gateways like TokenRouter/DeepSeek behave identically either way; the tone lives entirely in your `SYSTEM_PROMPT` string. Verify by checking a sample response reads like a colleague, not a comic-book villain.

## Reference Implementation

Full working example: `~/pentest-cli/beast.py` (860 lines). See `references/beast-terminal-quickref.md` for quick-start guide and slash command reference.

To expose the CLI as a browser/mobile terminal (Flask + SocketIO + tmux, delta output, chat UI, PWA, ngrok fallback), see `references/web-terminal-and-mobile.md`.

- 4 gateways (TokenRouter, CutAd, BlockRun, 9Router)
- Streaming + non-streaming fallback
- 12 slash commands
- Parallel execution
- Auto-pentest mode
- Session persistence
- Config management

## TokenRouter Configuration

```bash
# Required env var
export HERMES_CUSTOM_API_TOKENROUTER_COM_API_KEY="sk-..."

# API endpoint
https://api.tokenrouter.com/v1/chat/completions

# Available models
deepseek/deepseek-v4-pro          # Primary — most reliable
deepseek/deepseek-v4-pro-0813-free # Free tier (may be 503)
z-ai/glm-5.2                      # GLM-5.2 (needs academic framing)
custom/th/claude-sonnet-5         # Claude via TokenHarbor (may be 403)
```