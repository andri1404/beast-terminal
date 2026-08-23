#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# BEAST Terminal — Deploy to VPS
# ═══════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
BEAST_DIR="$HOME/pentest-cli"

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  BEAST Terminal — VPS Deployment                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 1. Check dependencies
echo -e "${CYAN}[1/5] Checking dependencies...${NC}"
command -v python3 >/dev/null || { echo "Need python3"; exit 1; }
command -v tmux >/dev/null || { echo "Need tmux"; apt install -y tmux; }
command -v cloudflared >/dev/null || { 
    echo "Installing cloudflared..."
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
    chmod +x /usr/local/bin/cloudflared
}

# 2. Install Python packages
echo -e "${CYAN}[2/5] Installing Python packages...${NC}"
pip install --break-system-packages flask flask-socketio rich prompt_toolkit requests curl_cffi 2>/dev/null

# 3. Set up systemd service
echo -e "${CYAN}[3/5] Setting up systemd service...${NC}"
TOKEN=$(grep -oP 'HERMES_CUSTOM_API_TOKENROUTER_COM_API_KEY=\K[^ ]+' ~/.bashrc 2>/dev/null || echo "")
if [ -z "$TOKEN" ]; then
    TOKEN="${HERMES_CUSTOM_API_TOKENROUTER_COM_API_KEY}"
fi

sed "s|%TOKENROUTER_KEY%|${TOKEN}|" "$BEAST_DIR/deploy/beast-terminal.service" | \
    sudo tee /etc/systemd/system/beast-terminal.service > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable beast-terminal
sudo systemctl restart beast-terminal

# 4. Wait for startup
echo -e "${CYAN}[4/5] Starting server...${NC}"
sleep 3
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Server running on port 5000${NC}"
else
    echo -e "${RED}✗ Server failed to start. Check: sudo journalctl -u beast-terminal -n 20${NC}"
    exit 1
fi

# 5. Start cloudflared tunnel (optional)
echo -e "${CYAN}[5/5] Cloudflare Tunnel (optional)...${NC}"
if command -v cloudflared >/dev/null; then
    # Kill existing tunnel
    pkill -f "cloudflared tunnel" 2>/dev/null || true
    
    # Start tunnel in background
    nohup cloudflared tunnel --url http://localhost:5000 > /tmp/beast-tunnel.log 2>&1 &
    sleep 3
    
    TUNNEL_URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/beast-tunnel.log | head -1)
    if [ -n "$TUNNEL_URL" ]; then
        echo -e "${GREEN}✓ Public URL: ${TUNNEL_URL}${NC}"
    else
        echo -e "${YELLOW}⚠ Tunnel starting... check: cat /tmp/beast-tunnel.log${NC}"
    fi
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗"
echo "║  BEAST Terminal Deployed!                                  ║"
echo "║  Local:  http://localhost:5000                             ║"
echo "║  Public: ${TUNNEL_URL:-N/A}                    ║"
echo "║  Status: sudo systemctl status beast-terminal              ║"
echo "║  Logs:   sudo journalctl -u beast-terminal -f              ║"
echo "╚══════════════════════════════════════════════════════════════╝${NC}"