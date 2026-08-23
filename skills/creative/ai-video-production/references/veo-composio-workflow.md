# Veo Composio Workflow — Detailed API Examples

## Generation + Polling Pattern

```python
# Step 1: Generate
result = run_composio_tool('GEMINI_GENERATE_VIDEOS', {
    'prompt': 'A cinematic scene of...',
    'aspect_ratio': '9:16',
    'duration_seconds': 6
})
op_name = result['data']['operation_name']
# Example: "models/veo-3.1-lite-generate-preview/operations/3mb7arc7qgpq"

# Step 2: Poll (wait 10-30s between polls, up to 12 min)
result = run_composio_tool('GEMINI_WAIT_FOR_VIDEO', {
    'operation_name': op_name
})
video_url = result['data']['video_file']['s3url']
```

## Error Patterns

### 400 INVALID_ARGUMENT — negative_prompt
```
"`negativePrompt` isn't supported by this model."
```
Fix: Remove `negative_prompt` / `negativePrompt` field entirely.

### 400 PROHIBITED_CONTENT
```
PROHIBITED_CONTENT or IMAGE_RECITATION
```
Fix: Rephrase prompt to neutral, policy-compliant language.

### 429 RESOURCE_EXHAUSTED
```
Too many concurrent jobs
```
Fix: Reduce concurrency, use exponential backoff (1s→2s→4s, ~5 retries).

### Safety filter rejection
```
done=true, no video_file, raiMediaFilteredReasons present
```
Fix: Revise prompt to avoid triggering content filters.

## Output Validation

```python
def validate_video(result):
    data = result.get('data', {})
    if not data.get('success'):
        return False
    vf = data.get('video_file', {})
    if not vf or not vf.get('s3url'):
        rf = data.get('rai_filtering', {})
        if rf.get('filtered'):
            raise Exception(f"Safety filtered: {rf}")
        return False
    return True
```

## Download Pattern

```bash
curl -sL -o output.mp4 "$S3URL"
# Verify
ffprobe -v error -show_entries stream=width,height,duration,codec_name \
  -of default=noprint_wrappers=1 output.mp4
```

## Veo 3.1 Lite Output Specs (confirmed)
- Resolution: 720x1280 (9:16) or 1280x720 (16:9)
- Codec: h264 video + AAC audio
- Duration: 4, 6, or 8 seconds exactly
- Size: ~4.6MB for 6-second clip
- FPS: typically 24fps
- Watermark: SynthID (invisible)