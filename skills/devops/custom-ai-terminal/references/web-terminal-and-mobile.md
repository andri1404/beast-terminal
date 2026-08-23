# Web Terminal + Mobile — Exposing a TUI CLI to the browser

Turn a `rich`/`prompt_toolkit` CLI into a browser/mobile terminal. Core pattern used by BEAST: **Flask + Flask-SocketIO + tmux** (tmux gives session persistence across disconnects).

## Architecture

```
Browser (xterm.js OR chat UI)
   │  WebSocket (socket.io)
   ▼
Flask-SocketIO  (web/server.py)
   │  tmux send-keys / capture-pane
   ▼
tmux session ── runs `python3 beast.py` (interactive CLI)
```

Why tmux: the CLI process keeps running when the browser tab closes — reconnect anytime, same shell, same session state. Each client `session_id` maps to one tmux session `beast-<id[:8]>`.

## Delta output streaming (avoid output duplication)

Naive version re-sends the FULL pane after every input, so the browser duplicates everything. Track a cursor and send only the delta:

```python
@ socket.on("input")
def handle_input(data):
    send_to_tmux(sid, text)          # tmux send-keys
    time.sleep(0.3)
    out = capture_tmux(sid)          # tmux capture-pane -S -100
    last = TMUX_SESSIONS[sid].get("last_pos", 0)
    if len(out) > last:
        TMUX_SESSIONS[sid]["last_pos"] = len(out)
        emit("output", {"data": out[last:]})   # only new bytes
    else:
        TMUX_SESSIONS[sid]["last_pos"] = 0      # pane reset, resync
```

Also set `last_pos` on initial connect so the first response doesn't replay the whole pane.

## Two UI styles

1. **Terminal (xterm.js)** — raw ANSI passthrough, accurate but dense. Good for a CLI-faithful view.
2. **Chat-style** (user generally prefers this for "simple, HP-friendly"): header + horizontally scrollable **quick chips** (one tap inserts `/recon ` etc.) + scrollable output + **input bar pinned to the bottom with a big Send button** + mobile key row (Tab/Esc/^C/^D/↑/↓). Strip ANSI before display:

```js
let clean = raw
  .replace(/\x1b\[[0-9;]*[a-zA-Z]/g, '')     // ANSI
  .replace(/[\u2500-\u257f\u2580-\u259f]/g, '') // box-drawing noise
  .replace(/\r/g, '');
```

Send as `socket.emit('input', { text: cmd + '\r' })` — append the literal CR so tmux `send-keys` submits it.

## PWA (install to phone home screen)

- `static/manifest.json` with `display: standalone`, `theme_color`, a data-URL SVG icon.
- `static/sw.js` service worker — cache static assets, network-first for socket.io.
- Register: `navigator.serviceWorker.register('/static/sw.js')`.
- `<meta name="apple-mobile-web-app-capable" content="yes">` + `viewport-fit=cover` + `env(safe-area-inset-bottom)` on the input bar.

## Exposing publicly

- **cloudflared quick tunnel** (`cloudflared tunnel --url http://localhost:5000`) often returns **530 origin unreachable** / 404 on some VPS network configs, and conflicts if a named-tunnel systemd service (`cf-tunnel`) is also running — kill/stop it first.
- **ngrok** (`ngrok http 5000`) is more reliable on the same box: direct TCP tunnel, gives `https://xxx.ngrok-free.dev`. Free tier shows a one-time "Visit Site" interstitial. Auth token via `ngrok config add-authtoken <token>`.
- Free tunnels die silently — pair with a systemd `Restart=always` service or just restart manually.

## Pitfalls

- Starting the web server with `python3 web/server.py &` in a foreground `terminal()` call is blocked — use `background=true`.
- On gateway/tunnel restarts the Flask server dies too; check `ss -tlnp | grep 5000` (a `pgrep server.py` can falsely match an unrelated `skills-api/server.py`).
- Windows install: `--break-system-packages` is Linux-only; `export` → `$env:`; `python3` → `python`. Repo README should carry separate Windows vs Linux/macOS install blocks.