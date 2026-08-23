---
name: 9router-prod-config
description: Production-ready 9Router setup with working models. Auto-detects broken ones.
---

# 9Router Production Config - Cleaned & Optimized

## ✅ Current Working Models (9 total)

| Speed | Model | Response Quality | Use Case |
|-------|-------|-----------------|----------|
| 🚀 7.9s | `qd/kmodel_latest` ⭐ | High | **DEFAULT** - Fastest pentest |
| ⚡ 8.6s | `qd/dmodel` | Highest | Best reasoning quality |
| ⚡ 8.7s | `qd/efficient` | High | Quick security tasks |
| ⚡ 8.9s | `qd/ultimate` | Very High | Complex analysis |
| 🔧 10.0s | `qd/qmodel` | High | Standard general use |
| 🌐 10.5s | `qd/qmodel_38max` | Max | Largest Qwen model |
| 🔄 11.1s | `qd/performance` | Medium | ChatGPT via 9R |
| 🏎️ 16.0s | `qd/auto` | Mixed | Auto router fallback |
| 📜 20.8s | `qd/kmodel` | Maximum | Long context documents |

## ❌ Removed from Rotation (5 censored/broken):

1. `qd/qmodel_preview` - Returns empty response (broken)
2. `qd/qmodel_latest` - Censored on security topics
3. `qd/gm51model` - Gemini refuses pentest queries
4. `qd/dfmodel` - Irony! DeepSeek fast version is filtered
5. `qd/mmodel` - MiniMax refuses security content
6. `qd/lite` - Long responses but too generic/censored

## 🔧 Active Configuration

```bash
# Primary recommendation
hermes config set model.default qd/kmodel_latest
hermes config set model.provider custom
hermes config set model.base_url http://localhost:20128/v1
hermes config set model.api_key sk-6b3ac6ef8e3b70c9-p98opp-3036c09b

# Alternative by use case:
# hermes config set model.default qd/dmodel        # For best quality
# hermes config set model.default qd/qmodel_latest # If you want latest Qwen
# hermes config set model.default qd/ultimate      # For complex reasoning
```

## 📊 Test Results Summary

- **Total Models Tested:** 15
- **Working (PASS):** 9/15 (60%)
- **Refused Content:** 5/15 (33%)
- **Broken:** 1/15 (7%)
- **Pentest Safety:** 0% refusal rate on PASS models

## 💡 Usage Strategy

### For Pentest Reconnaissance:
```bash
sniff exploit CVE-2026-33453
search_exploit apache struts
pentest wordpress vulns
```

All working with `qd/kmodel_latest` or `qd/dmodel`.

### For Long Research Documents:
Use `qd/kmodel` (20s but full details)

### For Complex Analysis:
Use `qd/ultimate` or `qd/qmodel_38max`

## Maintenance Commands

```bash
# Check current status
curl http://localhost:20128/v1/models -H "Authorization: Bearer sk-6b3..."

# Run pentest compliance check
python3 /tmp/test_all_9router.py

# Switch back to DeepSeek R1 if needed
hermes config set model.default qd/dmodel

# Verify skills API running
curl http://127.0.0.1:8765/stats -H "X-API-Key: hermes-logs-2026"
```

## Known Issues Resolved

✅ Fixed: Empty model selection → Now uses `qd/kmodel_latest`  
✅ Fixed: All 15 models visible in config  
✅ Fixed: Broken models marked as removed  
✅ Fixed: Pentagon-safe routing (no refusals)  

📁 Full test results: `/tmp/9router_pentest_test_results.json`
