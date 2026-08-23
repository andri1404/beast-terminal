# WAL Silent Bloating Detection

## The Problem

`hermes doctor`, `hermes sessions repair`, and `PRAGMA integrity_check` all report "clean" / "ok" even when the WAL file is silently bloating behind a long-running gateway read lock. The main DB file is intact — the corruption is in the WAL's inability to checkpoint.

## Symptoms
- `state.db-wal` growing over hours/days
- "database disk image is malformed" in errors.log
- "session storage could not be written" user-facing errors
- `PRAGMA integrity_check` returns `ok` (misleading!)

## Diagnosis

Always check WAL size before trusting repairs:
```bash
ls -lh ~/.hermes/state.db ~/.hermes/state.db-wal
```

A WAL > 1MB with a multi-day gateway uptime is a red flag.

## Root Cause

The gateway process holds a read lock on state.db, preventing WAL checkpoint. The WAL accumulates all writes since the gateway started. On a long-running gateway (days), this can reach multiple MB.

## Fix

Kill the gateway to release the read lock, allowing WAL checkpoint:
```bash
# Find + kill gateway
ps aux | grep "hermes.*gateway run" | grep -v grep
kill <gateway_pid>

# WAL auto-checkpoints on next connection, or force:
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/ubuntu/.hermes/state.db')
conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
conn.execute('VACUUM')
conn.close()
"

# Restart
hermes gateway start
```

## PITFALL — Gateway blocks self-kill

The gateway process blocks `fuser -k` and `kill` from within agent sessions. This must be done from SSH outside the gateway.