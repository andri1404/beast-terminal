# GDrive API Behavior with Large Directory Structures

## Observed Performance (2026-08-09)

### Environment
- rclone v1.75.0, Linux 6.8.0, GDrive remote (400 GB quota, 2 GB used)
- Source: `~/.hermes/omop-skills/` — 304 MB, 24,084 files, 21,692 directories (19,412 top-level)

### Dry-Run
- `rclone sync --fast-list --transfers 8 --no-update-modtime --dry-run`
- Completed in **91 seconds**
- Listed 86,320 items, checked 21,404
- 2,696 files (19.7 MB) needed transfer

### Real Sync Attempts
1. **`rclone sync` with `--verbose`**: Started setting directory modification times immediately. ~1 dir/sec = estimated 6 hours for 21K dirs. Killed after ~10 min.
2. **`rclone sync` with `--no-update-modtime` (no verbose)**: Timed out at 600s. No output.
3. **`rclone sync` with `--use-server-modtime --no-update-modtime`**: Timed out at 600s.
4. **`rclone copy` with `--fast-list --no-traverse --no-update-modtime`**: Running for 9+ min, still in progress. Read 53 MB from source.

### Root Cause
GDrive API mandates `SetModTime` on every directory creation. `--no-update-modtime` only suppresses file mod-time updates, not directory mod-time. With 19K+ top-level directories, the first sync is bottlenecked by GDrive API directory creation calls.

### Key Discovery: `--no-traverse` + `rclone sync`
`rclone sync` **ignores** `--no-traverse` with an explicit error:
```
ERROR : Ignoring --no-traverse with sync
```
Only `rclone copy` supports `--no-traverse`.

### Stats Buffering
When stdout is not a terminal (piped, cron, background), `--stats Ns` output is fully buffered and may not appear until process completion. Monitor via `/proc/PID/io` instead.

### Working Approach (First Sync)
For first-time sync of large directories:
```bash
rclone copy src/ dest/ --fast-list --no-traverse --transfers 8 --no-update-modtime
```
For subsequent syncs (dirs already exist on remote):
```bash
rclone sync src/ dest/ --fast-list --transfers 8 --no-update-modtime
```

## Follow-up Session (2026-08-09, same day)

### State After First Sync
- Remote: 60,478 objects (many duplicates from previous syncs)
- Local: 24,084 files, 304 MB

### Failed Approaches (Remote Already Has 60K+ Objects)
1. **`rclone sync` with `--fast-list --transfers 8`**: Timed out at 600s. Listing phase reached 60,478 objects then stalled.
2. **`rclone sync` with `--fast-list --transfers 4 --tpslimit 4 --bwlimit 2M`**: Listed 86,841 objects, found 2,441 files to transfer. Transfer rate was ~2.7 KiB/s — estimated 1h48m. Killed.
3. **`rclone sync` with `--fast-list --transfers 8 --no-traverse`**: Rejected — `--no-traverse` ignored by sync.
4. **`rclone copy` with `--fast-list --transfers 8 --ignore-existing`**: Listed 60K+ objects, found duplicate notices, then stalled for 5+ minutes.
5. **`rclone copy` with `--transfers 4 --tpslimit 8 --ignore-existing --no-traverse`**: No output for 3+ minutes, killed.
6. **`rclone ls`/`rclone size`/`rclone lsd` on `gdrive:hermes-backup/omop-skills/`**: All timed out at 15-60s. Even `--max-depth 0` and `--max-depth 1` failed.

### What Worked: `--files-from` + `--ignore-existing` + `--no-traverse`

```bash
find ~/.hermes/omop-skills/ -type f > /tmp/omop_files.txt
rclone copy ~/.hermes/omop-skills/ gdrive:hermes-backup/omop-skills/ \
  --files-from /tmp/omop_files.txt --no-traverse --transfers 8 \
  --tpslimit 8 --ignore-existing --stats 30s
```

- **Exit code**: 0 (success)
- **Output**: None (all 24,084 files already existed on remote)
- **Time**: ~120 seconds
- **Why it works**: `--files-from` reads the local file list and checks each file individually against the remote. `--no-traverse` prevents a full remote tree walk. `--ignore-existing` skips files already present. No massive remote listing needed.

### Rate Limiting After Repeated Attempts
After 5+ failed sync attempts (each listing 60K+ objects), the GDrive API became unresponsive even for basic operations:
- `rclone about gdrive:` still worked (different API endpoint)
- `rclone size gdrive:hermes-backup/omop-skills/` timed out
- `rclone ls gdrive:hermes-backup/omop-skills/ --max-depth 0` timed out
- Single file `rclone copyto` still worked

This suggests per-directory rate limiting, not account-level blocking.

### Key Takeaway
For directories with 60K+ remote objects, **never use `rclone sync` or `rclone ls`** — they all require a full remote listing. Use `--files-from` + `--ignore-existing` + `--no-traverse` for verification/sync, and accept that deduplication (`rclone dedupe`) may also time out.