# Capsolver API Reference

## Turnstile Solving

**Task type:** `AntiTurnstileTaskProxyLess` (no proxy needed)

**Endpoints:**
- `POST https://api.capsolver.com/createTask`
- `POST https://api.capsolver.com/getTaskResult`

**Required parameters:**
- `websiteURL` — The full URL of the page with the Turnstile challenge
- `websiteKey` — The Turnstile site key (e.g., `0x4AAAAAADBuC8Knz1EJZx9-`)

**Python example:**
```python
import requests, time

def solve_turnstile(api_key, site_key, page_url):
    resp = requests.post("https://api.capsolver.com/createTask", json={
        "clientKey": api_key,
        "task": {
            "type": "AntiTurnstileTaskProxyLess",
            "websiteURL": page_url,
            "websiteKey": site_key,
        }
    })
    task_id = resp.json()["taskId"]
    
    for i in range(30):
        time.sleep(1.5)
        result = requests.post("https://api.capsolver.com/getTaskResult", json={
            "clientKey": api_key, "taskId": task_id
        }).json()
        if result.get("status") == "ready":
            return result["solution"]["token"]
        elif result.get("status") == "failed":
            return None
    return None
```

**Response format:**
```json
{
  "errorId": 0,
  "taskId": "...",
  "status": "ready",
  "solution": {
    "token": "1.xxx...",
    "type": "turnstile",
    "userAgent": "Mozilla/5.0..."
  }
}
```

**Token usage:** Inject into `<input name="cf-turnstile-response">` on the page.

**Timing:** Solve time 2-10 seconds. Token valid for ~30-60 seconds. Inject immediately.
**Success rate:** ~70% for server-side validated Turnstile (Cloudflare managed mode). Varies by IP reputation.

**Token format:** 800-880 chars, starts with `1.`

## Error Codes
- `ERROR_INVALID_TASK_DATA` — Invalid site key or URL format
- `ERROR_CAPTCHA_SOLVE_FAILED` / `timeout` — Turnstile too hard, retry
- `ERROR_KEY_DOES_NOT_EXIST` — Invalid API key

## SDK
- `pip install capsolver` (official Python SDK)
- `capsolver.solve({...})` — one-shot solve