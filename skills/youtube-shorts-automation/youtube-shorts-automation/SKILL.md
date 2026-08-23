---
name: youtube-shorts-automation
description: Use when automating YouTube Shorts. Veo API+ffmpeg pipeline.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [youtube, shorts, video, veo, composio, ffmpeg, automation]
---

# YouTube Shorts Automated Video Production

Fully automated pipeline for creating AI-generated YouTube Shorts videos using Composio's Veo 3.1 Lite + Nano Banana, ffmpeg assembly, and YouTube upload.

## Pipeline Overview

```
Research → Script → Generate Images → Generate Video Clips → ffmpeg Concat → Upload
```

## Project Structure

```
~/youtube-shorts/
├── scripts/          # Script files per date (YYYY-MM-DD.md)
├── logs/             # topic_history.md for tracking used topics
├── output/           # Per-date video output
│   └── YYYYMMDD/
│       ├── clips/    # Individual scene clips
│       ├── final.mp4 # Concatenated final video
│       └── filelist.txt
└── assets/           # Character images, style references
```

## Script Format

Each script file (`scripts/YYYY-MM-DD.md`) should contain:

```markdown
# YouTube Shorts Script - YYYY-MM-DD
## Topic: "Title"
## Theme: emotional theme

### SCENE N: NAME (X-Y detik)
**Visual:** Description of scene
**Teks layar:** "On-screen text"
**Prompt Veo:** English prompt for Veo API generation
```

## Veo 3.1 Lite API (via Composio)

### Key Parameters
- `aspect_ratio`: `"9:16"` (vertical) or `"16:9"`
- `duration_seconds`: `4`, `6`, or `8`
- `resolution`: `"720p"` only for 3.1 Lite
- `person_generation`: `"allow_all"` only

### Pitfalls
- **DO NOT use `negative_prompt`** — not supported by Veo 3.1 Lite, causes 400 INVALID_ARGUMENT
- **Error code 13** = internal server error, retry with same prompt
- **Max 3-5 concurrent jobs** — more causes 429 RESOURCE_EXHAUSTED
- **S3 URLs expire ~1 hour** — download immediately after `GEMINI_WAIT_FOR_VIDEO` returns
- **Generation time**: 30-120 seconds per clip

### Workflow per Scene
1. `GEMINI_GENERATE_VIDEOS` → get `operation_name`
2. `GEMINI_WAIT_FOR_VIDEO` → poll until `done=true`
3. Download from `video_file.s3url` immediately via `urllib.request.urlretrieve` or `curl`

## Nano Banana (via Composio)

- Model: `gemini-3-pro-image-preview` (Nano Banana Pro)
- `aspect_ratio`: `"9:16"` for Shorts
- `image_size`: `"1K"` (sufficient for reference)
- Returns `image.s3url` — download within 1 hour

## ffmpeg Assembly

Concat all clips with stream copy (no re-encode):

```bash
for f in clips/scene_*.mp4; do echo "file '$f'" >> filelist.txt; done
ffmpeg -f concat -safe 0 -i filelist.txt -c copy final.mp4 -y
```

## gflow-cli (Google Flow Alternative)

`gflow-cli` reverse-engineers Google Flow's internal API but requires browser auth.

### Install
```bash
python3 -m venv .venv && .venv/bin/pip install gflow-cli
.venv/bin/playwright install chromium
```

### Auth
- `gflow auth login --browser internal` uses Playwright Chromium
- `--browser chrome` opens real Chrome (more reliable for Google OAuth)
- Profile stored at `~/.local/share/gflow-cli/profile_default/`
- If profile locked: remove `SingletonLock`, `SingletonCookie`, `SingletonSocket` files
- `gflow models` works without auth (reads static model info)

### Key Commands
- `gflow video r2v` — Reference-to-video (Ingredients! up to 3 ref images)
- `gflow video t2v` — Text-to-video
- `gflow image t2i` — Text-to-image (Nano Banana)
- `gflow movie run` — Multi-scene from TOML file
- `gflow scene create` — Scene composition

## Topic History

Track used topics in `logs/topic_history.md`:
```
YYYY-MM-DD | TOPIC | TITLE | STATUS
```

Avoid reusing themes. Popular themes: kehilangan, kerinduan, reuni, penyesalan, kasih sayang keluarga, persahabatan.

## YouTube Upload

Two options:
1. **Composio YouTube** — requires OAuth connection via `COMPOSIO_MANAGE_CONNECTIONS`
2. **Postiz CLI** — requires `POSTIZ_API_KEY` and `postiz` CLI

## Cron Job

Daily cron running at 19:00 WIB (12:00 UTC):
```
cronjob(action='create', schedule='0 12 * * *', prompt='...')
```

The cron agent should:
1. Read `logs/topic_history.md` to avoid repeats
2. Generate a new script
3. Call Composio for Veo + Nano Banana
4. Download and concat with ffmpeg
5. Upload to YouTube