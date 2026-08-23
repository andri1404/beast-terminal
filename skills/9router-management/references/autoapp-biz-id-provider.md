# autoapp.biz.id (bandelbanget-proxy)

External OpenAI-compatible API gateway. Similar to 9Router but hosted externally.

- **Endpoint:** `https://autoapp.biz.id/v1`
- **Auth:** Bearer token (sk-qwen-* prefix keys)
- **Owner:** `bandelbanget-proxy`

## Model List (as of 2026-08-10)

### Working (✅)
| Model | Grade | Type | min max_tokens |
|-------|-------|------|----------------|
| deepseek-v4-pro | A | Reasoning | ~2000 |
| deepseek-v4-flash | A | Reasoning | ~500 |
| deepseek-v4-mod | A | Reasoning (maps to v4-pro) | ~2000 |
| deepseek-v4-pro-b | B | Reasoning | ? |
| gpt-5.6 | A | Standard | 20 |
| gpt-5.6-luna | A | Standard | 20 |
| hy3 | A | Standard | 20 |
| kimi-k2.7-code | A | Standard | 20 |
| kimi-k2.7-code-highspeed | A | Standard | 20 |
| mimo-v2.5-pro | A | Standard | 20 |
| claude-sonnet-4.5 | B | Standard | 20 |
| glm-5.2 | A | Reasoning | ~500 |
| auto-debug | C | Debug (returns thinking in content) | 20 |

### Broken / Not Available (❌)
- `auto` — "Model tidak tersedia" (router broken)
- `grok-4.3-b` — "Model tidak tersedia"
- `claude-opus-4.8`, `claude-opus-5`, `claude-sonnet-4.6-b`, `claude-sonnet-5` — disabled
- `gpt-5.5`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna-b`, `gpt-5.6-sol-b`, `gpt-5.6-terra-b`, `gpt-5.6-sol-xhigh` — disabled
- `kimi-k3`, `mistral-large-3-675b-instruct`, `qwen3.7-max`, `qwen3.8-max`, `qwen3.8-max-b` — disabled

## Quirks

### Reasoning Models Consume Tokens on Thinking
deepseek-v4-pro, deepseek-v4-flash, deepseek-v4-mod, and glm-5.2 are reasoning models. They return `reasoning_content` in the message object and spend most tokens on thinking before emitting `content`. For short prompts, `max_tokens` must be set high:
- deepseek-v4-pro: ~270 reasoning tokens for "hi", needs ~2000 max_tokens
- deepseek-v4-flash: ~180 reasoning tokens, needs ~500 max_tokens
- deepseek-v4-mod: Maps to deepseek-v4-pro internally, same token needs
- glm-5.2: ~426 reasoning tokens, needs ~500 max_tokens

**Pitfall:** With too-low `max_tokens`, `content` comes back empty and `finish_reason` is `"length"`. The model appears broken but just needs more tokens.

### Key Expiry
Expired keys return:
```json
{"error":{"message":"Customer key expired at <ISO-date>. Please renew your subscription.","type":"invalid_request_error","code":"key_expired"}}
```

### Hermes Integration
Works as a custom provider. Reasoning models are handled correctly by Hermes's custom provider plugin (parses both `delta.content` and `delta.reasoning_content` from SSE).

```bash
hermes config set model.default deepseek-v4-pro
hermes config set model.provider custom
hermes config set model.base_url "https://autoapp.biz.id/v1"
hermes config set model.api_key "sk-qwen-..."
```

### Tested Keys
- `sk-qwen-875835177fd4299dbc2b254e58e72b6259e18e23dc63fb8b` — active as of 2026-08-10
- `sk-qwen-b309a1565bdf1923d789997ac60ae1ddd3af06f6b91a6fcc` — expired 2026-08-07