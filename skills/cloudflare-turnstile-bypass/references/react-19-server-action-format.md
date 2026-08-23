# React 19 / Next.js Server Action Wire Format

Discovered during TokenHarbor mass registration research. This is the #1 reason curl-based Next.js form submissions fail.

## The Problem

Next.js 15+ uses React 19 server actions. The wire format is NOT the plain field names visible in the HTML or `FormData`. All fields are prefixed with `1_` and there's an extra `0` field.

## The Wire Format (captured from browser fetch interceptor)

```json
{
  "0": "[\"$undefined\",\"$K1\"]",
  "1_$ACTION_REF_1": "",
  "1_$ACTION_1:0": "{\"id\":\"ACTION_ID\",\"bound\":\"$@1\"}",
  "1_$ACTION_1:1": "[\"$undefined\"]",
  "1_$ACTION_KEY": "kb59e6b88b9f36883e58e38e7e48870c6",
  "1_device_fingerprint": "uuid-here",
  "1_timezone": "Asia/Shanghai",
  "1_next": "",
  "1_cf-turnstile-response": "TURNSTILE_TOKEN",
  "1_email": "user@example.com",
  "1_password": "Password123!",
  "1_invite_code": "CODE"
}
```

## Required Headers

```python
headers = {
    "Accept": "text/x-component",
    "next-action": "ACTION_ID",           # lowercase! NOT "Next-Action"
    "next-router-state-tree": "%5B%22%22%2C%7B%22children%22%3A...",
    "x-deployment-id": "dpl_...",
    "Content-Type": "application/json",    # JSON, NOT multipart/form-data
}
```

## Error Responses

| Error | Meaning |
|-------|---------|
| `"Bot check failed" / needCaptcha:true` | Turnstile token missing/invalid |
| `"Something went wrong creating your account"` | Format accepted, but account creation failed (email, rate limit, etc.) |
| 404 HTML page | Missing `1_` prefix or wrong Content-Type |

## How to Capture

Intercept `fetch` in the browser console before submitting the form:

```javascript
const origFetch = window.fetch;
window.fetch = async function(...args) {
  const req = {url: args[0]?.url || args[0], method: args[1]?.method, headers: {}, body: null};
  if (args[1]?.headers instanceof Headers) args[1].headers.forEach((v,k) => req.headers[k]=v);
  if (args[1]?.body instanceof FormData) {
    req.body = {}; args[1].body.forEach((v,k) => req.body[k]=v);
  }
  console.log(JSON.stringify(req, null, 2));
  return origFetch.apply(this, arguments);
};
```

## Key Insight

The `$ACTION_1:1` field in the HTML is always `["$undefined"]` — a React placeholder, NOT the actual field value. The REAL field names are the plain names (`email`, `password`, `invite_code`) but with `1_` prefix in the wire format.

The `0` field contains `["$undefined","$K1"]` — a React action reference that must be present.