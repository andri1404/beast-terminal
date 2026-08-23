# Cron no_agent Script Timeout — Diagnostic & Fix

## Symptom
Cron job with `no_agent: true` + `script: <path>` fails with:
```
Script exited with code 1 stderr: Traceback (most recent call last):
  File "<script>", line N, in <module>
    main()
```
But the script runs fine when executed manually with a longer timeout.

## Root Cause
Hermes cron runner has a **~30s default timeout** for `no_agent` scripts. Scripts that make multiple network calls (gRPC, HTTP, API) can exceed this intermittently when the network/proxy is slow.

## Diagnostic Flow

### 1. Confirm it's a timeout, not a logic error
Run the script manually with a generous timeout:
```bash
timeout 120 python3 /path/to/script.py 2>&1; echo "EXIT: $?"
```
- Exit code 124 = timed out (script works but needs more time)
- Exit code 1 = real error (check traceback)

### 2. Isolate slow components
For multi-step scripts, time each network call individually:

```python
import time
t0 = time.time()
# ... single call ...
print(f"Call took {time.time()-t0:.1f}s")
```

### 3. Check proxy/token health
If the script uses a proxy:
```bash
python3 -c "
from curl_cffi import requests as cr
t0 = time.time()
s = cr.Session(impersonate='chrome', proxy='$PROXY', timeout=10, verify=False)
r = s.get('$HOST/')
print(f'OK: {r.status_code} in {time.time()-t0:.1f}s')
"
```

If the script uses JWT tokens:
```python
import json, time, base64
# decode JWT, check exp field
# exp - time.time() > 600  → still valid
```

### 4. Map total worst-case time
Count network calls × per-call timeout:
```
auth_refresh (20s) + 6 × candle_fetch (20s) + AI_API (120s) = 260s worst case
```
Normal execution: 15-25s. Proxy lag: 30-60s.

## Fix Options

### A. Reduce individual timeouts (recommended)
In scripts, reduce `timeout=` parameter in HTTP/gRPC calls:
```python
# Before: timeout=20
s = cr.Session(..., timeout=10, ...)  # 10s per call
```

### B. Accept intermittent failures
If the script usually completes within 30s and only fails during proxy lag, the next cron run (2m later) will likely succeed. This is acceptable for monitoring/non-critical jobs.

### C. Add internal timeout guard
```python
import signal

def handler(signum, frame):
    raise TimeoutError("Script exceeded time limit")

signal.signal(signal.SIGALRM, handler)
signal.alarm(25)  # 25s internal deadline
try:
    main()
except TimeoutError:
    print("Script timed out, will retry next cron cycle")
    sys.exit(0)
finally:
    signal.alarm(0)
```

## Real-World Example (HFM gRPC scripts)

| Script | TFs | Normal | Proxy-lag | Status |
|--------|-----|--------|-----------|--------|
| `hfm_ai_signal.py` | 6 (M1-D1) + Claude | 15-25s | 30-60s | Intermittent |
| `hfm_push_signal.py` | 6 (M1-D1) + rules | 10-20s | 30-50s | Intermittent |
| `hfm_cron_push.py` | Dashboard push | 5-10s | 15-25s | Rare |
| `hfm_collect.py` | 8 (M1-W1) + SQLite | 25-40s | 50-80s | **Routine** |

`hfm_collect.py` with 8 timeframes (including slow M30/W1) routinely exceeds 30s. Reduce `post()` timeout from 20s to 10s or accept intermittent failures.