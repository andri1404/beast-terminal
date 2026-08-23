# Disk Cleanup — Fastest Space Recovery

When `df -h /` shows 100% (or <500MB free), use these commands in order. All are safe to run from `terminal` even when `execute_code` is unavailable (disk-full blocks the sandbox).

## Quick Recovery (~350MB in 5 seconds)

```bash
# 1. Temp cruft (often 150-200MB)
rm -f /tmp/rockyou_raw.txt /tmp/exploitdb.csv /tmp/postech_*.pdf
rm -rf /tmp/epaksi_source /tmp/epaksi_source.zip

# 2. Old browser caches (varies, 5-50MB)
rm -rf /tmp/agent-browser-chrome-* /tmp/node-compile-cache

# 3. Truncate failed-login log (often 50-100MB)
sudo truncate -s 0 /var/log/btmp

# 4. Old auth/syslog rotated logs (often 30-50MB)
sudo rm -f /var/log/auth.log.1 /var/log/auth.log.2.gz /var/log/auth.log.3.gz /var/log/syslog.1 /var/log/syslog.2.gz

# 5. Sysstat SAR data (often 5-15MB)
sudo rm -rf /var/log/sysstat/*

# Verify
df -h /
```

## If Still Tight

```bash
# Hermes logs (safe to truncate)
find /home/ubuntu/.hermes/logs /home/ubuntu/.hermes/skills-api -name "*.log" -size +500k -exec truncate -s 0 {} \;

# Pip/uv caches
rm -rf /home/ubuntu/.cache/pip /home/ubuntu/.cache/uv

# Old DB backups (keep only the current)
rm -f /home/ubuntu/.hermes/skills-hub.db.bak /home/ubuntu/.hermes/skills-hub.db.bak.* /home/ubuntu/.hermes/skills-hub.db.empty_bak /home/ubuntu/.hermes/skills-hub.db.pre_restore
```

## After DB Restore

Once the full DB is restored and verified, clean up temp files to reclaim space:

```bash
rm -f /tmp/skills-hub-restored.db /tmp/skills-hub-restored.db.gz /tmp/skills-hub-full.db.gz
```

## Minimum Space Needed for Recovery

- GDrive download + decompress: ~720MB (185MB .gz + ~520MB decompressed)
- Pipe approach (rclone cat | gunzip): ~520MB (decompressed only)
- Local .gz restore: ~520MB (no download needed)
- .bak restore (skills-only): ~5MB (fast, no CVE data)