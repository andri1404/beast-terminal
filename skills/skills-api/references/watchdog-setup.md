#!/bin/bash
# Skills API Auto-Heal Watchdog
# Checks health, fixes issues, restarts if needed
# Run: every 5 minutes via cron or systemd timer
#
# INSTALL: cp this file to ~/.hermes/scripts/skills-watchdog.sh
#          cronjob action=create name=skills-api-watchdog-fast schedule="every 5m" \
#            script=skills-watchdog.sh no_agent=true

set -e

API_URL="http://127.0.0.1:8765"
API_KEY="hermes-logs-2026"
LOG_FILE="/home/ubuntu/.hermes/skills-api/watchdog.log"
SKILLS_MIN=100
MCP_SERVER="/home/ubuntu/.hermes/skills-api/mcp_server_v2.py"
DB_PATH="/home/ubuntu/.hermes/skills-hub.db"
START_SCRIPT="/home/ubuntu/.hermes/skills-api/start-all.sh"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

fix_skills_dirs_extra() {
    local svc="/etc/systemd/system/skills-api.service"
    if grep -q 'SKILLS_DIRS_EXTRA=$' "$svc" 2>/dev/null || grep -q 'SKILLS_DIRS_EXTRA=""' "$svc" 2>/dev/null; then
        log "FIX: Updating SKILLS_DIRS_EXTRA in systemd service"
        sed -i 's|Environment=SKILLS_DIRS_EXTRA=.*|Environment=SKILLS_DIRS_EXTRA=/home/ubuntu/.hermes/skills|' "$svc"
        systemctl daemon-reload
        return 0
    fi
    return 1
}

check_api() {
    curl -s --connect-timeout 5 "$API_URL/health" > /dev/null 2>&1
}

check_db() {
    if [ -f "$DB_PATH" ]; then
        local skills=$(python3 -c "import sqlite3; db=sqlite3.connect('$DB_PATH'); print(db.execute('SELECT COUNT(*) FROM skills').fetchone()[0])" 2>/dev/null)
        [ -n "$skills" ] && [ "$skills" -ge "$SKILLS_MIN" ]
    else
        return 1
    fi
}

restart_api() {
    log "RESTART: Killing existing API..."
    fuser -k 8765/tcp 2>/dev/null || true
    sleep 2
    log "RESTART: Running start-all.sh..."
    cd /home/ubuntu/.hermes/skills-api
    bash "$START_SCRIPT" >> "$LOG_FILE" 2>&1
    sleep 5
    if check_api; then
        log "✓ API restarted successfully"
        return 0
    else
        log "✗ API restart failed"
        return 1
    fi
}

# ---- MAIN ----
log "=== Watchdog check ==="

ISSUES=0

# 1. Fix systemd service config
if fix_skills_dirs_extra; then
    ISSUES=$((ISSUES + 1))
fi

# 2. Check API health
if ! check_api; then
    log "ISSUE: API not responding"
    restart_api
    ISSUES=$((ISSUES + 1))
else
    log "✓ API health OK"
fi

# 3. Check DB skills count
if ! check_db; then
    log "ISSUE: DB skills count below minimum ($SKILLS_MIN)"
    restart_api
    ISSUES=$((ISSUES + 1))
else
    log "✓ Skills count OK"
fi

# 4. Verify MCP v2 server works
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"watchdog","version":"1.0"}}}' | timeout 5 python3 "$MCP_SERVER" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log "✓ MCP v2 server OK"
else
    log "ISSUE: MCP v2 server not responding"
    ISSUES=$((ISSUES + 1))
fi

if [ "$ISSUES" -gt 0 ]; then
    log "⚠️  Fixed $ISSUES issue(s)"
else
    log "✅ All systems healthy"
fi