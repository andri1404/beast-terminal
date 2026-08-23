#!/usr/bin/env python3
"""
BEAST Terminal Web Server — 24/7 VPS Deployable
tmux sessions persist across disconnects. Access via browser.
"""

import os, sys, json, time, subprocess, uuid, signal, fcntl, select, pty, struct, termios
from pathlib import Path
from datetime import datetime

# Fix PYTHONPATH for background processes
SITE_PACKAGES = Path.home() / ".local/lib/python3.12/site-packages"
if str(SITE_PACKAGES) not in sys.path:
    sys.path.insert(0, str(SITE_PACKAGES))

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
from collections import defaultdict

# ═══════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════

BEAST_DIR = Path(__file__).resolve().parent.parent
TMUX_SESSIONS = {}
SESSIONS_DIR = Path.home() / ".beast" / "web_sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

MODE_SYSTEM_PROMPTS = {
    "pentest": "PENTEST MODE: You are BEAST, a penetration testing AI. Use /recon /exploit /cve /auto commands.",
    "coding": "CODING MODE: You are a senior software engineer. Write clean, efficient code. Use /! for shell commands.",
    "general": "GENERAL MODE: You are a helpful AI assistant. Use /help for available commands.",
}

app = Flask(__name__, static_folder="static", template_folder="static")
app.config["SECRET_KEY"] = os.urandom(24).hex()
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ═══════════════════════════════════════════════
# TMUX SESSION MANAGEMENT
# ═══════════════════════════════════════════════

def create_tmux_session(session_id, mode="pentest"):
    """Create a new tmux session running BEAST terminal."""
    session_name = f"beast-{session_id[:8]}"
    mode_prompt = MODE_SYSTEM_PROMPTS.get(mode, MODE_SYSTEM_PROMPTS["pentest"])
    
    # Kill existing session if any
    subprocess.run(f"tmux kill-session -t {session_name}", shell=True, stderr=subprocess.DEVNULL)
    
    # Create new tmux session with BEAST
    beast_py = BEAST_DIR / "beast.py"
    cmd = f"tmux new-session -d -s {session_name} -x 140 -y 40 'python3 {beast_py}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        return None, result.stderr
    
    # Get window info
    info = subprocess.run(f"tmux list-windows -t {session_name} -F '#{{window_id}} #{{pane_pid}}'",
                         shell=True, capture_output=True, text=True)
    if info.returncode != 0:
        return None, "Failed to get window info"
    
    parts = info.stdout.strip().split()
    window_id = parts[0] if parts else "?"
    pane_pid = parts[1] if len(parts) > 1 else "?"
    
    TMUX_SESSIONS[session_id] = {
        "session_name": session_name,
        "window_id": window_id,
        "pane_pid": pane_pid,
        "created": datetime.now(),
    }
    
    return session_name, None

def send_to_tmux(session_id, data):
    """Send data to tmux session."""
    if session_id not in TMUX_SESSIONS:
        return False
    session_name = TMUX_SESSIONS[session_id]["session_name"]
    # Escape special characters
    escaped = data.replace("'", "'\\''")
    subprocess.run(f"tmux send-keys -t {session_name} '{escaped}'",
                  shell=True, stderr=subprocess.DEVNULL)
    return True

def capture_tmux(session_id):
    """Capture tmux pane output."""
    if session_id not in TMUX_SESSIONS:
        return ""
    session_name = TMUX_SESSIONS[session_id]["session_name"]
    result = subprocess.run(
        f"tmux capture-pane -t {session_name} -p -S -100",
        shell=True, capture_output=True, text=True
    )
    return result.stdout

def read_tmux_output(session_id, last_pos=0):
    """Read new output from tmux since last position."""
    output = capture_tmux(session_id)
    if len(output) > last_pos:
        new_data = output[last_pos:]
        return new_data, len(output)
    return "", last_pos

# ═══════════════════════════════════════════════
# WEBSOCKET HANDLERS
# ═══════════════════════════════════════════════

@socketio.on("connect")
def handle_connect():
    session_id = request.args.get("session_id", str(uuid.uuid4())[:12])
    join_room(session_id)
    
    # Create or resume tmux session
    mode = request.args.get("mode", "pentest")
    if session_id not in TMUX_SESSIONS:
        name, error = create_tmux_session(session_id, mode)
        if error:
            emit("error", {"message": f"Failed to create session: {error}"})
            return
        time.sleep(1)  # Wait for tmux to initialize
    
    emit("connected", {
        "session_id": session_id,
        "session_name": TMUX_SESSIONS[session_id]["session_name"],
        "message": "BEAST Terminal ready! Type /help for commands."
    })
    
    # Send initial tmux output
    output = capture_tmux(session_id)
    if output:
        emit("output", {"data": output})

@socketio.on("input")
def handle_input(data):
    session_id = data.get("session_id", "")
    text = data.get("text", "")
    if session_id in TMUX_SESSIONS:
        send_to_tmux(session_id, text)
        time.sleep(0.2)
        # Send updated output
        output = capture_tmux(session_id)
        emit("output", {"data": output})

@socketio.on("resize")
def handle_resize(data):
    session_id = data.get("session_id", "")
    cols = data.get("cols", 140)
    rows = data.get("rows", 40)
    if session_id in TMUX_SESSIONS:
        session_name = TMUX_SESSIONS[session_id]["session_name"]
        subprocess.run(f"tmux resize-window -t {session_name} -x {cols} -y {rows}",
                      shell=True, stderr=subprocess.DEVNULL)

@socketio.on("mode")
def handle_mode(data):
    session_id = data.get("session_id", "")
    mode = data.get("mode", "pentest")
    if session_id in TMUX_SESSIONS:
        TMUX_SESSIONS[session_id]["mode"] = mode
        prompt = MODE_SYSTEM_PROMPTS.get(mode, "")
        send_to_tmux(session_id, f"\n\x1b[33m[MODE: {mode.upper()}]\x1b[0m\n")

@socketio.on("disconnect")
def handle_disconnect():
    # Session stays alive in tmux - user can reconnect
    pass

@socketio.on("kill_session")
def handle_kill_session(data):
    session_id = data.get("session_id", "")
    if session_id in TMUX_SESSIONS:
        session_name = TMUX_SESSIONS[session_id]["session_name"]
        subprocess.run(f"tmux kill-session -t {session_name}", shell=True, stderr=subprocess.DEVNULL)
        del TMUX_SESSIONS[session_id]
        emit("killed", {"message": "Session terminated"})

# ═══════════════════════════════════════════════
# HTTP ROUTES
# ═══════════════════════════════════════════════

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "sessions": len(TMUX_SESSIONS),
        "uptime": str(datetime.now() - start_time) if "start_time" in globals() else "unknown",
    })

@app.route("/api/sessions")
def list_sessions():
    return jsonify({
        str(sid): {
            "name": info["session_name"],
            "created": info["created"].isoformat(),
        }
        for sid, info in TMUX_SESSIONS.items()
    })

# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    start_time = datetime.now()
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  BEAST Terminal Web Server                                  ║
║  Port: {port}                                                  ║
║  URL:  http://{host}:{port}                                       ║
║  Sessions persist in tmux — reconnect anytime               ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)