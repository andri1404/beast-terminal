# Reusable gRPC-Web client (Python) — verified working against HFM

Reverse-engineered + exercised against `wt-proxy.mtp-hfm.com`. `config.Config/AppConfig`
returned 229KB and the full 2FA chain (`AuthEmailPwd` → `SendEmail2faOtp` → `Validate2faOtp`)
completed successfully — so the framing/protobuf/trailers code below is confirmed correct.
The only unresolved step is the account MT5 master password (see SKILL.md "LAST BLOCKER").

## gRPC-Web over HTTP/1.1 (the essentials)

- Host is an Envoy proxy. Every path returns `content-type: application/grpc`.
- Request: `POST <host>/<package.Service>/<Method>` with headers
  `Content-Type: application/grpc-web+proto`, `X-Grpc-Web: 1`, `X-User-Agent: grpc-web-javascript/0.1`.
  Custom metadata is sent as lowercase HTTP headers (e.g. `device-id`, `authentication: Bearer <tok>`).
- Request body = `\x00` (flag) + `u32be(len(msg))` + protobuf `msg`. (5-byte length prefix.)
- Response body = a stream of 5-byte-prefixed frames: data frames flag `0x00`, **trailers frame flag `0x80`**.
  `grpc-status` / `grpc-message` live in the TRAILERS FRAME (text `grpc-status:N\r\ngrpc-message:...\r\n`),
  NOT in HTTP headers over HTTP/1.1. This is the #1 gotcha — checking `r.headers` makes every
  successful call look like `grpc-status "?"`.

## Core helpers

```python
import struct

def varint(n):
    o = bytearray()
    while True:
        b = n & 0x7F; n >>= 7
        o.append(b | 0x80 if n else b)
        if not n: return bytes(o)

def field_varint(f, v): return varint((f << 3) | 0) + varint(v)          # wire type 0
def field_bytes(f, v):                                                  # wire type 2 (len-delimited)
    v = v.encode() if isinstance(v, str) else v
    return varint((f << 3) | 2) + varint(len(v)) + v
def field_fixed64(f, d): return varint((f << 3) | 1) + struct.pack("<d", d)  # wire type 1

def frame(msg): return b"\x00" + struct.pack(">I", len(msg)) + msg

def read_varint(buf, i):
    r = 0; s = 0
    while True:
        b = buf[i]; i += 1
        r |= (b & 0x7F) << s
        if not (b & 0x80): return r, i
        s += 7

def decode(payload):  # naive field decoder -> {field_num: value}
    out = {}; i = 0
    while i < len(payload):
        tag, i = read_varint(payload, i)
        f, wt = tag >> 3, tag & 7
        if wt == 2:
            ln, i = read_varint(payload, i)
            raw = payload[i:i+ln]; i += ln
            try: out[f] = raw.decode()
            except Exception: out[f] = raw.hex()          # nested message / binary -> hex
        elif wt == 0:
            v, i = read_varint(payload, i); out[f] = v
        elif wt == 1:
            out[f] = struct.unpack("<d", payload[i:i+8])[0]; i += 8
        elif wt == 5:
            i += 4
        else:
            break
    return out

def parse_response(r):
    """Return (grpc_status, grpc_message, first_data_frame_payload)."""
    data = r.content
    status = r.headers.get("grpc-status")     # usually None over HTTP/1.1
    msg = r.headers.get("grpc-message", "")
    dp = None; i = 0
    while i + 5 <= len(data):
        fl = data[i]; ln = struct.unpack(">I", data[i+1:i+5])[0]
        pl = data[i+5:i+5+ln]; i += 5 + ln
        if fl & 0x80:                          # trailers
            for line in pl.decode(errors="replace").split("\r\n"):
                if line.startswith("grpc-status:"): status = line.split(":",1)[1].strip()
                elif line.startswith("grpc-message:"): msg = line.split(":",1)[1].strip()
        elif dp is None:
            dp = pl                             # first data frame
    return status, msg, dp
```

## Reverse-engineering recipe (how the schemas were recovered)

1. Fetch the SPA page, find the RSC payload key `envoyUrl` (the gRPC-Web host).
2. Download `/_next/static/chunks/*.js` (proxy + curl_cffi `impersonate="chrome"`; some chunks block stochastically — retry).
3. `grep -oE '"/[a-z_]+\.[A-Za-z.]+/[A-Z][A-Za-z]+"'` → the full method-path list.
4. `grep 'MethodDescriptor'` → request/response type per method.
5. `grep '<Message>.toObject=function'` → field name → field number → wire-type map.
6. Auth: `grep 'authentication'` in the bundle → the metadata header name + `Bearer` semantics.

## HFM-specific facts (from this reversal)

- Host `wt-proxy.mtp-hfm.com`, services: `pricing.Pricing` (TicksStream/CandleStream/CandlesData/SymbolsData),
  `session.Session` (AuthEmailPwd/AuthAccount/AuthAccountPwd/RefreshAccountToken/Validate2faOtp/SendEmail2faOtp),
  `trading.Trading` (OpenTrade/CloseTrade/GetAccountData/...), `config.Config`, `event.Event`, `price_alerts.PriceAlerts`.
- Metadata (account mode): `device-id:web`, `authentication:Bearer <accountAuth>`, `account:<id>`, `is-testing:false`.
  Wallet mode: `authentication:Bearer <walletToken>` + `wallet:<id>`. `AuthEmailPwd` itself needs `device-id:web` (else `No device ID present`).
- Full proto field maps are in SKILL.md; the working scripts live in `trading/hfm_*.py`.
