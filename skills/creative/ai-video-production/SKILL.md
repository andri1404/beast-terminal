---
name: ai-video-production
description: "Use when making AI video. Google Flow, Veo, ffmpeg."
version: 1.0.0
author: agent
tags: [video, youtube-shorts, composio, veo, gemini, nano-banana, ffmpeg, social-media]
platforms: [linux]
---

# AI Video Production Pipeline

Automated AI video generation for short-form social media (YouTube Shorts, TikTok, Reels) using Composio's Gemini integration (Veo for video, Nano Banana for images).

## Architecture Decision: Composio vs gflow-cli vs flow-py vs Gemini API

| Feature | Composio Veo 3.1 Lite | gflow-cli | flow-py | Gemini API (Official) |
|---------|----------------------|-----------|---------|----------------------|
| Model | Veo 3.1 Lite only | Veo 3.1 Lite/Fast/Quality + Omni Flash | Same as gflow-cli | Veo 3.1 Fast/Quality + Omni Flash |
| Text-to-Video | ✅ | ✅ | ✅ | ✅ |
| Image-to-Video (Ingredients) | ❌ | ✅ `gflow video r2v --ref` | ✅ `flow frames` | ✅ referenceImages |
| Character consistency | ❌ | ✅ `gflow character` | ❌ | ❌ |
| Duration | 4/6/8s | 4/6/8/10s (Omni Flash: 10s) | Same | 4/6/8/10s |
| Extend Video | ❌ | ❌ | ✅ `flow extend` | ✅ video extension |
| Upscale (free) | ❌ | ❌ | ✅ `flow upscale` (2K/4K) | ❌ |
| Camera Motion | ❌ | ❌ | ✅ `flow camera` | ❌ |
| Insert/Remove Object | ❌ | ❌ | ✅ `flow insert/remove` | ❌ |
| Scene composition | ❌ | ✅ `gflow scene create` | ❌ | ❌ |
| Movie production | ❌ | ✅ `gflow movie run` | ❌ | ❌ |
| Image generation | ✅ Nano Banana | ✅ `gflow image t2i` | ✅ `flow image` | ✅ Imagen/Nano Banana |
| reCAPTCHA | N/A (API key) | Real browser required | Real browser required | N/A (API key) |
| Auth | API key | One-time Playwright login | One-time Playwright login | **Google AI Studio API key** |
| Headless server | ✅ Works | ❌ Needs manual auth | ❌ Needs manual auth | ✅ **Works — no browser!** |
| Free tier | ❌ (paid) | Google Flow free tier | Google Flow free tier | ❌ (paid after one-time quota) |

**⚠️ CRITICAL: All Google Flow CLI tools (gflow-cli, flow-py, flow-agent, etc.) require browser-based auth. On headless servers, auth on a machine with a real display, then copy the profile. See references/gflow-cli-google-flow.md.**

**Use Composio Veo when**: headless server, simple single-clip text-to-video, need instant results.
**Use gflow-cli when**: character consistency, multi-scene stories, ingredients/reference images needed, and have a real display for one-time auth.
**Use flow-py when**: need extend, upscale, camera motion, or object insertion/removal, and have a real display for one-time auth.
**Use Gemini API (Official) when**: headless server, want official Google API (no reverse-engineering), API key auth (no browser at all), need reliable production-grade access. Best for fully automated headless bots.
**Use n8n + Gemini API when**: want workflow automation with Google Sheets/Drive/YouTube integration, visual builder UI.

## Gemini API — Official Veo Video Generation (NO BROWSER AUTH)

The **official Google Gemini API** supports Veo video generation via `predictLongRunning` endpoint. This is the ONLY approach that works on headless servers without any browser interaction.

### Auth: Google AI Studio API Key

1. Go to https://aistudio.google.com/apikey
2. Create an API key (free, no Google Cloud project needed)
3. Use `x-goog-api-key` header

### Endpoint

```bash
# Submit generation
POST https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-generate-preview:predictLongRunning
Header: x-goog-api-key: YOUR_KEY
Header: Content-Type: application/json

# Poll status
GET https://generativelanguage.googleapis.com/v1beta/{operation_name}
Header: x-goog-api-key: YOUR_KEY

# Download video (from response.generateVideoResponse.generatedSamples[0].video.uri)
GET {video_uri}
Header: x-goog-api-key: YOUR_KEY
```

### Full curl example

```bash
# 1. Submit
OPERATION=$(curl -s "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-generate-preview:predictLongRunning" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "instances": [{"prompt": "cinematic drone shot of tropical beach"}],
    "parameters": {"aspectRatio": "9:16", "durationSeconds": 8, "resolution": "720p"}
  }' | jq -r '.name')

# 2. Poll until done
while true; do
  STATUS=$(curl -s -H "x-goog-api-key: $GEMINI_API_KEY" \
    "https://generativelanguage.googleapis.com/v1beta/$OPERATION")
  DONE=$(echo "$STATUS" | jq -r '.done')
  if [ "$DONE" = "true" ]; then
    VIDEO_URI=$(echo "$STATUS" | jq -r '.response.generateVideoResponse.generatedSamples[0].video.uri')
    curl -L -H "x-goog-api-key: $GEMINI_API_KEY" "$VIDEO_URI" -o output.mp4
    break
  fi
  sleep 10
done
```

### Models available

| Model ID | Notes |
|----------|-------|
| `veo-3.1-generate-preview` | Full Veo 3.1 |
| `veo-3.1-fast-generate-preview` | Faster, lower quality |
| `veo-3.1-lite-generate-preview` | Most efficient |

### Pitfalls
- Free tier has one-time lifetime quota (not daily refresh). After exhaustion, needs paid plan.
- Paid plan requires billing setup in Google AI Studio ($10 minimum prepay).
- `predictLongRunning` endpoint uses Vertex AI request format, not standard Gemini format.
- Reference images: pass `referenceImages` in `instances[0]` with `bytesBase64Encoded` or `uri`.
- Video extension: pass `video.uri` from previous generation in `instances[0]`.
- See `references/gemini-api-veo.md` for detailed API reference.

## gflow-cli (Google Flow Reverse-Engineered API)

### Installation
```bash
pip install gflow-cli
playwright install chromium
```

### Auth (one-time, requires real browser with display)

```bash
gflow auth login --browser chrome
```

**⚠️ Headless server auth is IMPOSSIBLE to automate.** Every approach tried and confirmed blocked:

| Approach | Result |
|----------|--------|
| Playwright/CDP browser | ❌ *"This browser or app may not be secure"* |
| Browserbase/Steel cloud browser | ❌ Same Google bot detection |
| DataImpulse residential proxy | ❌ Google blocks proxy IPs entirely |
| xdotool on Xvfb | ❌ No window manager, focus failures, unreliable |
| `browser_navigate` / `browser_click` tools | ❌ Google detects cloud browser |
| `cua_browser` tools | ❌ Require real display binding (headless has none) |
| noVNC + VNC relay | ❌ Session drops, can't reliably interact |

**ONLY RELIABLE METHOD:** Auth on a machine with a real display (laptop/PC), then copy `~/.local/share/gflow-cli/profile_default/` to the headless server. See `references/gflow-cli-google-flow.md` for Windows/Linux/macOS instructions and Google Drive transfer method (no SSH needed). Once done, the session persists indefinitely — no re-auth needed.

**⚠️ CROSS-PLATFORM PITFALL:** Chrome encrypts cookies with OS-specific keys. A profile from Windows Chrome CANNOT be used on Linux — the encrypted cookie values are unreadable. Use `--browser internal` (Playwright Chromium) for cross-platform profiles, or auth directly on the Linux server via VNC. The Google Drive transfer method works for Playwright Chromium profiles, not real Chrome profiles. See `references/gflow-cli-google-flow.md` for the full cross-platform compatibility matrix.

**Script:** `scripts/gflow_auto_login.py` — Playwright-based auto-login for machines with a real display only (404 on headless due to missing `playwright` module in background subshells).

### Key Commands
```bash
# Text-to-Video
gflow video t2v "prompt" --aspect 9:16 --duration 8 --model veo-fast

# Reference-to-Video (Ingredients!) — up to 3 refs for Veo, 7 for Omni Flash
gflow video r2v "prompt" --ref char.png --ref scene.png --ref style.png --model veo-fast

# Image generation (Nano Banana/Imagen)
gflow image t2i "prompt"
gflow image i2i "prompt" --ref input.png

# Multi-scene movie from TOML
gflow movie template
gflow movie run

# Scene composition (like Scenebuilder)
gflow scene create CLIP_REF1 CLIP_REF2...

# Character management
gflow character create --name "Hero" --prompt "description..."
```

### Google Flow Internal API Endpoints
Base: `https://aisandbox-pa.googleapis.com`
API Key: `AIzaSyBtrm0o5ab1c-Ec8ZuLcGt3oJAA5VWt3pY` (public)
reCAPTCHA site key: `6LdsFiUsAAAAAIjVDZcuLhaHiDn5nnHVXVRQGeMV`

- `POST /v1/projects/{id}/flowMedia:batchGenerateImages` — T2I
- `POST /v1/video:batchAsyncGenerateVideoText` — T2V
- `POST /v1/video:batchAsyncGenerateVideoStartImage` — I2V (start frame)
- `POST /v1/video:batchAsyncGenerateVideoReferenceImages` — R2V (ingredients)
- `POST /v1/video:batchCheckAsyncVideoGenerationStatus` — poll
- `GET /v1/media/{mediaId}` — get result
- `GET /v1/credits` — credit check

Auth: Bearer `ya29.*` + reCAPTCHA in `recaptchaContext.token`.

## Composio Tool Invocation Patterns

### SEARCH_TOOLS
```python
# Always use queries array with use_case + known_fields, session with generate_id
mcp__composio__COMPOSIO_SEARCH_TOOLS(
    queries=[{"use_case": "...", "known_fields": "key:value"}],
    session={"generate_id": true}
)
```

### MANAGE_CONNECTIONS
```python
# Parameter is `toolkits` (plural array), NOT `toolkit`
mcp__composio__COMPOSIO_MANAGE_CONNECTIONS(toolkits=["youtube"])
```

### MULTI_EXECUTE_TOOL
```python
# Execute tools in parallel. Each tool needs tool_slug + arguments.
mcp__composio__COMPOSIO_MULTI_EXECUTE_TOOL(
    tools=[{"tool_slug": "GEMINI_GENERATE_VIDEOS", "arguments": {...}}],
    sync_response_to_workbench=false,
    session_id="come"
)
```

## Veo 3.1 Lite Video Generation

Model: `veo-3.1-lite-generate-preview` (only model available)

### Supported Parameters
| Parameter | Values | Notes |
|-----------|--------|-------|
| `aspect_ratio` | `9:16`, `16:9` | 9:16 for Shorts/TikTok |
| `duration_seconds` | 4, 6, 8 | Max 8 seconds per clip |
| `resolution` | `720p` | Only 720p supported |
| `person_generation` | `allow_all` | Only option |

### Pitfalls
- **NO `negative_prompt`** — Veo 3.1 Lite does NOT support it. Will return 400 INVALID_ARGUMENT.
- **NO `negativePrompt`** — same field, same rejection.
- Resolution is limited to 720p. 1080p is coerced to 720p silently.
- 8-second minimum for 1080p (but we only get 720p anyway).
- Keep concurrent jobs ≤ 3-5 to avoid 429 RESOURCE_EXHAUSTED.

### Workflow
1. Call `GEMINI_GENERATE_VIDEOS` → get `operation_name`
2. Call `GEMINI_WAIT_FOR_VIDEO` with operation_name → get `video_file.s3url`
3. Download from s3url with curl (URL is time-limited, ~1 hour)

### Output
- Format: h264 + AAC, 720x1280 (9:16) or 1280x720 (16:9)
- File: ~4-6MB per 6-second clip
- SynthID watermarked (invisible)

## Nano Banana Image Generation

Model: `gemini-3-pro-image-preview` (Nano Banana Pro, default)

### Supported Parameters
| Parameter | Values |
|-----------|--------|
| `aspect_ratio` | `1:1`, `9:16`, `16:9`, `4:5`, etc. |
| `image_size` | `1K`, `2K`, `4K` |
| `model` | `gemini-3-pro-image-preview`, `gemini-2.5-flash-image` |

### Pitfalls
- Concurrent usage may trigger 429 — keep ≤ 3 concurrent.
- Output is JPEG only (not PNG).
- s3url is time-limited; download immediately.

## YouTube Upload

### Via Composio
- Requires OAuth connection via `COMPOSIO_MANAGE_CONNECTIONS(toolkits=["youtube"])`
- User must click auth link within 10 minutes
- Tools: `YOUTUBE_UPLOAD_VIDEO`, `YOUTUBE_MULTIPART_UPLOAD_VIDEO`
- Video file must be uploaded as s3key-backed staged object

### Via Postiz
- Postiz CLI: `postiz upload video.mp4` → `postiz posts:create ...`
- Postiz REST API: `POST /public/v1/posts` with API key
- Supports scheduling with precise timestamps

## Video Assembly

Google Flow's Scenebuilder is **UI-only** — no API. Use `ffmpeg` for automated concatenation:

```bash
# Concat multiple clips
for f in clips/scene_*.mp4; do
    echo "file '$f'" >> filelist.txt
done
ffmpeg -f concat -safe 0 -i filelist.txt -c copy final.mp4 -y
```

Limitations: no transitions, no audio mixing, no overlay text. For cinematic quality, manual assembly in Google Flow Scenebuilder is required.

## Pipeline Project Structure

```
youtube-shorts/
├── scripts/          # Generated scripts (YYYY-MM-DD.md)
├── logs/
│   └── topic_history.md   # Track used topics
├── output/
│   └── YYYYMMDD/
│       ├── clips/    # Individual Veo clips
│       └── final.mp4 # Concatenated video
├── assets/           # Character/style reference images
└── concat.sh         # ffmpeg concat helper
```

## Cron Job Setup

For daily automated runs, use `cronjob` tool with the full pipeline prompt. The cron agent will:
1. Check topic_history.md for used topics
2. Generate new script
3. Call Veo API for each scene
4. Download and concat with ffmpeg
5. Upload to YouTube

Schedule: `0 12 * * *` UTC = 19:00 WIB (7 PM Jakarta time).

## References

- `references/veo-composio-workflow.md` — Detailed Veo API call examples and error patterns
- `references/pipeline-script-template.md` — Full pipeline script template for cron jobs
- `references/gflow-cli-google-flow.md` — gflow-cli setup, auth, model matrix, headless auth pitfalls, and alternative CLI tools
- `scripts/gflow_auto_login.py` — Playwright auto-login for gflow-cli (real display only)