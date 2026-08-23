---
name: hermes-custom-provider-setup
description: "Use when wiring a third-party API gateway into Hermes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, provider, gateway, custom, model-alias, anthropic-compatible, openai-compatible]
    related_skills: [hermes-troubleshooting, hermes-pentest-powerup]
---

# Hermes Custom Provider Setup

How to route Hermes to a third-party LLM API gateway (a proxy that forwards
requests to upstream models). Common examples: tokenrouter.com, 9router,
qoder.com, TongKhoKr-style proxied Claude gateways, one-api / new-api panels.

## The #1 Pitfall: full-form `model_aliases` IGNORE api_key

The most common failure. A full-form alias entry with `base_url` AND `api_key`
does NOT carry the api_key to the request:

```yaml
# ❌ DOES NOT WORK — api_key is silently dropped
model_aliases:
  tong-sonnet5:
    model: claude-sonnet-5
    provider: custom
    base_url: https://api.mwapi.dev
    api_key: sk-XXXX            # <-- ignored!
```

`DirectAlias` in `hermes_cli/model_switch.py` only holds `model`, `provider`,
`base_url`. When the alias overrides `base_url`, api_key falls back to the
**current provider's key** (e.g. tokenrouter's key), so the new gateway gets the
wrong credential and fails after retries. Symptom: `Model switched to X` then
`⚠️ The model provider failed after retries`; gateway logs show auth failure.

## The Correct Pattern: named `providers:` block + short-form alias + `models:` declaration

Give the gateway its own named provider block carrying the key, then point
aliases at it with the short `provider/model` form. **CRITICAL: also declare
`models:` in the provider block.** Without this, `validate_requested_model`
probes the `/models` endpoint (which Anthropic proxies don't expose), gets
`accepted: false`, and the switch fails with a model-listing error even though
auth and base_url are correct. The `models:` declaration triggers the override
at `switch_model` line 1709-1743, skipping the live probe.

```bash
# 1. Named provider block (config.yaml `providers:` section)
hermes config set providers.mwapi.base_url https://api.mwapi.dev
hermes config set providers.mwapi.api_key sk-XXXX
# transport: anthropic_messages for Anthropic-compatible (/v1/messages),
#            openai_compatible for OpenAI-compatible (/v1/chat/completions)
hermes config set providers.mwapi.transport anthropic_messages
hermes config set providers.mwapi.provider_type custom

# 2. CRITICAL: declare models so the /models probe is bypassed
hermes config set providers.mwapi.models.claude-sonnet-5.model claude-sonnet-5
hermes config set providers.mwapi.models.claude-opus-5.model claude-opus-5
hermes config set providers.mwapi.models.claude-haiku-4-5-20251001.model claude-haiku-4-5-20251001

# 3. Short-form aliases referencing the named provider
hermes config set model.aliases.tong-sonnet5 mwapi/claude-sonnet-5
hermes config set model.aliases.tong-opus5   mwapi/claude-opus-5
hermes config set model.aliases.tong-haiku   mwapi/claude-haiku-4-5-20251001
```

Resulting config:
```yaml
model:
  aliases:
    tong-sonnet5: mwapi/claude-sonnet-5
providers:
  mwapi:
    base_url: https://api.mwapi.dev
    api_key: sk-XXXX
    transport: anthropic_messages
    provider_type: custom
    models:
      claude-sonnet-5:
        model: claude-sonnet-5
      claude-opus-5:
        model: claude-opus-5
      claude-haiku-4-5-20251001:
        model: claude-haiku-4-5-20251001
```

## Config key facts (from hermes_cli source)

- Top-level `model_aliases:` = dict-based format, each entry is `{model,
  provider, base_url}`. **No api_key field is read.**
- `model.aliases:` (set via `hermes config set model.aliases.xxx`) = short form
  `provider/model` strings, converted to DirectAlias at load. Provider is parsed
  from the `/` prefix; if no slash, the current provider is used.
- `providers:` named blocks are normalized by
  `_normalize_custom_provider_entry` — accepted keys: `name`, `api`, `url`,
  `base_url`, `api_key`, `key_env`/`api_key_env`, `api_mode`, `transport`,
  `model`, `context_length`, etc. If the block has a literal `api_key`, that key
  is used directly (no env lookup needed).
- Alias resolution order: direct aliases (builtin + user) FIRST, then catalog.
  Aliases win over the global `model.base_url`.

## Verify before telling the user it works

Always confirm the switch resolves the RIGHT base_url + api_key + api_mode:

```bash
cd ~/.hermes/hermes-agent && HERMES_HOME=~/.hermes python3 -c "
from hermes_cli.model_switch import _ensure_direct_aliases, DIRECT_ALIASES, resolve_alias
_ensure_direct_aliases()
da = DIRECT_ALIASES.get('tong-sonnet5')
print('alias:', da)
print('resolved:', resolve_alias('tong-sonnet5', 'custom'))
"
```

Then a live end-to-end check (Anthropic-compatible):
```bash
curl -s -X POST "$BASE/v1/messages" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-sonnet-5","max_tokens":50,"messages":[{"role":"user","content":"OK"}]}'
```

## Pitfalls

- **`hermes config set model_aliases.*` warns** — the CLI flags `model_aliases`
  as "not a recognized config key" and suggests `model_catalog`. That's a
  red herring for this use case; the dict-form `model_aliases` IS read by
  model_switch.py. But since it can't carry api_key, prefer the named
  `providers:` block approach anyway.
- **`models:` declaration is MANDATORY for Anthropic proxies.** Without it,
  `validate_requested_model` (model_switch.py line 1692) probes the `/models`
  endpoint. Anthropic-compatible proxies don't expose `/models` or
  `/v1/models` — the probe fails, validation returns `accepted: false`, and the
  switch rejects the model. The `models:` block triggers the override at line
  1709-1743, skipping the live probe. Even if auth and base_url are correct,
  the switch fails with a model-listing error without this step.
- **Use a DIFFERENT provider slug than `custom`.** When the alias resolves to
  `provider: custom` (same as the current provider), `provider_changed` is
  False and the `switch_model` code takes the `else` branch (line 1643) which
  calls `resolve_runtime_provider(requested=current_provider)` — this
  resolves the default custom provider's key (e.g. tokenrouter), NOT the named
  provider's key. Using a distinct slug (e.g. `mwapi`) triggers
  `provider_changed=true`, which forces credential resolution from the named
  provider block's `api_key`.
- **transport matters.** Anthropic generic gateways expose `/v1/messages`
  (use `anthropic_messages`); OpenAI-compatible ones expose
  `/v1/chat/completions` (use `openai_compatible`). Wrong transport = 400s on
  tools even when auth succeeds.
- **`anthropic` Python package must be installed in the Hermes venv.** When
  `transport: anthropic_messages`, the agent SDK requires the `anthropic`
  package. If missing, the switch fails with `The 'anthropic' package is
  required`. Install: `/usr/local/lib/hermes-agent/venv/bin/pip install
  'anthropic>=0.39.0'`. If the venv is root-owned, `sudo chown -R $USER:$USER`
  the `site-packages/` directory first.
- **Third-party proxies may inject identity text.** A proxied Claude gateway
  may have its own system prompt ("I'm X, not Claude"). Don't trust the
  model's self-claimed identity — it's prompt injection from the gateway, not
  an actual model change.
- Per-session switch: `/model <alias>`. Persist default: `hermes config set
  model.default <alias>`.

See `references/tongkhokr-mwapi.md` for the TongKhoKr/mwapi example.