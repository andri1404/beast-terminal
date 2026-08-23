# Live DB Snapshot Workaround

## Problem

`rclone copyto` on SQLite databases that Hermes is actively writing to (state.db, skills-hub.db) fails during resumable upload because the file's modification time changes mid-transfer:

```
ERROR : Attempt 1/3 failed with 1 errors and:
  can't copy - source file is being updated
  (mod time changed from 2026-08-12 02:37:38 to 2026-08-12 02:38:30)
```

This happens even with `--ignore-times` — the GDrive resumable upload API independently checks the source file's mod-time against the upload session's start time, and `--ignore-times` only affects the comparison logic, not the upload session integrity check.

## Root Cause

Hermes writes to state.db and skills-hub.db continuously (session state, skill cache, CVE data). For a 174MB state.db or 515MB skills-hub.db, the upload takes minutes — during which Hermes will inevitably write to the file, changing its mod-time.

The resumable upload protocol sends the file in chunks. Between chunks, the GDrive API validates that the source file hasn't changed. When it detects a mod-time change, it aborts with the error above.

## Workaround: Snapshot to /tmp

Copy the DB to a temporary location first, then upload from the frozen copy:

```bash
# Snapshot → upload → cleanup
cp ~/.hermes/state.db /tmp/state.db.snap
rclone copyto /tmp/state.db.snap gdrive:hermes-backup/state.db \
  --transfers 1 --no-traverse --stats 30s
rm /tmp/state.db.snap
```

The snapshot is a point-in-time copy. Even though it's slightly stale by the time the upload completes, it's a consistent, valid SQLite database (WAL mode ensures readers don't block writers).

## Secondary Benefit: Bypasses Shared OAuth Hangs

The shared OAuth client (`202264815644.apps.googleusercontent.com`) can also cause `copyto` to hang silently — zero I/O for 12+ minutes with no error:

```
read_bytes: 16384
write_bytes: 0
```

The snapshot approach also bypasses this because the file copy is local (instant) and the `rclone copyto` from /tmp/ starts fresh with a clean API session.

## Applicability

Use the snapshot method for any DB file > 10MB that Hermes writes to during operation:
- `~/.hermes/state.db` (174MB+) — ALWAYS snapshot
- `~/.hermes/skills-hub.db` (515MB+) — ALWAYS snapshot
- `~/.hermes/kanban.db` (116KB) — direct copyto is fine
- `~/.hermes/verification_evidence.db` (32KB) — direct copyto is fine