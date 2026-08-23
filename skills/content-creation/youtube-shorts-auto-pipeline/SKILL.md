---
name: youtube-shorts-auto-pipeline
description: "Use when making automated YT Shorts. Veo API, ffmpeg, upload."
version: 1.0.0
---

# YouTube Shorts Automated Video Pipeline

Automated daily pipeline for producing AI-generated short films (9:16 vertical, ~50s) using Google's Veo video generation, Nano Banana image generation, ffmpeg assembly, and YouTube upload.

## Architecture

```
Research → Script → Generate Veo Clips → Download → ffmpeg Concat → YouTube Upload
```

## Step 1: Research & Script

Generate a topic and script with 5-6 scenes. Each scene needs:
- Visual description (Subject + Action + Setting + Mood/Lighting)
- Duration per scene: 8 seconds (Veo API max)
- Text overlay cues
- Audio/music cues

Save script to `scripts/{date}.md`. Track used topics in `logs/topic_history.md`.

## Step 2: Generate Video Clips (Veo API via Composio)

Use `GEMINI_GENERATE_VIDEOS` + `GEMINI_WAIT_FOR_VIDEO` via `COMPOSIO_MULTI_EXECUTE_TOOL`.

### Critical Rules
- **Batch size**: Generate 3 scenes per batch (max concurrency before 429 errors)
- **Download IMMEDIATELY** after polling — S3 URLs expire within ~1 hour
- **Use `urllib.request.urlretrieve`** in execute_code for reliable downloads (curl from terminal often fails with exit code 23 on expired URLs)

### Veo Model Parameters
- Model: `veo-3.1-lite-generate-preview` (only option currently)
- Aspect ratio: `9:16` (vertical shorts)
- Duration: `8` seconds (max for Veo Lite; 4, 6, 8 available)
- Resolution: `720p` (only option)

### Veo API Limitations
- **NO `negative_prompt`** — Veo 3.1 Lite rejects it with 400 INVALID_ARGUMENT
- **NO image references** — Veo API is text-only; "Ingredients" (reference images) only work in Google Flow UI
- **Character consistency**: Use VERY detailed, IDENTICAL character descriptions in every prompt (hair color, skin tone, clothing, age, facial features) to maintain visual consistency across scenes
- **Error code 13**: Internal server error — retry with same prompt, usually works on 2nd attempt
- **Concurrency**: Keep parallel jobs to ≤3 to avoid 429 RESOURCE_EXHAUSTED

### Prompt Structure for Consistency
Since Veo API lacks Ingredients support, use this pattern in every scene prompt:
```
A [CHARACTER DESCRIPTION - identical across all scenes], [ACTION], [SETTING], [MOOD/LIGHTING], [STYLE - identical across all scenes]
```
Example: "A man in his late 20s, short black hair, light brown skin, olive green t-shirt, [specific action], [setting], warm cinematic lighting, 3D animation style, Pixar-inspired"

## Step 3: Download & Assembly

### Download
Use `execute_code` with `urllib.request.urlretrieve`:
```python
import urllib.request, os

out = "/home/ubuntu/youtube-shorts/output/{project}/clips"
os.makedirs(out, exist_ok=True)
for name, url in urls.items():
    urllib.request.urlretrieve(url, os.path.join(out, name))
```

### Assembly with ffmpeg
```bash
# Create file list
for f in clips/scene_01.mp4 ...; do echo "file '$f'" >> filelist.txt; done

# Concat (no re-encoding — fast)
ffmpeg -f concat -safe 0 -i filelist.txt -c copy final.mp4 -y
```

### Expected Output
- 6 scenes × 8 seconds = 48 seconds total
- File size: ~10-12MB for 720p
- Codec: h264 + AAC
- Resolution: 720×1280 (9:16)

## Step 4: YouTube Upload

Two options:
1. **Composio YouTube** — requires OAuth connection via `COMPOSIO_MANAGE_CONNECTIONS`. User must click auth link.
2. **Postiz CLI** — `postiz upload video.mp4` + `postiz posts:create` with YouTube settings. Requires `POSTIZ_API_KEY` and `postiz` CLI installed.

### YouTube Metadata
- Title: Emotional, curiosity-driven, one sentence
- Description: Story context + CTA
- Tags: `#shortfilm #animasi #ceritapendek #sadstory #viral #fyp #storytelling #emosional`
- Schedule: 19:00-21:00 WIB (12:00-14:00 UTC)

## Step 5: Cron Job

Set up via `cronjob` tool:
- Schedule: `0 12 * * *` (19:00 WIB = 12:00 UTC)
- Load this skill in the cron job
- Prompt: Full pipeline instructions

## gflow-cli (Google Flow CLI)

### Discovery
`gflow-cli` (v0.53.1, PyPI) reverse-engineers Google Flow's internal API at `aisandbox-pa.googleapis.com`. Supports:
- `gflow video r2v` — Reference-to-video (Ingredients!) with up to 3 ref images
- `gflow video t2v` — Text-to-video
- `gflow image t2i` — Nano Banana image generation
- `gflow scene` — Scenebuilder-like assembly
- `gflow movie` — Multi-scene movie from TOML

### Auth Issue
`gflow-cli` requires browser-based Google OAuth login. On headless servers, this fails with `ProfileLockedError` because Playwright's `launch_persistent_context` can't start properly. Real Chrome (`--browser chrome`) also fails. The `--browser internal` mode launches Playwright Chromium but still requires manual Google sign-in.

**Workaround**: If the user can run `gflow auth login` on their local machine and copy the profile directory (`~/.local/share/gflow-cli/`) to the server, gflow can work. Otherwise, fall back to Composio Veo API.

### Installation
```bash
python3 -m venv .venv
.venv/bin/pip install gflow-cli
.venv/bin/playwright install chromium
```

## Pitfalls

1. **S3 URL expiration**: Download clips immediately after polling — URLs expire quickly
2. **Veo internal error 13**: Retry the scene; usually works on 2nd attempt
3. **Profile lock**: Remove `SingletonLock`, `SingletonCookie`, `SingletonSocket` from gflow profile dir before retrying
4. **Terminal backgrounding**: Don't use `&` in foreground commands — use `terminal(background=true)` instead
5. **gflow auth**: Headless server auth is unreliable; use Composio Veo API as primary path