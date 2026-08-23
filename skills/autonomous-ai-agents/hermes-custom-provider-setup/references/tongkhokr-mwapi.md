# TongKhoKr / mwapi gateway — worked example

The TongKhoKr proxied-Claude setup (install script host `api.mwapi.dev`).
This is the concrete case that spawned the `hermes-custom-provider-setup`
skill. It's a **third-party Claude proxy** — Anthropic-compatible wire
protocol (`/v1/messages`).

## What the TongKhoKr install script does (outside Hermes)

`curl -fsSL "https://api.mwapi.dev/install.sh?key=KEY" | bash` is a Claude
Code gateway configurator. It sets:
- `ANTHROPIC_BASE_URL=https://api.mwapi.dev`
- `ANTHROPIC_AUTH_TOKEN=<key>`
- Model env vars, e.g. `ANTHROPIC_DEFAULT_OPUS_MODEL=claude-opus-5`,
  `ANTHROPIC_DEFAULT_SONNET_MODEL=claude-sonnet-5`,
  `ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-haiku-4-5-20251001`
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`,
  `CLAUDE_CODE_ATTRIBUTION_HEADER=0`

It writes these to `~/.bashrc`/`~/.zshrc` and `~/.claude/settings.json`
(creating backups first). Uninstall: `curl -fsSL
"https://api.mwapi.dev/install.sh" | bash -s -- --uninstall`.

Model tiers offered (default = first):
- Opus: `claude-opus-5`, `claude-opus-5[1m]`, `claude-opus-4-8`, `claude-opus-4-8[1m]`
- Sonnet: `claude-sonnet-5`, `claude-sonnet-5[1m]`, `claude-sonnet-4-6`
- Haiku: `claude-haiku-4-5-20251001` (single, not offered)

In non-interactive shells the script auto-picks option 1 (default models)
since `/dev/tty` is unavailable — fine for headless install.

## Wiring it into Hermes (must use named `providers:` block + `models:`)

```bash
hermes config set providers.mwapi.base_url https://api.mwapi.dev
hermes config set providers.mwapi.api_key sk-...
hermes config set providers.mwapi.transport anthropic_messages
hermes config set providers.mwapi.provider_type custom

# CRITICAL: declare models to bypass the /models probe (Anthropic proxies don't expose it)
hermes config set providers.mwapi.models.claude-sonnet-5.model claude-sonnet-5
hermes config set providers.mwapi.models.claude-opus-5.model claude-opus-5
hermes config set providers.mwapi.models.claude-haiku-4-5-20251001.model claude-haiku-4-5-20251001

hermes config set model.aliases.tong-opus5   mwapi/claude-opus-5
hermes config set model.aliases.tong-sonnet5 mwapi/claude-sonnet-5
hermes config set model.aliases.tong-haiku   mwapi/claude-haiku-4-5-20251001
```

## The failures this teaches (4 iterations to working)

### Failure 1: full-form model_aliases with api_key
First attempt used full-form `model_aliases:` entries with `base_url` +
`api_key`. The switch reported `Model switched to tong-sonnet5` / `Provider:
Custom endpoint` but then `⚠️ The model provider failed after retries`.
Root cause: `DirectAlias` drops `api_key`, so the request went to
`api.mwapi.dev` with the **current provider's (tokenrouter) key** → auth
failure.

### Failure 2: named provider without models declaration
Second attempt used a named `providers.mwapi` block with `api_key` + short-form
alias `mwapi/claude-sonnet-5`. The alias resolved correctly (provider=mwapi,
base_url=mwapi.dev, api_key=mwapi key), but the switch STILL failed with:
`Note: could not reach this custom endpoint's model listing at https://api.mwapi.dev/models`.
Root cause: `validate_requested_model` (model_switch.py line 1692) probes the
`/models` endpoint. Anthropic proxies don't expose this — the probe fails,
validation returns `accepted: false`, and the switch is rejected. Fix: add
`models:` to the provider block, which triggers the override at line 1709-1743
and skips the live probe entirely.

### Failure 3: using provider=custom in the alias (provider_changed=false)
When the alias resolves to `provider: custom` (same as current provider),
`provider_changed` is False and `switch_model` takes the `else` branch (line
1643) which resolves credentials from the default custom provider pool — NOT
the named provider's api_key. Using a distinct slug (`mwapi`) triggers
`provider_changed=true`, which forces the named provider's credential
resolution. The short-form alias `mwapi/claude-sonnet-5` is correct because it
resolves to `provider=mwapi` (not `custom`).

### Failure 4: missing `anthropic` Python package
After all config is correct, the switch fails with:
`Error: Model switch to claude-sonnet-5 failed (The 'anthropic' package is required for the Anthropic provider. Install it with: pip install 'anthropic>=0.39.0')`
Root cause: Hermes uses the `anthropic` SDK to communicate with
Anthropic-compatible endpoints (`transport: anthropic_messages`). If the
package isn't installed in the Hermes venv, the switch is rejected at the agent
level before any API call is made. Fix:
```bash
# Hermes venv is typically at /usr/local/lib/hermes-agent/venv/ (root-owned)
# If permission denied, chown first:
sudo chown -R $USER:$USER /usr/local/lib/hermes-agent/venv/lib/python3.11/site-packages/
/usr/local/lib/hermes-agent/venv/bin/pip install 'anthropic>=0.39.0'
```
Verify: `ls /usr/local/lib/hermes-agent/venv/lib/python3.11/site-packages/anthropic/`

### Final working config
```yaml
model:
  aliases:
    tong-sonnet5: mwapi/claude-sonnet-5
providers:
  mwapi:
    base_url: https://api.mwapi.dev
    api_key: sk-...
    transport: anthropic_messages
    models:
      claude-sonnet-5: {model: claude-sonnet-5}
      claude-opus-5: {model: claude-opus-5}
      claude-haiku-4-5-20251001: {model: claude-haiku-4-5-20251001}
```

## Live verification (Anthropic-compatible)

```bash
curl -s -X POST "https://api.mwapi.dev/v1/messages" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-sonnet-5","max_tokens":50,"messages":[{"role":"user","content":"OK"}]}'
```

## Behavioral note

The gateway's model self-identifies as "Kiro — an AI-powered development
environment, not Claude" and refuses identity-impersonation instructions. That
is prompt injection from the gateway's own system prompt, not a real model
change. Flag it to the user as expected behavior for third-party proxies.