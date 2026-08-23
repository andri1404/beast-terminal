# mwapi.dev Provider (TongKhoKr)

Source: `https://api.mwapi.dev` — Claude API proxy, install script at `https://api.mwapi.dev/install.sh?key=<key>`.

## Credentials

- **Base URL:** `https://api.mwapi.dev/v1`
- **API Key:** `sk-ddc99b1396aa742acd3a0732c0a3982115384bf1a59beee81f16f26a99bc2e1b`
- **Auth:** Bearer token (OpenAI-compatible)
- **9Router prefix:** `mw`

## Available Models (7 Claude models)

| Model ID | Display Name | Type |
|---|---|---|
| `claude-opus-5` | Claude Opus 5 | Anthropic flagship |
| `claude-opus-4-8` | Claude Opus 4.8 | |
| `claude-opus-4-7` | Claude Opus 4.7 | |
| `claude-opus-4-6` | Claude Opus 4.6 | |
| `claude-sonnet-5` | Claude Sonnet 5 | Balanced |
| `claude-sonnet-4-6` | Claude Sonnet 4.6 | |
| `claude-haiku-4-5-20251001` | Claude Haiku 4.5 | Fast/light |

## Verification

```bash
# List models
curl -s "https://api.mwapi.dev/v1/models" \
  -H "Authorization: Bearer sk-ddc99b1396aa742acd3a0732c0a3982115384bf1a59beee81f16f26a99bc2e1b"

# Chat test
curl -s "https://api.mwapi.dev/v1/chat/completions" \
  -H "Authorization: Bearer sk-ddc99b1396aa742acd3a0732c0a3982115384bf1a59beee81f16f26a99bc2e1b" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-5","messages":[{"role":"user","content":"say hi in 3 words"}],"max_tokens":20}'
```

## 9Router Model IDs

Two formats, both valid for chat:

- **Short:** `mw/claude-sonnet-5`, `mw/claude-opus-5`, etc.
- **Long (auto-discovered):** `openai-compatible-chat-<uuid>/claude-sonnet-5`

Only the long format appears in `/v1/models`. Both work for `/v1/chat/completions`.

## Usage Notes

- All models are Claude (Anthropic) — strictest censorship tier. NOT suitable for pentest recon prompts.
- Response format: standard JSON (not SSE streaming for single-turn with `max_tokens`).
- Prompt tokens: Claude Opus 5 uses ~7,400 prompt tokens even for trivial "hi" prompts (system prompt overhead).
- Installed: 2026-08-10. Working at time of install.