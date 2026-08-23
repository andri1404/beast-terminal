# gflow-cli Reference

Reverse-engineered CLI for Google Flow's internal API (`aisandbox-pa.googleapis.com`).

## Install
```bash
python3 -m venv .venv
.venv/bin/pip install gflow-cli
.venv/bin/playwright install chromium
```

## Model Inventory
```
Image models:
- NARWHAL (nano2)          - Nano Banana 2, ref cap 10
- GEM_PIX_2 (nano-pro)     - Nano Banana Pro, ref cap 10
- IMAGEN_3_5 (image4)      - Imagen 4, ref cap 3

Video models:
- omni_flash               - Omni Flash, ref cap 7, max 10s
- veo_3_1_lite             - Veo 3.1 Lite, ref cap 3, max 8s
- veo_3_1_fast             - Veo 3.1 Fast, ref cap 3, max 8s
- veo_3_1_quality          - Veo 3.1 Quality, ref cap 0, max 8s
```

## Auth Flow

### Passive Capture (--browser chrome)
```bash
gflow auth login --browser chrome
```
Opens real Chrome. User must sign in at labs.google/fx. Once Flow editor loads, close browser manually.

### Internal Browser (--browser internal)
```bash
gflow auth login --browser internal
```
Uses Playwright Chromium. Same sign-in flow but may have Google OAuth issues.

## Profile Lock Fix

When you see `ProfileLockedError`:
```
the browser exited immediately while launching on profile dir
```

Fix:
```bash
rm -f ~/.local/share/gflow-cli/profile_default/SingletonLock
rm -f ~/.local/share/gflow-cli/profile_default/SingletonCookie
rm -f ~/.local/share/gflow-cli/profile_default/SingletonSocket
# Also kill stale Chrome processes
ps aux | grep -i chrome | grep -v grep | awk '{print $2}' | xargs -r kill -9
```

## Key Commands

```bash
# Text-to-video
gflow video t2v "prompt" --aspect 9:16 --duration 8 --model veo-fast

# Reference-to-video (Ingredients!)
gflow video r2v "prompt" --ref char.png --ref scene.png --model veo-fast

# Text-to-image
gflow image t2i "prompt" --aspect 9:16 --model nano-pro --out output.png

# Multi-scene movie from TOML
gflow movie template  # generate template
gflow movie run       # execute

# Scene composition
gflow scene create clip1_id clip2_id
```

## Headless Server Notes

gflow-cli requires a browser for auth. On headless servers:
1. Use Xvfb for virtual display: `Xvfb :99 -screen 0 1280x720x24`
2. Set `DISPLAY=:99` for all gflow commands
3. `--browser internal` mode uses Playwright's Chromium headless shell
4. Google OAuth may block sign-in in automated browsers - use `--browser chrome` with real Chrome if possible
5. Once cookies are captured, they persist in the profile directory