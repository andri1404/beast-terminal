# Veo 3.1 Lite API Reference (via Composio Gemini)

## Tool: GEMINI_GENERATE_VIDEOS

### Request Schema
```json
{
  "aspect_ratio": "9:16",
  "duration_seconds": 8,
  "prompt": "video description in English",
  "model": "veo-3.1-lite-generate-preview",
  "resolution": "720p",
  "person_generation": "allow_all"
}
```

### Response
```json
{
  "operation_name": "models/veo-3.1-lite-generate-preview/operations/XXXXXXXXXX",
  "raw": {
    "done": false,
    "name": "models/veo-3.1-lite-generate-preview/operations/XXXXXXXXXX"
  }
}
```

## Tool: GEMINI_WAIT_FOR_VIDEO

### Request
```json
{
  "operation_name": "models/veo-3.1-lite-generate-preview/operations/XXXXXXXXXX"
}
```

### Success Response
```json
{
  "success": true,
  "video_file": {
    "mimetype": "video/mp4",
    "name": "generated_video_1786377924.mp4",
    "s3url": "https://temp.4d4f16c61d89ec64e760039c4ec50717.r2.cloudflarestorage.com/..."
  }
}
```

### Error: negative_prompt not supported
```json
{
  "error": {
    "code": 400,
    "message": "`negativePrompt` isn't supported by this model.",
    "status": "INVALID_ARGUMENT"
  }
}
```

### Error: Internal server error (code 13)
```json
{
  "message": "Video generation operation failed with error code 13: Video generation failed due to an internal server issue."
}
```
**Fix**: Retry with same prompt. Usually succeeds on 2nd attempt.

## Video Output Properties
- Codec: h264 (video) + AAC (audio)
- Resolution: 720x1280 (9:16 vertical)
- Duration: 6 or 8 seconds (as requested)
- Size: ~1.5-4MB per clip

## Download Pattern
```python
import urllib.request
urllib.request.urlretrieve(s3url, output_path)
```
S3 URLs expire in ~1 hour. Download immediately after polling completes.