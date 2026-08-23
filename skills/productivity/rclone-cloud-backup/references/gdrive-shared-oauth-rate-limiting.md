# GDrive Shared OAuth Client Rate Limiting (2026-08-09)

## Context

Syncing `~/.hermes/omop-skills/` (304 MB, 24,084 files, 21,692 dirs) to `gdrive:hermes-backup/omop-skills/` using the default rclone OAuth client.

## The Problem

The default rclone GDrive client ID `202264815644.apps.googleusercontent.com` is shared by all rclone users globally. When global usage is high, GDrive API returns 403 rate-limit errors even for moderate operations.

### Error Transcript

```
Error 403: Quota exceeded for quota metric 'Queries' and limit 'Queries per minute'
of service 'drive.googleapis.com' for consumer 'project_number:202264815644'.
Details:
[
  {
    "@type": "type.googleapis.com/google.rpc.ErrorInfo",
    "domain": "googleapis.com",
    "metadata": {
      "consumer": "projects/202264815644",
      "quota_limit": "defaultPerMinutePerProject",
      "quota_limit_value": "840000",
      "quota_location": "global",
      "quota_metric": "drive.googleapis.com/default",
      "quota_unit": "1/min/{project}",
      "service": "drive.googleapis.com"
    },
    "reason": "RATE_LIMIT_EXCEEDED"
  }
]
, rateLimitExceeded
```

## Failed Approaches

| Approach | Flags | Result |
|----------|-------|--------|
| `rclone sync` | `--fast-list --transfers 8` | Timed out 600s |
| `rclone sync` | `--fast-list --transfers 4 --checkers 4` | 403 after 46s, listed 66K items |
| `rclone copy` | `--fast-list --transfers 2 --checkers 1 --tpslimit 2 --tpslimit-burst 2` | 403 after 60s, attempt 2/3 |
| `rclone copy` | `--no-traverse --ignore-existing --transfers 2 --checkers 1 --tpslimit 1` | 403 after 30s, listed 32K items |
| `rclone copy` | `--fast-list --transfers 1 --checkers 1 --tpslimit 0.5` | 403 after 46s, listed 66K items |
| `rclone copy` | `--transfers 1 --checkers 1 --tpslimit 1` (no --fast-list) | 403 after 49s, listed 57K items |

**Key insight:** `--tpslimit` doesn't throttle `--fast-list` bulk listing calls. Even without `--fast-list`, paginated listing was making ~1,183 API calls/sec — far exceeding the shared quota.

## Working Approach

```bash
rclone copy ~/.hermes/omop-skills/ gdrive:hermes-backup/omop-skills/ \
  --transfers 1 --checkers 1 --tpslimit 1 --tpslimit-burst 1 \
  --drive-list-chunk 10 --drive-chunk-size 16M --retries 2
```

**Why it works:**
- `--drive-list-chunk 10`: Only 10 items per API page — tiny, stays under quota
- `--tpslimit 1 --tpslimit-burst 1`: 1 API call per second
- Combined: ~10 items listed per second, ~300-600 items per minute
- No `--fast-list`: Uses paginated listing that respects `--tpslimit`

**Performance:** 20,512 items listed after 5 minutes. With 45,776 total items (files + dirs), listing alone takes ~2.5 hours. Uploads follow.

## Permanent Fix

Create a custom GCP project:
1. Go to Google Cloud Console → APIs & Services → Enable Drive API
2. Create OAuth 2.0 Client ID (Desktop application)
3. Configure rclone: `rclone config` → edit gdrive remote → enter custom `client_id` and `client_secret`
4. With a custom client, `--tpslimit 10` is safe and `--fast-list` works normally

## Session Outcome

- `~/.hermes/skills/` sync: **Completed** (no changes)
- `~/.hermes/omop-skills/` sync: **Running in background** with `--drive-list-chunk 10 --tpslimit 1` (~2.5h ETA for listing)