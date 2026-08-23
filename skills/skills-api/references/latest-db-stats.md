# Latest DB Stats (2026-08-23)

Verified from live `skills-hub.db` during cron backup sync:

```
integrity: ok
skills: 19,374
cves: 379,857
exploits: 25,026
db_size_mb: 522
state_db_mb: 268 (raw) → 99 (gz)
```

The GDrive backup at `gdrive:hermes-backup/skills-hub-full.db.gz` (177 MB compressed → 522 MB decompressed) is the canonical snapshot. Download via `rclone copyto`.

## Previous snapshots

- 2026-08-23 (08:00 UTC): 379,857 CVEs, 25,026 exploits, 522MB (cron backup — current)
- 2026-08-23 (earlier): 379,852 CVEs, 25,026 exploits, 522MB (cron backup)
- 2026-08-20: 374,319 CVEs, 25,012 exploits, 513.8MB (GDrive restore)
- 2026-08-18: 378,442 CVEs, 25,020 exploits (after NVD sync, later lost)
- 2026-08-17: 374,319 CVEs, 25,012 exploits (GDrive canonical)
- 2026-08-14: 374,319 CVEs, 25,012 exploits

The GDrive backup at `gdrive:hermes-backup/skills-hub-full.db.gz` is the canonical snapshot. As of 2026-08-23, the DB has grown to 522MB with 379,857 CVEs — NVD API incremental syncs are adding CVEs steadily.

## DB stripped incident (2026-08-20)

The DB was found stripped (0 skills, 0 CVEs, 84KB empty shell). Restored from GDrive in ~15s download + 2s decompress. Root cause: unknown — the DB tables existed but all rows were deleted. The watchdog's `check_cve_count()` (min 50,000) would have caught this, but the watchdog script itself can't run from within gateway cron sessions (lifecycle guard blocks it). The manual recovery via `execute_code` worked perfectly.