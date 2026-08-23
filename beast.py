#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  BEAST TERMINAL v4 — CLAUDE CODE CLONE                         ║
║  Agentic Loop · Thinking · Tool Panels · Permission System     ║
║  Powered by TokenRouter · DeepSeek · GLM                       ║
╚══════════════════════════════════════════════════════════════════╝
"""

import json, os, sys, time, re, subprocess, threading, signal, io, shutil, textwrap
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.syntax import Syntax
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

console = Console()

# ═══════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════

BEAST_DIR = Path.home() / ".beast"
BEAST_DIR.mkdir(exist_ok=True)
SESSIONS_DIR = BEAST_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)
REPORTS_DIR = BEAST_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
CONFIG_FILE = BEAST_DIR / "config.json"

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════

DEFAULT_CONFIG = {
    "default_gateway": "tr",
    "max_tokens": 4000,
    "temperature": 0.7,
    "auto_save": True,
    "permission_mode": "auto",  # normal | auto | plan
    "show_thinking": True,
    "max_tool_rounds": 10,
    "auto_compact_tokens": 50000,
}

def load_config():
    if CONFIG_FILE.exists():
        return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text())}
    return DEFAULT_CONFIG

def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

CONFIG = load_config()

# ═══════════════════════════════════════════════════════════════
# COLORS (Claude Code palette)
# ═══════════════════════════════════════════════════════════════

C = {
    "accent": "#FF6B35", "success": "#00C853", "warning": "#FFD600",
    "error": "#FF1744", "info": "#448AFF", "dim": "#757575",
    "model": "#E040FB", "tool": "#00BCD4", "token": "#69F0AE",
    "white": "#FFFFFF", "think": "#546E7A",
}

# ═══════════════════════════════════════════════════════════════
# GATEWAYS
# ═══════════════════════════════════════════════════════════════

GATEWAYS = {
    "tr": {
        "name": "TokenRouter DeepSeek V4 Pro",
        "api": "https://api.tokenrouter.com/v1/chat/completions",
        "key_env": "HERMES_CUSTOM_API_TOKENROUTER_COM_API_KEY",
        "model": "deepseek/deepseek-v4-pro", "max_tokens": 4000,
        "supports_reasoning": True, "supports_streaming": True,
        "tags": "deepseek", "priority": 1,
    },
    "tr-glm": {
        "name": "TokenRouter GLM-5.2",
        "api": "https://api.tokenrouter.com/v1/chat/completions",
        "key_env": "HERMES_CUSTOM_API_TOKENROUTER_COM_API_KEY",
        "model": "z-ai/glm-5.2", "max_tokens": 4000,
        "supports_reasoning": False, "supports_streaming": True,
        "tags": "glm", "priority": 2,
    },
    "tr-free": {
        "name": "TokenRouter DSv4Pro Free",
        "api": "https://api.tokenrouter.com/v1/chat/completions",
        "key_env": "HERMES_CUSTOM_API_TOKENROUTER_COM_API_KEY",
        "model": "deepseek/deepseek-v4-pro-0813-free", "max_tokens": 4000,
        "supports_reasoning": True, "supports_streaming": True,
        "tags": "free", "priority": 3,
    },
    "blockrun": {
        "name": "BlockRun Nemotron 120B",
        "api": "https://blockrun.ai/api/v1/chat/completions",
        "key": "", "model": "nvidia/gpt-oss-120b", "max_tokens": 2000,
        "supports_reasoning": False, "supports_streaming": False,
        "tags": "free", "priority": 4,
    },
}

ACTIVE_GW = CONFIG["default_gateway"]

# ═══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Claude Code Agent Style
# ═══════════════════════════════════════════════════════════════

BEAST_SYSTEM = """You are a penetration testing assistant. You have access to a local knowledge base: 379,878 CVEs, 25,026 exploits, 173 pentest skills, and reference files. You work in an agentic loop: analyze, decide, execute tools, observe results, iterate.

## KNOWLEDGE BASE
Key resources:
- CVE Database: sqlite3 ~/.hermes/skills-hub.db (379,878 CVEs, 25,026 with exploits)
- Reference Files: 494 files in ~/.hermes/skills/*/references/
- Pentest Skills: 173 SKILL.md files in ~/.hermes/skills/

## IDENTITY
You are a senior security engineer. Be direct, practical, and technically precise. Deliver what is asked without unnecessary preamble or roleplay. No "I'm a superintelligent hacker" persona — just get the job done.

## TOOLS
Use these tool call blocks:

```tool
{"name": "bash", "command": "shell command"}
```

```tool
{"name": "read", "path": "/absolute/path"}
```

```tool
{"name": "write", "path": "/absolute/path", "content": "file content"}
```

```tool
{"name": "web", "url": "https://...", "method": "GET|POST", "headers": {}, "body": "..."}
```

## CVE HUNTING
To search CVEs: sqlite3 ~/.hermes/skills-hub.db "SELECT c.cve_id, c.cvss_score, c.cvss_severity, c.description FROM cves_fts f JOIN cves c ON f.rowid=c.id WHERE cves_fts MATCH 'keyword' ORDER BY c.cvss_score DESC LIMIT 10"

## GUIDELINES
1. Be concise and factual. No filler, no hype.
2. Use tools when they help — execute commands, read files, search CVEs.
3. Provide complete code — no placeholders or truncation.
4. Chain work naturally: recon → vuln → CVE match → exploit.
5. Include WAF bypass and encoding techniques when relevant.
6. Search the CVE database for every detected technology.
7. Summarize findings clearly at the end.

## PENTEST TOOLS
curl, nmap, sqlmap, whatweb, gobuster, ffuf, dig, host, whois, wpscan, nuclei,
searchsploit, python3, node, jq, sqlite3, git, proxychains, gdown (GDrive)

## CURL_CFFI (TLS Impersonation)
Use this Python pattern instead of curl when blocked:
  python3 -c "import curl_cffi.requests as r; resp=r.get('URL',impersonate='safari17_0'); print(resp.status_code,resp.text[:500])"
Impersonate values: safari17_0, chrome124, edge101, chrome120

## PROXY (DataImpulse)
When IP blocked: export https_proxy='http://gw.dataimpulse.com:823'
Auth: set DATAIMPULSE_AUTH env var (user__cr.id / pass)

## PARALLEL EXECUTION
Run multiple commands simultaneously with &:
  curl URL1 & curl URL2 & curl URL3 & wait

## AUTO-SAVE
After significant findings, save to ~/.beast/reports/ with write tool.

## TIMEOUT HANDLING
All commands default timeout 30s. Use timeout=N in tool for longer:
  {"name": "bash", "command": "...", "timeout": 60}"""

# ═══════════════════════════════════════════════════════════════
# SESSION
# ═══════════════════════════════════════════════════════════════

class Session:
    def __init__(self):
        self.id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.messages = []
        self.tokens = {"in": 0, "out": 0, "total": 0}
        self.cost = 0.0
        self.start = datetime.now()
        self.gateway = ACTIVE_GW
        self.commands = []
        self.tool_rounds = 0
        self.per_model_tokens = {}
        self.token_history = []
        self.budget_limit = None
    
    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content, "time": datetime.now().isoformat()})
    
    def add_tokens(self, in_tok, out_tok, model=None):
        self.tokens["in"] += in_tok
        self.tokens["out"] += out_tok
        self.tokens["total"] += in_tok + out_tok
        cost = (in_tok * 0.50 + out_tok * 2.00) / 1_000_000
        self.cost += cost
        if model:
            if model not in self.per_model_tokens:
                self.per_model_tokens[model] = {"in": 0, "out": 0, "total": 0, "cost": 0.0}
            self.per_model_tokens[model]["in"] += in_tok
            self.per_model_tokens[model]["out"] += out_tok
            self.per_model_tokens[model]["total"] += in_tok + out_tok
            self.per_model_tokens[model]["cost"] += cost
        self.token_history.append({
            "time": datetime.now().isoformat(),
            "in": in_tok, "out": out_tok, "cost": cost,
            "model": model or "unknown",
        })
    
    def save(self):
        path = SESSIONS_DIR / f"{self.id}.json"
        path.write_text(json.dumps({
            "id": self.id, "gateway": self.gateway,
            "tokens": self.tokens, "cost": self.cost,
            "start": self.start.isoformat(), "commands": self.commands,
            "messages": self.messages,
        }, indent=2))
        return path
    
    def to_markdown(self):
        md = f"# BEAST Session: {self.id}\n\n"
        md += f"**Gateway:** {GATEWAYS[self.gateway]['name']}\n"
        md += f"**Tokens:** {self.tokens['total']:,} | **Cost:** ${self.cost:.4f}\n"
        md += f"**Duration:** {datetime.now() - self.start}\n\n---\n\n"
        for msg in self.messages:
            md += f"## {msg['role'].upper()}\n\n{msg['content']}\n\n---\n\n"
        return md

SESSION = Session()

# ═══════════════════════════════════════════════════════════════
# API
# ═══════════════════════════════════════════════════════════════

def get_api_key(gw_id):
    gw = GATEWAYS[gw_id]
    if "key" in gw and gw["key"]:
        return gw["key"]
    return os.environ.get(gw.get("key_env", ""), "")

def call_api(gw_id, messages, system=None, max_tokens=None):
    """Non-streaming API call."""
    gw = GATEWAYS[gw_id]
    api_key = get_api_key(gw_id)
    if not api_key and gw_id != "blockrun":
        return {"error": f"No API key"}
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    full_msgs = []
    if system:
        full_msgs.append({"role": "system", "content": system})
    full_msgs.extend(messages)
    
    body = {
        "model": gw["model"], "messages": full_msgs,
        "max_tokens": max_tokens or gw.get("max_tokens", 2000),
        "temperature": CONFIG["temperature"], "stream": False,
    }
    
    try:
        req = Request(gw["api"], data=json.dumps(body).encode(), headers=headers)
        with urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode())
            choice = result.get("choices", [{}])[0]
            msg = choice.get("message", {})
            return {
                "content": msg.get("content", ""),
                "reasoning": msg.get("reasoning_content", ""),
                "finish_reason": choice.get("finish_reason", "unknown"),
                "prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": result.get("usage", {}).get("completion_tokens", 0),
                "total_tokens": result.get("usage", {}).get("total_tokens", 0),
                "model": result.get("model", gw["model"]),
            }
    except Exception as e:
        return {"error": str(e)}

def call_api_stream(gw_id, messages, system=None, max_tokens=None):
    """Streaming API call. Yields: {'type':'token'|'reasoning'|'usage'|'done'|'error', ...}"""
    gw = GATEWAYS[gw_id]
    api_key = get_api_key(gw_id)
    if not api_key and gw_id != "blockrun":
        yield {"type": "error", "error": "No API key"}
        return
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    full_msgs = []
    if system:
        full_msgs.append({"role": "system", "content": system})
    full_msgs.extend(messages)
    
    body = {
        "model": gw["model"], "messages": full_msgs,
        "max_tokens": max_tokens or gw.get("max_tokens", 2000),
        "temperature": CONFIG["temperature"], "stream": True,
        "stream_options": {"include_usage": True},
    }
    
    try:
        req = Request(gw["api"], data=json.dumps(body).encode(), headers=headers)
        with urlopen(req, timeout=180) as resp:
            content = ""
            reasoning = ""
            for line in resp:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        break
                    try:
                        j = json.loads(chunk)
                        # Check usage first — usage chunk has empty choices []
                        if j.get("usage"):
                            yield {"type": "usage", "data": j["usage"]}
                        choices = j.get("choices") or [{}]
                        delta = choices[0].get("delta", {})
                        text = delta.get("content", "")
                        rtext = delta.get("reasoning_content", "")
                        if rtext:
                            reasoning += rtext
                            yield {"type": "reasoning", "text": rtext}
                        if text:
                            content += text
                            yield {"type": "token", "text": text}
                    except:
                        pass
            yield {"type": "done", "content": content, "reasoning": reasoning}
    except Exception as e:
        yield {"type": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════════
# TOOL EXECUTION ENGINE
# ═══════════════════════════════════════════════════════════════

def execute_tool(tool_name, params):
    """Execute a tool and return the result."""
    try:
        if tool_name == "bash":
            cmd = params.get("command", "")
            timeout = params.get("timeout", 30)
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            output = (result.stdout or "") + (result.stderr or "")
            return {
                "exit_code": result.returncode,
                "output": output[:5000],
                "truncated": len(output) > 5000,
            }
        elif tool_name == "read":
            path = params.get("path", "")
            limit = params.get("limit", 200)
            try:
                content = Path(path).read_text()[:limit * 200]
                return {"content": content, "lines": len(content.splitlines())}
            except Exception as e:
                return {"error": str(e)}
        elif tool_name == "write":
            path = params.get("path", "")
            content = params.get("content", "")
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(content)
            return {"written": len(content), "path": path}
        elif tool_name == "web":
            url = params.get("url", "")
            method = params.get("method", "GET").upper()
            headers = params.get("headers", {})
            body = params.get("body", "")
            data = body.encode() if body else None
            req = Request(url, data=data, headers=headers, method=method)
            with urlopen(req, timeout=30) as resp:
                content = resp.read().decode("utf-8", errors="replace")[:5000]
                return {"status": resp.status, "headers": dict(resp.headers), "body": content}
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        return {"error": str(e)}

def parse_tool_calls(content):
    """Parse tool call blocks from AI response."""
    pattern = r'```tool\s*\n(.*?)\n```'
    matches = re.findall(pattern, content, re.DOTALL)
    tools = []
    for m in matches:
        try:
            tools.append(json.loads(m.strip()))
        except:
            pass
    return tools

# ═══════════════════════════════════════════════════════════════
# PERMISSION SYSTEM (Claude Code-style)
# ═══════════════════════════════════════════════════════════════

def permission_check(tool_name, params):
    """Check if a tool call should be allowed."""
    mode = CONFIG["permission_mode"]
    
    if mode == "auto":
        return True
    
    if mode == "plan":
        # In plan mode, only allow read operations
        return tool_name in ("read", "web")
    
    # Normal mode — show tool details and ask
    if tool_name == "bash":
        cmd = params.get("command", "")
        console.print(Panel(
            f"[{C['tool']}]$ {cmd}[/]",
            title=f"[{C['warning']}]⏳ Bash Command[/]",
            border_style=C["warning"], box=box.ROUNDED,
        ))
    elif tool_name == "write":
        path = params.get("path", "")
        console.print(Panel(
            f"[{C['dim']}]Write to: {path}[/]",
            title=f"[{C['warning']}]⏳ File Write[/]",
            border_style=C["warning"], box=box.ROUNDED,
        ))
    
    # Auto-approve for now
    return True

def show_tool_panel(tool_name, params, result, status="running"):
    """Show a Claude Code-style tool execution panel."""
    status_icons = {"running": "⏳", "done": "✓", "error": "✗"}
    status_colors = {"running": C["tool"], "done": C["success"], "error": C["error"]}
    
    icon = status_icons.get(status, "●")
    color = status_colors.get(status, C["tool"])
    
    if tool_name == "bash":
        cmd = params.get("command", "")[:200]
        output = result.get("output", "")[:800] if result else ""
        exit_code = result.get("exit_code", "?") if result else "?"
        
        panel_content = f"[{C['dim']}]$ {cmd}[/]\n"
        if output:
            panel_content += f"\n[{C['dim']}]{output}[/]"
        panel_content += f"\n\n[{C['dim']}]Exit: {exit_code}[/]"
        
        console.print(Panel(
            panel_content,
            title=f"[{color}]{icon} Bash[/]",
            border_style=color, box=box.ROUNDED, padding=(0, 1),
        ))
    
    elif tool_name == "read":
        path = params.get("path", "")
        lines = result.get("lines", 0) if result else 0
        console.print(Panel(
            f"[{C['dim']}]{path} ({lines} lines)[/]",
            title=f"[{color}]{icon} Read[/]",
            border_style=color, box=box.ROUNDED, padding=(0, 1),
        ))
    
    elif tool_name == "write":
        path = params.get("path", "")
        written = result.get("written", 0) if result else 0
        console.print(Panel(
            f"[{C['dim']}]{path} ({written} bytes)[/]",
            title=f"[{color}]{icon} Write[/]",
            border_style=color, box=box.ROUNDED, padding=(0, 1),
        ))
    
    elif tool_name == "web":
        url = params.get("url", "")[:80]
        status_code = result.get("status", "?") if result else "?"
        console.print(Panel(
            f"[{C['dim']}]{params.get('method', 'GET')} {url} → {status_code}[/]",
            title=f"[{color}]{icon} Web[/]",
            border_style=color, box=box.ROUNDED, padding=(0, 1),
        ))

# ═══════════════════════════════════════════════════════════════
# AGENTIC LOOP (Claude Code-style)
# ═══════════════════════════════════════════════════════════════

def agentic_loop(user_input):
    """Run the agentic loop: AI thinks → uses tools → observes → iterates."""
    gw = GATEWAYS[ACTIVE_GW]
    SESSION.add_message("user", user_input)
    SESSION.commands.append(user_input)
    SESSION.tool_rounds = 0
    
    max_rounds = CONFIG["max_tool_rounds"]
    
    console.print()
    
    for round_num in range(max_rounds):
        SESSION.tool_rounds = round_num + 1
        
        # Build context (last 20 messages)
        context = SESSION.messages[-20:] if len(SESSION.messages) > 20 else SESSION.messages
        api_msgs = [{"role": m["role"], "content": m["content"]} for m in context]
        
        # Streaming with thinking
        full_content = ""
        full_reasoning = ""
        thinking_shown = False
        
        if gw.get("supports_streaming", True):
            # Show thinking spinner
            spinner = Spinner("dots", text=f"[dim]BEAST is thinking…[/]", style=C["accent"])
            
            with Live(spinner, refresh_per_second=10, console=console, transient=True) as live:
                try:
                    for event in call_api_stream(ACTIVE_GW, api_msgs, system=get_effective_system_prompt()):
                        if event["type"] == "reasoning":
                            full_reasoning += event["text"]
                            if CONFIG["show_thinking"] and not thinking_shown:
                                thinking_shown = True
                                live.update(Text(f"[{C['think']}]✻ {full_reasoning[-200:]}[/]"))
                        elif event["type"] == "token":
                            full_content += event["text"]
                            preview = full_content[:60].replace("\n", " ")
                            live.update(Spinner("dots", text=f"[dim]Generating: {preview}…[/]", style=C["accent"]))
                        elif event["type"] == "usage" and event.get("data"):
                            SESSION.add_tokens(
                                event["data"].get("prompt_tokens", 0),
                                event["data"].get("completion_tokens", 0),
                                model=gw.get("model", "unknown"),
                            )
                        elif event["type"] == "done":
                            full_content = event.get("content", full_content)
                            full_reasoning = event.get("reasoning", full_reasoning)
                        elif event["type"] == "error":
                            raise Exception(event["error"])
                except Exception as e:
                    console.print(f"[{C['error']}]Stream error: {e}, falling back…[/]")
                    result = call_api(ACTIVE_GW, api_msgs, system=get_effective_system_prompt())
                    if "error" not in result:
                        full_content = result["content"]
                        full_reasoning = result.get("reasoning", "")
                        SESSION.add_tokens(result.get("prompt_tokens", 0), result.get("completion_tokens", 0), model=result.get("model", "unknown"))
        else:
            result = call_api(ACTIVE_GW, api_msgs, system=get_effective_system_prompt())
            if "error" in result:
                console.print(f"[{C['error']}]API Error: {result['error']}[/]")
                return
            full_content = result["content"]
            full_reasoning = result.get("reasoning", "")
            SESSION.add_tokens(result.get("prompt_tokens", 0), result.get("completion_tokens", 0), model=result.get("model", "unknown"))
        
        if not full_content:
            console.print(f"[{C['error']}]Empty response[/]")
            return
        
        SESSION.add_message("assistant", full_content)
        
        # Show thinking (Claude Code-style collapsed thinking)
        if full_reasoning and CONFIG["show_thinking"]:
            console.print(Panel(
                full_reasoning[-500:] if len(full_reasoning) > 500 else full_reasoning,
                title=f"[{C['think']}]✻ Thinking[/]",
                border_style=C["think"], box=box.ROUNDED, padding=(0, 1),
            ))
        
        # Parse tool calls
        tool_calls = parse_tool_calls(full_content)
        
        if not tool_calls:
            # No tool calls — final response
            console.print()
            header = Text()
            header.append("✻ ", style=C["accent"])
            header.append(f"{gw['name']} ", style=f"bold {C['model']}")
            header.append(f"· {SESSION.tokens['total']:,} tokens ", style=C['token'])
            header.append(f"· ${SESSION.cost:.4f} ", style=C['success'])
            console.print(header)
            console.print()
            
            # Clean content for display (remove tool blocks)
            display_content = re.sub(r'```tool\s*\n.*?\n```', '', full_content, flags=re.DOTALL).strip()
            if display_content:
                try:
                    console.print(Markdown(display_content, code_theme="monokai"))
                except:
                    console.print(display_content)
            
            console.print()
            console.print("─" * min(console.width, 100), style=C["dim"])
            
            if CONFIG["auto_save"]:
                SESSION.save()
            return
        
        # Execute tools
        for tool in tool_calls:
            tool_name = tool.get("name", "")
            params = {k: v for k, v in tool.items() if k != "name"}
            
            if not permission_check(tool_name, params):
                SESSION.add_message("tool", json.dumps({"error": "Permission denied"}))
                continue
            
            result = execute_tool(tool_name, params)
            show_tool_panel(tool_name, params, result, "done" if "error" not in result else "error")
            
            # Feed result back to conversation
            tool_result = f"Tool result for {tool_name}:\n```json\n{json.dumps(result, indent=2)}\n```"
            SESSION.add_message("tool", tool_result)
    
    # Max rounds reached
    console.print(f"[{C['warning']}]Max tool rounds ({max_rounds}) reached.[/]")

# ═══════════════════════════════════════════════════════════════
# COMMANDS
# ═══════════════════════════════════════════════════════════════

def cmd_help():
    console.print(Panel(
        f"[bold {C['accent']}]PENTEST[/]\n"
        f"[{C['tool']}]  /recon <t>[/]  Recon  [{C['tool']}]  /exploit <t>[/]  Exploit\n"
        f"[{C['tool']}]  /cve <s>[/]    CVE    [{C['tool']}]  /bypass <t>[/]   WAF bypass\n"
        f"[{C['tool']}]  /chain <t>[/]  Chain  [{C['tool']}]  /auto <t>[/]     Auto pentest\n"
        f"[{C['tool']}]  /sqlmap <u>[/] SQLi   [{C['tool']}]  /fuzz <e>[/]      Fuzz\n\n"
        f"[bold {C['model']}]SESSION[/]\n"
        f"[{C['tool']}]  /model <id>[/]   Switch model\n"
        f"[{C['tool']}]  /gateways[/]     List gateways\n"
        f"[{C['token']}]  /tokens[/]        Token breakdown per model\n"
        f"[{C['success']}]  /cost[/]          Cost breakdown with rates\n"
        f"[{C['warning']}]  /budget <$>[/]     Set spending limit\n"
        f"[{C['dim']}]  /history[/]       Command history with costs\n"
        f"[{C['tool']}]  /permission <m>[/] Permission mode (normal/auto/plan)\n"
        f"[{C['tool']}]  /thinking[/]      Toggle thinking display\n"
        f"[{C['tool']}]  /compact[/]       Compress context\n"
        f"[{C['tool']}]  /clear[/]         New session\n"
        f"[{C['tool']}]  /save[/]          Save session\n"
        f"[{C['tool']}]  /export[/]        Export report\n"
        f"[{C['tool']}]  /report[/]        Auto-save findings\n"
        f"[{C['tool']}]  /status[/]        Session stats\n"
        f"[{C['tool']}]  /probe[/]         Test gateways\n"
        f"[{C['tool']}]  /! <cmd>[/]       Shell command\n"
        f"[{C['tool']}]  /help[/]          This help\n"
        f"[{C['tool']}]  /exit[/]          Quit\n",
        title="[bold]BEAST v4[/]", border_style=C["accent"], box=box.HEAVY, padding=(1, 2),
    ))

def cmd_gateways():
    table = Table(box=box.ROUNDED, border_style=C["dim"])
    table.add_column("#", style=C["accent"], justify="right")
    table.add_column("ID", style=C["model"]); table.add_column("Gateway", style="bold")
    table.add_column("Model", style=C["dim"]); table.add_column("Status")
    for i, (gw_id, gw) in enumerate(sorted(GATEWAYS.items(), key=lambda x: x[1].get("priority", 99)), 1):
        marker = "▶" if gw_id == ACTIVE_GW else " "
        key = get_api_key(gw_id)
        status = f"[{C['success']}]✓[/]" if key else f"[{C['warning']}]FREE[/]" if gw_id == "blockrun" else f"[{C['error']}]✗[/]"
        table.add_row(f"{i}", f"{marker}{gw_id}", gw["name"], gw["model"], status)
    console.print(table)

def cmd_model(args):
    global ACTIVE_GW
    ids = list(GATEWAYS.keys())
    if args:
        gw_id = args[0].lower()
        # Numeric selection: /model 2
        if gw_id.isdigit() and 1 <= int(gw_id) <= len(ids):
            gw_id = ids[int(gw_id) - 1]
        if gw_id in GATEWAYS:
            ACTIVE_GW = gw_id; SESSION.gateway = gw_id
            console.print(f"[{C['success']}]✓ Model → {GATEWAYS[gw_id]['name']} ({GATEWAYS[gw_id]['model']})[/]")
        else:
            console.print(f"[{C['error']}]Unknown: {gw_id}[/]")
            console.print(f"[{C['dim']}]Tersedia: {', '.join(ids)}[/]")
        return
    # No args → simple numbered list
    cmd_gateways()
    console.print(f"\n[{C['dim']}]Pilih: /model 1-{len(ids)}  atau /model <id>[/]")

def cmd_permission(args):
    if not args:
        console.print(f"[{C['model']}]Permission mode: {CONFIG['permission_mode']}[/]")
        return
    mode = args[0].lower()
    if mode in ("normal", "auto", "plan"):
        CONFIG["permission_mode"] = mode; save_config(CONFIG)
        console.print(f"[{C['success']}]✓ Permission: {mode}[/]")
    else:
        console.print(f"[{C['error']}]Invalid mode. Use: normal, auto, plan[/]")

def cmd_thinking():
    CONFIG["show_thinking"] = not CONFIG["show_thinking"]; save_config(CONFIG)
    console.print(f"[{C['success']}]Thinking: {'ON' if CONFIG['show_thinking'] else 'OFF'}[/]")

def cmd_compact():
    global SESSION
    if len(SESSION.messages) <= 10:
        console.print(f"[{C['dim']}]Context already compact ({len(SESSION.messages)} msgs)[/]")
        return
    SESSION.save()
    old_len = len(SESSION.messages)
    SESSION.messages = SESSION.messages[-6:]
    console.print(f"[{C['success']}]✓ Compacted: {old_len} → {len(SESSION.messages)} messages[/]")

def cmd_status():
    elapsed = datetime.now() - SESSION.start
    console.print(Panel(
        f"[{C['model']}]Model:[/] {GATEWAYS[ACTIVE_GW]['name']}\n"
        f"[{C['token']}]Tokens:[/] {SESSION.tokens['total']:,} | [{C['success']}]Cost:[/] ${SESSION.cost:.6f}\n"
        f"[{C['dim']}]Messages:[/] {len(SESSION.messages)} | Rounds: {SESSION.tool_rounds}\n"
        f"[{C['dim']}]Permission:[/] {CONFIG['permission_mode']} | Thinking: {'ON' if CONFIG['show_thinking'] else 'OFF'}\n"
        f"[{C['dim']}]Session:[/] {elapsed}",
        title="[bold]Status[/]", border_style=C["dim"], box=box.ROUNDED,
    ))

def cmd_clear():
    global SESSION
    SESSION.save(); SESSION = Session(); SESSION.gateway = ACTIVE_GW
    console.print(f"[{C['success']}]✓ New session[/]")

def cmd_save(args):
    console.print(f"[{C['success']}]✓ {SESSION.save()}[/]")

def cmd_report():
    """Auto-generate and save pentest report."""
    report = SESSION.to_markdown()
    path = REPORTS_DIR / f"report_{SESSION.id}.md"
    path.write_text(report)
    
    # Also save a summary JSON
    summary = {
        "session_id": SESSION.id,
        "gateway": SESSION.gateway,
        "tokens": SESSION.tokens,
        "cost": SESSION.cost,
        "commands": SESSION.commands[-10:],
        "duration": str(datetime.now() - SESSION.start),
        "findings": [],
    }
    json_path = REPORTS_DIR / f"summary_{SESSION.id}.json"
    json_path.write_text(json.dumps(summary, indent=2))
    
    console.print(f"[{C['success']}]✓ Report: {path}[/]")
    console.print(f"[{C['success']}]✓ Summary: {json_path}[/]")

def cmd_export():
    path = REPORTS_DIR / f"report_{SESSION.id}.md"
    path.write_text(SESSION.to_markdown())
    console.print(f"[{C['success']}]✓ {path}[/]")

def cmd_probe():
    console.print(f"\n[{C['accent']}]PROBING…[/]\n")
    for gw_id, gw in sorted(GATEWAYS.items(), key=lambda x: x[1].get("priority", 99)):
        key = get_api_key(gw_id)
        if not key and gw_id != "blockrun":
            console.print(f"  [{C['error']}]✗[/] {gw['name']:<30} NO KEY")
            continue
        console.print(f"  [{C['warning']}]⏳[/] {gw['name']:<30}", end="\r")
        result = call_api(gw_id, [{"role": "user", "content": "Say OK"}], system="Reply OK.", max_tokens=10)
        if "error" in result:
            console.print(f"  [{C['error']}]✗[/] {gw['name']:<30} {result['error'][:40]}")
        else:
            console.print(f"  [{C['success']}]✓[/] {gw['name']:<30} ALIVE — {result.get('model','?')} ({result.get('total_tokens',0)}t)")
    console.print()

def execute_shell(cmd):
    console.print(f"\n[{C['tool']}]$ {cmd}[/]")
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if r.stdout.strip() or r.stderr.strip():
            console.print(Panel(
                Syntax((r.stdout + r.stderr).strip(), "bash", theme="monokai"),
                title=f"[{C['dim']}]Output (exit: {r.returncode})[/]",
                border_style=C["dim"], box=box.ROUNDED,
            ))
        else:
            console.print(f"[{C['dim']}]Exit: {r.returncode}[/]")
    except Exception as e:
        console.print(f"[{C['error']}]{e}[/]")

def cmd_tokens():
    """Detailed token breakdown."""
    if not SESSION.per_model_tokens and SESSION.tokens["total"] == 0:
        console.print(f"[{C['dim']}]No tokens used yet. Start chatting![/]")
        return
    
    table = Table(title="Token Usage", box=box.ROUNDED, border_style=C["dim"])
    table.add_column("Model", style=C["model"])
    table.add_column("Input", style=C["dim"], justify="right")
    table.add_column("Output", style=C["dim"], justify="right")
    table.add_column("Total", style=C["token"], justify="right")
    table.add_column("Cost", style=C["success"], justify="right")
    
    for model, data in sorted(SESSION.per_model_tokens.items(), key=lambda x: -x[1]["total"]):
        table.add_row(
            model[:40],
            f"{data['in']:,}", f"{data['out']:,}",
            f"{data['total']:,}", f"${data['cost']:.6f}",
        )
    
    table.add_row("─"*20, "─"*8, "─"*8, "─"*8, "─"*10, style=C["dim"])
    table.add_row(
        "[bold]TOTAL[/]", f"{SESSION.tokens['in']:,}", f"{SESSION.tokens['out']:,}",
        f"[bold]{SESSION.tokens['total']:,}[/]", f"[bold]${SESSION.cost:.6f}[/]",
        style="bold",
    )
    
    if SESSION.budget_limit:
        pct = (SESSION.cost / SESSION.budget_limit) * 100
        color = C["success"] if pct < 50 else C["warning"] if pct < 80 else C["error"]
        table.add_row("", "", "", f"[{color}]Budget: {pct:.1f}%[/]", f"[{color}]${SESSION.budget_limit:.4f}[/]")
    
    console.print(table)

def cmd_cost():
    """Cost breakdown."""
    if SESSION.tokens["total"] == 0:
        console.print(f"[{C['dim']}]No cost data yet. Start chatting![/]")
        return
    elapsed = datetime.now() - SESSION.start
    hours = elapsed.total_seconds() / 3600
    rate = SESSION.cost / max(hours, 0.001)
    tok_rate = SESSION.tokens["total"] / max(hours, 0.001)
    avg_cost = SESSION.cost / max(len(SESSION.token_history), 1)
    
    lines = []
    lines.append(f"[{C['token']}]Session Tokens:[/] {SESSION.tokens['total']:,} ([{C['dim']}]in: {SESSION.tokens['in']:,}, out: {SESSION.tokens['out']:,})[/]")
    lines.append(f"[{C['success']}]Session Cost:[/] ${SESSION.cost:.6f}")
    lines.append(f"[{C['dim']}]Rate:[/] ${rate:.4f}/hr ({tok_rate:.0f} tok/hr)")
    lines.append(f"[{C['dim']}]Avg per request:[/] ${avg_cost:.6f}")
    lines.append(f"[{C['dim']}]Total requests:[/] {len(SESSION.token_history)}")
    lines.append("")
    lines.append(f"[{C['model']}]Per-Model:[/]")
    for m, d in sorted(SESSION.per_model_tokens.items(), key=lambda x: -x[1]["cost"]):
        lines.append(f"  [{C['dim']}]{m[:40]}:[/] {d['total']:,}t = [{C['success']}]${d['cost']:.6f}[/]")
    if SESSION.budget_limit:
        pct = SESSION.cost / SESSION.budget_limit * 100
        lines.append(f"[{C['warning']}]Budget: {pct:.1f}% of ${SESSION.budget_limit:.4f}[/]")
    
    console.print(Panel("\n".join(lines), title="[bold]Cost Breakdown[/]", border_style=C["dim"], box=box.ROUNDED))
def cmd_budget(args):
    """Set spending limit."""
    if not args:
        if SESSION.budget_limit:
            pct = (SESSION.cost / SESSION.budget_limit) * 100
            console.print(f"[{C['model']}]Budget: ${SESSION.budget_limit:.4f} — [{C['success'] if pct < 80 else C['error']}]{pct:.1f}% used[/]")
        else:
            console.print(f"[{C['dim']}]No budget set. Use /budget <amount>[/]")
        return
    try:
        limit = float(args[0])
        SESSION.budget_limit = limit
        console.print(f"[{C['success']}]✓ Budget set: ${limit:.4f}[/]")
    except ValueError:
        console.print(f"[{C['error']}]Invalid amount[/]")

def cmd_history():
    """Show command history with token costs."""
    table = Table(box=box.ROUNDED, border_style=C["dim"])
    table.add_column("#", style=C["dim"], width=3)
    table.add_column("Command", style="bold", max_width=40)
    table.add_column("Tokens", style=C["token"], justify="right")
    table.add_column("Cost", style=C["success"], justify="right")
    
    for i, cmd in enumerate(SESSION.commands[-20:]):
        preview = cmd[:40] + "..." if len(cmd) > 40 else cmd
        tok_data = SESSION.token_history[i] if i < len(SESSION.token_history) else {}
        table.add_row(
            str(i+1), preview,
            f"{tok_data.get('total', tok_data.get('in',0)+tok_data.get('out',0)):,}",
            f"${tok_data.get('cost', 0):.6f}",
        )
    
    console.print(table)

# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# PROJECT CONTEXT + GIT + REVIEW
# ═══════════════════════════════════════════════════════════════

def load_project_context():
    """Load CLAUDE.md / AGENTS.md / .cursorrules from cwd for coding context."""
    context = ""
    for fname in ["CLAUDE.md", "AGENTS.md", ".cursorrules"]:
        p = Path(fname)
        if p.exists():
            try:
                content = p.read_text()[:2000]
                context += f"\n## PROJECT CONTEXT ({fname})\n{content}\n"
            except:
                pass
    return context

PROJECT_CONTEXT = load_project_context()

def get_effective_system_prompt():
    """Return BEAST_SYSTEM with project context if available."""
    if PROJECT_CONTEXT:
        return BEAST_SYSTEM + PROJECT_CONTEXT
    return BEAST_SYSTEM

def cmd_git(args):
    """Git helper: status, log, diff, commit, branch."""
    action = args[0] if args else "status"
    if action == "status":
        execute_shell("git status --short")
    elif action == "log":
        execute_shell("git log --oneline -10")
    elif action == "diff":
        execute_shell("git diff --stat && git diff | head -200")
    elif action == "branch":
        execute_shell("git branch -a")
    elif action == "commit" and len(args) > 1:
        msg = " ".join(args[1:])
        execute_shell(f'git add -A && git commit -m "{msg}"')
    elif action == "push":
        execute_shell("git push")
    elif action == "pull":
        execute_shell("git pull")
    else:
        console.print(f"[{C['dim']}]Usage: /git [status|log|diff|branch|commit <msg>|push|pull][/]")

def cmd_review(args):
    """Code review via AI on git diff or a file."""
    if args and Path(args[0]).exists():
        # Review a specific file (resolve absolute path)
        path = str(Path(args[0]).resolve())
        content = Path(path).read_text()[:5000]
        prompt = f"Review the code below for bugs, security issues, and improvements. The full content is already provided — do NOT re-read the file, just analyze it:\n\nFile: {path}\n\n```\n{content}\n```"
    else:
        # Review git diff
        import subprocess
        diff = subprocess.run("git diff HEAD 2>/dev/null | head -300", shell=True, capture_output=True, text=True).stdout
        if not diff.strip():
            console.print(f"[{C['warning']}]No git diff. Use /review <file> to review a specific file.[/]")
            return
        prompt = f"Review this git diff for bugs, security issues, and improvements:\n```diff\n{diff}\n```"
    
    console.print(f"\n[{C['accent']}]📝 CODE REVIEW[/]\n")
    agentic_loop(prompt)

def cmd_edit(args):
    """Open a file in $EDITOR or vim."""
    if not args:
        console.print(f"[{C['error']}]Usage: /edit <file>[/]")
        return
    path = args[0]
    if not Path(path).exists():
        console.print(f"[{C['warning']}]File not found: {path}[/]")
        return
    editor = os.environ.get("EDITOR", "vim")
    os.system(f"{editor} {path}")

# ═══════════════════════════════════════════════════════════════
# EXTERNAL API INTEGRATIONS (Skills API + CVE + Exa)
# ═══════════════════════════════════════════════════════════════

SKILLS_API = "http://localhost:8765"
SKILLS_API_KEY = os.environ.get("LOG_API_KEY", "hermes-logs-2026")
EXA_API_KEY = os.environ.get("MCP_EXA_API_KEY", "")

def api_get(path):
    """GET request to Skills API."""
    url = SKILLS_API + path
    headers = {"X-API-Key": SKILLS_API_KEY}
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def cmd_skill(args):
    """Fetch full skill content from Skills API."""
    if not args:
        console.print(f"[{C['error']}]Usage: /skill <name>[/]")
        return
    name = args[0]
    console.print(f"[{C['dim']}]Fetching skill: {name}...[/]")
    data = api_get(f"/skills/{name}")
    if "error" in data:
        console.print(f"[{C['error']}]Error: {data['error']}[/]")
        return
    content = data.get("content", "")
    if isinstance(content, dict):
        content = json.dumps(content, indent=2)
    content = str(content)
    # Strip YAML frontmatter (between --- markers)
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2].strip()
    console.print(Panel(
        f"[{C['model']}]{name}[/]\n\n{content[:4000]}",
        title=f"[bold]Skill: {name}[/]",
        border_style=C["model"], box=box.ROUNDED,
    ))

def cmd_search(args):
    """Search skills via FTS."""
    if not args:
        console.print(f"[{C['error']}]Usage: /search <query>[/]")
        return
    query = " ".join(args)
    console.print(f"[{C['dim']}]Searching: {query}...[/]")
    data = api_get(f"/search?q={urllib.parse.quote(query)}&limit=10")
    if "error" in data:
        console.print(f"[{C['error']}]Error: {data['error']}[/]")
        return
    results = data.get("results", [])
    if not results:
        # Try OR search for multi-word queries
        or_query = " OR ".join(query.split())
        data2 = api_get(f"/search?q={urllib.parse.quote(or_query)}&limit=10")
        results = data2.get("results", [])
    if not results:
        console.print(f"[{C['warning']}]No results for '{query}'[/]")
        return
    table = Table(title=f"Skill Search: {query} ({data.get('total', 0)} found)", box=box.ROUNDED, border_style=C["dim"])
    table.add_column("Name", style=C["model"])
    table.add_column("Category", style=C["dim"])
    table.add_column("Description", style="bold", max_width=60)
    for r in results:
        table.add_row(r.get("name", "?"), r.get("category", "?"), r.get("description", "")[:60])
    console.print(table)

def cmd_web(args):
    """Exa web search."""
    if not args:
        console.print(f"[{C['error']}]Usage: /web <query>[/]")
        return
    query = " ".join(args)
    if not EXA_API_KEY:
        console.print(f"[{C['error']}]No MCP_EXA_API_KEY set. Set valid key: export MCP_EXA_API_KEY=...[/]")
        return
    console.print(f"[{C['dim']}]Searching web: {query}...[/]")
    body = json.dumps({"query": query, "numResults": 5}).encode()
    req = Request(
        "https://api.exa.ai/search",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {EXA_API_KEY}"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        console.print(f"[{C['error']}]Exa error: {e}[/]")
        return
    results = data.get("results", [])
    if not results:
        console.print(f"[{C['warning']}]No web results[/]")
        return
    table = Table(title=f"Web Search: {query}", box=box.ROUNDED, border_style=C["info"])
    table.add_column("#", style=C["dim"])
    table.add_column("Title", style="bold", max_width=40)
    table.add_column("URL", style=C["info"], max_width=50)
    for i, r in enumerate(results):
        table.add_row(str(i+1), r.get("title", "?")[:40], r.get("url", "?")[:50])
    console.print(table)

def cmd_cve_api(args):
    """Enhanced CVE search via Skills API."""
    if not args:
        console.print(f"[{C['error']}]Usage: /cve-api <query>[/]")
        return
    query = " ".join(args)
    console.print(f"[{C['dim']}]Searching CVEs: {query}...[/]")
    data = api_get(f"/cve/search?q={urllib.parse.quote(query)}&limit=10")
    if "error" in data:
        console.print(f"[{C['error']}]Error: {data['error']}[/]")
        return
    results = data.get("results", [])
    if not results:
        console.print(f"[{C['warning']}]No CVEs for '{query}'[/]")
        return
    table = Table(title=f"CVE Search: {query} ({data.get('total', 0)} found)", box=box.ROUNDED, border_style=C["dim"])
    table.add_column("CVE", style=C["model"])
    table.add_column("CVSS", style=C["warning"], justify="right")
    table.add_column("Severity", style="bold")
    table.add_column("Description", max_width=60)
    for c in results:
        sev = c.get("cvss_severity", "?")
        sev_color = C["error"] if sev == "CRITICAL" else C["warning"] if sev == "HIGH" else C["dim"]
        table.add_row(c.get("cve_id", "?"), str(c.get("cvss_score", "?")), f"[{sev_color}]{sev}[/]", c.get("description", "")[:60])
    console.print(table)

# PENTEST PROMPTS
# ═══════════════════════════════════════════════════════════════

def cmd_parallel(args):
    """Ask multiple gateways simultaneously."""
    if not args:
        console.print(f"[{C['error']}]Usage: /parallel <question>[/]")
        return
    question = " ".join(args)
    gateways = [g for g in GATEWAYS if get_api_key(g) or g == "blockrun"]
    gateways = gateways[:3]
    console.print(f"\n[{C['accent']}]⚡ PARALLEL: {len(gateways)} gateways[/]\n")
    results = {}
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        tasks = {g: progress.add_task(f"[{C['model']}]{GATEWAYS[g]['name']}[/]", total=None) for g in gateways}
        def ask_one(gw):
            result = call_api(gw, [{"role": "user", "content": question}], system=BEAST_SYSTEM)
            progress.update(tasks[gw], completed=True, visible=False)
            return gw, result
        with ThreadPoolExecutor(max_workers=len(gateways)) as ex:
            futures = {ex.submit(ask_one, g): g for g in gateways}
            for future in as_completed(futures):
                gw, result = future.result()
                results[gw] = result
    for gw, result in results.items():
        name = GATEWAYS[gw]["name"]
        if "error" in result:
            console.print(f"[{C['error']}]✗ {name}: {result['error'][:60]}[/]")
        else:
            console.print(Panel(
                result["content"][:600] + ("..." if len(result["content"]) > 600 else ""),
                title=f"[{C['model']}]{name}[/] ({result.get('total_tokens', 0)}t)",
                border_style=C["success"], box=box.ROUNDED,
            ))

PENTEST = {
    "recon": lambda t: f"Full reconnaissance on {t}. Use bash tools: dig, whatweb, curl, nmap. Check DNS, subdomains, tech stack, ports, directories, JS, CVEs, WAF, origin IP. Execute commands and report findings.",
    "exploit": lambda t: f"Active exploitation on {t}. Use bash tools for curl, python3 exploits. Identify vectors, develop PoC, bypass WAF. Priority: RCE > SQLi > Auth Bypass. Execute and report.",
    "cve": lambda t: f"Search CVEs for {t}. Use bash: sqlite3 ~/.hermes/skills-hub.db. Get details, public exploits, exploitation steps, WAF bypass. Execute commands.",
    "bypass": lambda t: f"Bypass WAF/CDN on {t}. Use bash tools: curl_cffi, dig, curl. Try origin IP, TLS impersonation, smuggling, encoding. Execute each technique.",
    "chain": lambda t: f"Full attack chain on {t}. Phase 1: Recon. Phase 2: Vuln. Phase 3: Exploit. Phase 4: Priv Esc. Phase 5: Report. Use tools for each phase.",
    "sqlmap": lambda t: f"Automated SQLi on {t}. Use bash: sqlmap with all flags. Execute and report.",
    "fuzz": lambda t: f"Parameter fuzzing on {t}. Use bash: ffuf with wordlists. Execute and report.",
}

def dispatch(cmd, args):
    if cmd in ("help", "h", "?"): cmd_help()
    elif cmd in ("gateways", "models"): cmd_gateways()
    elif cmd == "model": cmd_model(args)
    elif cmd == "permission": cmd_permission(args)
    elif cmd == "thinking": cmd_thinking()
    elif cmd == "compact": cmd_compact()
    elif cmd == "tokens": cmd_tokens()
    elif cmd == "cost": cmd_cost()
    elif cmd == "budget": cmd_budget(args)
    elif cmd == "history": cmd_history()
    elif cmd == "report": cmd_report()
    elif cmd == "parallel": cmd_parallel(args)
    elif cmd == "git": cmd_git(args)
    elif cmd == "review": cmd_review(args)
    elif cmd == "edit": cmd_edit(args)
    elif cmd == "skill": cmd_skill(args)
    elif cmd == "search": cmd_search(args)
    elif cmd == "web": cmd_web(args)
    elif cmd == "cve-api": cmd_cve_api(args)
    elif cmd == "probe": cmd_probe()
    elif cmd == "status": cmd_status()
    elif cmd == "clear": cmd_clear()
    elif cmd == "save": cmd_save(args)
    elif cmd == "export": cmd_export()
    elif cmd == "!": execute_shell(" ".join(args))
    elif cmd in ("exit", "quit", "q"):
        SESSION.save()
        console.print(f"\n[{C['accent']}]👋 Session: {SESSION.id}[/]")
        sys.exit(0)
    elif cmd == "auto":
        target = args[0] if args else input("Target: ").strip()
        if target:
            console.print(f"\n[{C['accent']}]⚡ AUTO PENTEST: {target}[/]")
            for phase in ["recon", "vuln", "exploit", "report"]:
                console.print(f"\n[{C['info']}]▸ PHASE: {phase.upper()}[/]")
                agentic_loop(PENTEST[phase](target) if phase in PENTEST else f"Generate pentest report for {target}.")
        else:
            console.print(f"[{C['error']}]No target[/]")
    elif cmd in PENTEST:
        target = " ".join(args) if args else "target.com"
        console.print(f"\n[{C['accent']}]⚡ /{cmd} {target}[/]")
        agentic_loop(PENTEST[cmd](target))
    else:
        console.print(f"[{C['error']}]Unknown: /{cmd}[/]")

# ═══════════════════════════════════════════════════════════════
# STATUS BAR (Claude Code-style, always visible)
# ═══════════════════════════════════════════════════════════════

def render_status_bar():
    gw = GATEWAYS[ACTIVE_GW]
    elapsed = datetime.now() - SESSION.start
    mins, secs = int(elapsed.total_seconds() // 60), int(elapsed.total_seconds() % 60)
    perm = CONFIG["permission_mode"]
    mode_sym = {"auto": "⏵⏵", "plan": "○", "normal": "⏸"}.get(perm, "⏸")
    t = Text()
    t.append(f" {mode_sym} {perm}", style=C['dim'])
    t.append(f" · {ACTIVE_GW}", style=C['model'])
    t.append(f" · {SESSION.tokens['total']:,} tok", style=C['token'])
    t.append(f" · ${SESSION.cost:.4f}", style=C['success'])
    t.append(f" · {mins}m {secs}s", style=C['dim'])
    return Panel(t, border_style=C["dim"], box=box.ROUNDED, padding=(0, 1))

# ═══════════════════════════════════════════════════════════════
# BANNER
# ═══════════════════════════════════════════════════════════════

def print_banner():
    """Claude Code-style startup banner."""
    gw = GATEWAYS[ACTIVE_GW]
    version = "5.3"
    cwd = os.getcwd().replace(os.path.expanduser("~"), "~")
    console.print()
    console.print(f"[bold {C['accent']}]▐▛███▛█[/]   [bold white]BEAST Terminal v{version}[/]")
    console.print(f"[bold {C['accent']}]▝▜██████▀[/]  [{C['model']}]{gw['name']}[/] · [{C['dim']}]API Usage[/]")
    console.print(f"[{C['accent']}]  ▝▝ ▝▝[/]    [{C['dim']}]{cwd}[/]")
    console.print()

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    global ACTIVE_GW
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "-l": cmd_gateways(); return
        if sys.argv[1] == "--probe": cmd_probe(); return
        if sys.argv[1] == "-m" and len(sys.argv) > 2:
            cmd_model([sys.argv[2]])
            if len(sys.argv) > 3: user_input = " ".join(sys.argv[3:])
            else: return
        elif sys.argv[1] == "--auto" and len(sys.argv) > 2:
            for phase in ["recon", "vuln", "exploit", "report"]:
                console.print(f"\n[{C['info']}]▸ {phase.upper()}[/]")
                agentic_loop(PENTEST[phase](sys.argv[2]) if phase in PENTEST else f"Report for {sys.argv[2]}.")
            return
        else:
            user_input = " ".join(sys.argv[1:])
        
        if user_input.startswith("/"):
            parts = user_input[1:].split(maxsplit=1)
            dispatch(parts[0].lower(), parts[1].split() if len(parts) > 1 else [])
        else:
            agentic_loop(user_input)
        return
    
    # Interactive mode
    print_banner()
    console.print()
    
    history_file = str(BEAST_DIR / "history")
    completions = list(PENTEST.keys()) + ["auto", "model", "gateways", "permission", "thinking", 
                    "compact", "clear", "save", "export", "status", "probe", "tokens", "cost", "budget", "history", "help", "exit"]
    completer = WordCompleter(["/" + c for c in completions], ignore_case=True, sentence=True)
    
    style = Style.from_dict({"prompt": f"bold {C['accent']}", "sep": C['dim'], "gw": f"bold {C['model']}"})
    
    session = PromptSession(
        history=FileHistory(history_file), completer=completer, style=style,
        auto_suggest=AutoSuggestFromHistory(),
    )
    
    while True:
        try:
            console.print(render_status_bar())
            prompt_text = HTML(f'<prompt>❯ </prompt>')
            user_input = session.prompt(prompt_text).strip()
        except (EOFError, KeyboardInterrupt):
            SESSION.save()
            console.print(f"\n[{C['accent']}]👋 {SESSION.id}[/]")
            break
        
        if not user_input: continue
        
        if user_input.startswith("/"):
            parts = user_input[1:].split(maxsplit=1)
            dispatch(parts[0].lower(), parts[1].split() if len(parts) > 1 else [])
        else:
            agentic_loop(user_input)

if __name__ == "__main__":
    import urllib.request, urllib.error, urllib.parse
    main()