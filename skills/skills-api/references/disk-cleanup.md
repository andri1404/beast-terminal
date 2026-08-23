# Disk Space Management

## Current State (2026-08-08)

| Item | Size | Action |
|---|---|---|
| cvelistV5 raw repo | 4.1G | Deleted (saves 4.1G) |
| cve.db (SQLite) | 188M | Keep (needed by API) |
| omop-skills | 304M | Keep (API primary storage) |
| hermes-agent | 842M | Keep (core binary) |
| skills-api | 25M | Keep (API server) |
| logs | 13M | Rotate periodically |

## Cleanup Commands

```bash
# Delete CVE raw repo (after DB is built)
rm -rf /home/ubuntu/cve-db/cvelistV5

# Truncate large logs
find ~/.hermes/logs -name "*.log" -size +1M -exec truncate -s 0 {} \;

# Check disk usage
du -sh /home/ubuntu/cve-db/ /home/ubuntu/.hermes/omop-skills/ /home/ubuntu/.hermes/logs/
df -h /
```

## CVE Update Script Fix

The `update_cve.sh` at `/home/ubuntu/cve-db/update_cve.sh` depends on `cvelistV5/` repo.
If the repo was deleted to save space, the script needs to be updated to re-clone on demand:

```bash
#!/bin/bash
# Alternative: clone fresh each time, delete after build
set -e
CVE_DIR="/home/ubuntu/cve-db"
REPO_DIR="$CVE_DIR/cvelistV5"

# Clone if missing
if [ ! -d "$REPO_DIR" ]; then
    git clone --depth 1 https://github.com/CVEProject/cvelistV5.git "$REPO_DIR"
fi

cd "$REPO_DIR"
git fetch --depth 1 origin main
git reset --hard origin/main

cd "$CVE_DIR"
python3 build_db.py

# Clean up to save space
rm -rf "$REPO_DIR"
```

This saves 4.1G between updates but adds ~2-5 min to each update cycle for the clone.