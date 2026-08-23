# Veo API Patterns (Composio Gemini)

## Generate Video

### Tool: GEMINI_GENERATE_VIDEOS
```json
{
  "aspect_ratio": "9:16",
  "duration_seconds": 8,
  "prompt": "Detailed scene description..."
}
```

### Tool: GEMINI_WAIT_FOR_VIDEO
```json
{
  "operation_name": "models/veo-3.1-lite-generate-preview/operations/xxxxx"
}
```

### Response (success)
```json
{
  "success": true,
  "data": {
    "rai_filtering": null,
    "success": true,
    "video_file": {
      "mimetype": "video/mp4",
      "name": "generated_video_1786379592.mp4",
      "s3url": "https://temp.4d4f16c61d89ec64e760039c4ec50717.r2.cloudflarestorage.com/..."
    }
  }
}
```

### Response (error code 13)
```json
{
  "success": false,
  "data": {
    "message": "Video generation operation failed with error code 13: Video generation failed due to an internal server issue."
  }
}
```

## Generate Image (Nano Banana)

### Tool: GEMINI_GENERATE_IMAGE
```json
{
  "aspect_ratio": "9:16",
  "image_size": "1K",
  "model": "gemini-3-pro-image-preview",
  "prompt": "Character description..."
}
```

### Response (success)
```json
{
  "success": true,
  "data": {
    "image": {
      "mimetype": "image/jpeg",
      "name": "generated_image.jpg",
      "s3url": "https://temp.4d4f16c61d89ec64e760039c4ec50717.r2.cloudflarestorage.com/..."
    }
  }
}
```

## Parallel Execution Pattern

Use COMPOSIO_MULTI_EXECUTE_TOOL with session_id from COMPOSIO_SEARCH_TOOLS:

```json
{
  "tools": [
    {"tool_slug": "GEMINI_GENERATE_VIDEOS", "arguments": {...}},
    {"tool_slug": "GEMINI_GENERATE_VIDEOS", "arguments": {...}},
    {"tool_slug": "GEMINI_GENERATE_VIDEOS", "arguments": {...}}
  ],
  "sync_response_to_workbench": false,
  "session_id": "come",
  "current_step": "GEN_SCENES"
}
```

## Download Pattern (execute_code)

```python
import urllib.request, os

out = "/home/ubuntu/youtube-shorts/output/{project}/clips"
os.makedirs(out, exist_ok=True)

urls = {
    "scene_01.mp4": "https://temp.4d4f16c61d89ec64e760039c4ec50717.r2.cloudflarestorage.com/...",
    # ...
}

for name, url in urls.items():
    path = os.path.join(out, name)
    urllib.request.urlretrieve(url, path)
    size = os.path.getsize(path)
    print(f"✅ {name}: {size/1024:.0f}KB")
```

## ffmpeg Concat

```bash
cd /home/ubuntu/youtube-shorts/output/{project}
for f in clips/scene_01.mp4 clips/scene_02.mp4 ...; do
  echo "file '$f'"
done > filelist.txt

ffmpeg -f concat -safe 0 -i filelist.txt -c copy final.mp4 -y
```

## Known Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 13 | Internal server error | Retry same prompt (usually works) |
| 429 | Rate limit | Reduce concurrency, add backoff |
| 400 | Invalid argument | Check for unsupported params (negative_prompt, etc.) |