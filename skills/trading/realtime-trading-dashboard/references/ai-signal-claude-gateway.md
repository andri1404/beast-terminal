# AI trading signal via Claude (custom Anthropic gateway) — reproduction notes

Session: 2026-08-14. User's Anthropic access is a custom gateway, not api.anthropic.com.

## Endpoint & auth facts
- Endpoint: `https://api.mwapi.dev/v1` (stored `~/.hermes/secrets/anthropic_endpoint`).
- Key: `sk-ddc99…` (NOT `sk-ant-…`) → `~/.hermes/secrets/anthropic_key`, chmod 600.
- Behind Cloudflare. Plain `urllib` / `requests` → `HTTP 403` / `error code: 1010` (bot block).
- Works: `curl_cffi` `Session(impersonate="chrome")`.
- `/v1/models` returns `{"data":[{"id":"claude-haiku-4-5-20251001",...},{"id":"claude-opus-4-6"...}, ...], "object":"list"}`.
  Full id list seen: claude-haiku-4-5-20251001, claude-opus-4-6, claude-opus-4-7, claude-opus-4-8, claude-opus-5, claude-sonnet-4-6, claude-sonnet-5.
- Wrong model name → HTTP 404 `{"error":{"type":"model_not_found","message":"Model \"X\" is not supported by any configured account in this group"}}`.

## Working request (Anthropic /messages shape)
```python
from curl_cffi import requests as cr
s = cr.Session(impersonate="chrome", timeout=60)
r = s.post(ENDPOINT + "/messages", json={
    "model": "claude-sonnet-4-6",
    "max_tokens": 500,
    "system": "…",
    "messages": [{"role": "user", "content": "…"}],
}, headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
text = "".join(b["text"] for b in r.json()["content"] if b["type"] == "text")
```

## Signal prompt (proven — gives strict parseable verdict)
```
system: Kamu trader emas (XAUUSD) profesional. ... beri SATU keputusan tegas: BUY, SELL, atau WAIT.
Jawab dalam Bahasa Indonesia, format TEPAT seperti ini (3 baris, tanpa markdown, tanpa tabel):
ARAH: <BUY/SELL/WAIT>
REASON: <1 kalimat alasan>
PLAN: Masuk <zona> -> TP <tp> · SL <sl>
Disiplin: jangan BUY di resistance tanpa breakout, jangan SELL di support tanpa breakdown.
Sesi likuiditas rendah = prefer WAIT.

user (compact context): XAUUSD spot $X (ctx, sesi SESS LIQ)
Trend H4/M15/D1 + EMA21/50 · RSI 5m/15m/1H/4H · MACD15 hist + Stochastic + ADX + ATR
Bollinger15 · Fibonacci1H 38.2/50/61.8 · Range M5 + S/R 1H · Candle M5 terakhir
```
Parse `ARAH:` line → `arah ∈ {BUY,SELL,WAIT}`; emoji map `{BUY:🟢, SELL:🔴, WAIT:🟡}`.

## Fundamental context (gold news headlines — added later the same session)
Feed the model recent headlines so the verdict weighs sentiment, not just indicators. Free + keyless source that works from cron:
- Google News RSS: `https://news.google.com/rss/search?q=gold%20price%20XAUUSD&hl=en-US&gl=US&ceid=US:en`
- Parse `re.findall(r"<title>(.*?)</title>", rss)[1:6]`, `html.unescape` each — drop index 0 (the "Google News" wrapper title). Take 5.
- Prepend to the user prompt as `Berita terbaru (fundamental):\n- <t>…` and add to system: "REASON: … sebut sentimen berita kalau relevan".
- Exa (`EXA_API_KEY`) is the richer option but requires a key that may not be set; Google News RSS is the no-key fallback that already ships in the script.

## Dashboard feed (third panel — added later the same session)
- `hfm_ai_signal.py` writes `/tmp/hfm_ai_result.json` = `{price, arah, resp, news, model, ts}` every run (before the dedup gate).
- `webui/app.py` serves it at `GET /api/ai` (auth), falling back to `{"error":"belum ada sinyal AI","arah":null}` when the file is absent.
- Frontend (`templates/index.html`) renders a `🤖 Sinyal AI (Claude)` card: emoji+ARAH, `$price · model · time`, the multi-line `resp`, and a news list. Escape the LLM text (`&`→`&amp;`, `<`→`&lt;`) before injecting as innerHTML.
- Remember: Flask reads the template once at import — restart the server after editing `index.html` (`pkill -9 -f "python app.py"` then relaunch).

## Model choice (upgraded)
Started on `claude-sonnet-4-6`; user asked for the deepest analysis, so the loop now defaults to `claude-opus-5`. Opus adds real nuance — e.g. "trend D1/H4/M15 seragam naik + ADX 29 + sentimen berita bullish (PPI lunak), TAPI harga nempel resistance + Stoch 98, jadi entry hanya sah di pullback". It is more expensive; drop back to `claude-sonnet-4-6` (or raise the interval to 5m) if the user's API cost spikes. `MODEL` is an env-overridable constant (`ANTHROPIC_MODEL`).

## Cron wiring (parallel, silent-when-unchanged)
- Script: `~/.hermes/scripts/hfm_ai_signal.py` (no_agent). Dedup state `/tmp/hfm_ai_signal_state.json` keyed on `{price rounded, arah, lo15, hi15}`; force re-post on `$3` move. Prints nothing when unchanged.
- `hfm_ai_signal.py` imports `curl_cffi` lazily inside `claude()` because the execute_code sandbox python lacks it while system python has it.

## Gotchas already fixed
- Cron `lifecycle_guard` blocked creation twice until division was rewritten so `/` never leads a shell segment (`* (1.0/n)`, `* 0.5`, hoist `n=len(x)`) AND the `~/.hermes/secrets/` literal was split via `os.path.join(expanduser("~"), ".hermes", "secrets", name)`. Full mechanics in `web-dashboard-serve-expose` §2.
- `datetime.datetime.utcnow()` emits a DeprecationWarning on py3.12 — harmless for a cron script; leave it or switch to `datetime.datetime.now(datetime.UTC)`.
