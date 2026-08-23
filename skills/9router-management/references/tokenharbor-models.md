# TokenHarbor Model Catalog (via 9Router)

TokenHarbor provider: `openai-compatible-chat-bcac984e-9619-462a-aead-d9337c9814d7`
Base URL: `https://tokenharbor.ai/v1`
Custom prefix: `th/`
API keys: 5 keys load-balanced across 5 provider connections

## Model Test Results (2026-08-10)

Tested with prompt "Say hi in 1 sentence", max_tokens=200, temperature=0.7.

### ✅ Working (18/21)

| # | Model ID | Display Name | Time | Tokens (in/out) | Notes |
|---|----------|-------------|------|-----------------|-------|
| 1 | `th/th-orchestra` | Orchestra | 0.6s | 61/40 | MiMo-based orchestrator |
| 2 | `th/claude-sonnet-5` | Claude Sonnet 5 | 2.6s | 7/4 | Fast response |
| 3 | `th/claude-opus-5` | Claude Opus 5 | 3.7s | 7/37 | Verbose, helpful |
| 4 | `th/kimi-k3` | Kimi K3 | 0.4s | 91/62 | Very fast |
| 5 | `th/mimo-v2.5-pro` | Mimo v2.5 Pro | 0.6s | 65/49 | Xiaomi MiMo |
| 6 | `th/mimo-v2.5` | Mimo v2.5 | 0.4s | 61/40 | Xiaomi MiMo |
| 7 | `th/deepseek-v4-pro` | DeepSeek v4 Pro | 0.4s | 10/50 | Reasoning model |
| 8 | `th/deepseek-v4-flash` | DeepSeek v4 Flash | 0.4s | 89/46 | Reasoning model |
| 9 | `th/claude-fable-5` | Claude Fable 5 | 3.6s | 17/15 | Creative writing |
| 10 | `th/gemini-3.1-pro-preview` | Gemini 3.1 Pro | 0.4s | 640/319 | High token usage |
| 11 | `th/qwen3.8-max` | Qwen 3.8 Max | 0.4s | 54/30 | Alibaba |
| 12 | `th/grok-4.5` | Grok 4.5 | 0.4s | 84/29 | xAI |
| 13 | `th/gpt-5.6-sol` | GPT 5.6 Sol | 9.5s | 12/6 | Slow (~9.5s) |
| 14 | `th/gpt-5.6-terra` | GPT 5.6 Terra | 3.5s | 12/6 | |
| 15 | `th/gemini-3.6-flash` | Gemini 3.6 Flash | 0.4s | 7/216 | High completion tokens |
| 16 | `th/glm-5.2` | GLM 5.2 | 7.0s | 18/257 | Empty content (reasoning only) |
| 17 | `th/minimax-m3` | MiniMax M3 | 0.4s | 182/21 | High prompt tokens |
| 18 | `th/kimi-k3:free` | Kimi K3 (FREE) 🆓 | 0.4s | 91/62 | Free tier |

### ❌ Failed (3/21)

| # | Model ID | Display Name | Error | Cause |
|---|----------|-------------|-------|-------|
| 1 | `th/gpt-5.6-luna` | GPT 5.6 Luna | 402 | "Claude and OpenAI" — payment required |
| 2 | `th/mimo-v2.5:free` | Mimo v2.5 (FREE) 🆓 | 403 | "Verify your email" — email not verified |
| 3 | `th/deepseek-v4-flash:free` | DeepSeek v4 Flash (FREE) 🆓 | 403 | "Verify your email" — email not verified |

## Response Format

TokenHarbor responses through 9Router use a **JSON+DONE hybrid format**:
- Complete JSON body with `choices[0].message.content` (non-streaming shape)
- Trailing `data: [DONE]\n\n\n\n` appended

Parse by stripping the trailing SSE marker before `json.loads`:
```python
import re, json
clean = re.sub(r'\n?data:\s*\[DONE\].*$', '', raw, flags=re.DOTALL).strip()
data = json.loads(clean)
content = data["choices"][0]["message"]["content"]
```

## Pricing Notes

- **Paid models** (💰): All models without `:free` suffix — require credit balance
- **Free models** (🆓): `kimi-k3:free`, `mimo-v2.5:free`, `deepseek-v4-flash:free` — BUT `mimo-v2.5:free` and `deepseek-v4-flash:free` require email verification
- **Credit balance**: ~$25 total across 5 accounts ($5 each)