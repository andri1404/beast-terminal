# Gemini API — Veo Video Generation Reference

## Official Google API (no reverse-engineering, no browser auth)

Base URL: `https://generativelanguage.googleapis.com/v1beta`

## Auth

API key from Google AI Studio: https://aistudio.google.com/apikey
Header: `x-goog-api-key: YOUR_API_KEY`

## Endpoints

### Submit video generation
```
POST /v1beta/models/{model}:predictLongRunning
Content-Type: application/json
x-goog-api-key: {key}

Body:
{
  "instances": [{
    "prompt": "video description",
    "referenceImages": [                          // optional, up to 3
      {
        "referenceType": "asset",                 // or "style"
        "image": {
          "bytesBase64Encoded": "...",
          "mimeType": "image/jpeg"
        }
      }
    ],
    "video": {                                    // optional, for extension
      "uri": "https://generativelanguage.googleapis.com/v1beta/files/..."
    }
  }],
  "parameters": {
    "aspectRatio": "9:16",                        // or "16:9"
    "durationSeconds": 8,                         // 4, 6, 8, 10
    "resolution": "720p",                         // or "1080p"
    "sampleCount": 1,                             // 1-4
    "seed": 12345,                                // optional
    "personGeneration": "allow_all"               // or "allow_adult"
  }
}

Response (202):
{
  "name": "operations/...",
  "done": false
}
```

### Poll status
```
GET /v1beta/{operation_name}
x-goog-api-key: {key}

Response (200, done):
{
  "name": "operations/...",
  "done": true,
  "response": {
    "generateVideoResponse": {
      "generatedSamples": [{
        "video": {
          "uri": "https://generativelanguage.googleapis.com/v1beta/files/..."
        }
      }]
    }
  }
}
```

### Download video
```
GET {video.uri}
x-goog-api-key: {key}
Response: binary video/mp4
```

## Models

| Model ID | Notes |
|----------|-------|
| `veo-3.1-generate-preview` | Full Veo 3.1, highest quality |
| `veo-3.1-fast-generate-preview` | Faster, lower quality |
| `veo-3.1-lite-generate-preview` | Most efficient, lowest cost |

## Pricing & Limits

- Free tier: one-time lifetime quota per account (not daily refresh)
- After exhaustion: needs paid plan ($10 minimum prepay via Google AI Studio)
- Paid tier: ~$0.05-0.10/second for video generation
- Rate limits: varies by tier, keep ≤ 3 concurrent

## Pitfalls

- `predictLongRunning` format is Vertex AI style, NOT standard Gemini `generateContent` format
- Response uses `instances` array (not `contents`)
- The `@google/genai` SDK's `generateVideos()` method may return 404 for preview models; use REST `predictLongRunning` instead
- Free tier quota is ONE-TIME, not daily. Once exhausted, UI elements gray out permanently
- SynthID watermark embedded in all outputs (invisible)

## n8n Integration

n8n community nodes available:
- `n8n-nodes-googleflow-ai` — Google Flow (Nano Banana / Veo) nodes
- `n8n-nodes-veo` (morekaccino) — uses Gemini API key
- `n8n-nodes-google-vertex-ai` — Vertex AI with service account
- `flavien317/n8n-nodes-vertex-ai-full` — Full Vertex AI with service account

n8n workflow templates for Veo available at https://n8n.io/workflows

## Sources

- https://ai.google.dev/gemini-api/docs/video
- https://ai.google.dev/gemini-api/docs/models/veo-3.1-generate-preview
- https://aistudio.google.com/models/veo-3
- https://docs.apigo.ai/en/api-reference/examples/video-generation-gemini