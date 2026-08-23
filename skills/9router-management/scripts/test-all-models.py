#!/usr/bin/env python3
"""Test all 9Router models with a given prompt. Parses SSE streaming responses."""
import subprocess, json, time, sys, os

API_KEY = os.environ.get("9ROUTER_API_KEY", "sk-6b3ac6ef8e3b70c9-p98opp-3036c09b")
BASE_URL = os.environ.get("9ROUTER_URL", "http://localhost:20128/v1/chat/completions")

PROMPT = sys.argv[1] if len(sys.argv) > 1 else "Say hello in Indonesian in 1 sentence and identify yourself."

# Models to test — edit as needed
MODELS = [
    "qd/ultimate", "qd/auto", "qd/performance", "qd/efficient",
    "qd/qmodel_preview", "qd/qmodel_latest", "qd/qmodel",
    "qd/kmodel_latest", "qd/kmodel", "qd/gm51model",
    "qd/dmodel", "qd/dfmodel", "qd/mmodel", "qd/lite", "qd/qmodel_38max"
]

def parse_sse(text):
    """Parse SSE streaming or JSON+DONE hybrid responses.
    
    Some providers (e.g., TokenHarbor) return a complete JSON body
    followed by 'data: [DONE]' — strip the SSE terminator and parse
    as JSON first, then fall back to SSE streaming.
    """
    import re
    
    # Try JSON+DONE hybrid first
    clean = re.sub(r'\n?data:\s*\[DONE\].*$', '', text, flags=re.DOTALL).strip()
    try:
        data = json.loads(clean)
        if "choices" in data and len(data["choices"]) > 0:
            msg = data["choices"][0].get("message", {})
            content = msg.get("content", "") or ""
            reasoning = msg.get("reasoning_content", "") or ""
            usage = data.get("usage", {})
            model = data.get("model", "")
            return content.strip(), model, usage
    except:
        pass
    
    # Fall back to SSE streaming
    content = ""
    model = ""
    usage = {}
    for line in text.split("\n"):
        if line.startswith("data: ") and line != "data: [DONE]":
            try:
                chunk = json.loads(line[6:])
                if "model" in chunk and not model:
                    model = chunk["model"]
                if "choices" in chunk:
                    for c in chunk["choices"]:
                        if "delta" in c and "content" in c["delta"]:
                            content += c["delta"]["content"]
                if "usage" in chunk:
                    usage = chunk["usage"]
            except:
                pass
    return content.strip(), model, usage

results = []
for i, model in enumerate(MODELS, 1):
    print(f"[{i}/{len(MODELS)}] Testing {model}...", flush=True)
    start = time.time()
    try:
        r = subprocess.run([
            "curl", "-s", "--max-time", "120", BASE_URL,
            "-H", f"Authorization: Bearer {API_KEY}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": PROMPT}],
                "max_tokens": 500,
                "temperature": 0.7
            })
        ], capture_output=True, text=True, timeout=130)
        elapsed = time.time() - start
        
        content, actual_model, usage = parse_sse(r.stdout)
        
        if content:
            pt = usage.get("prompt_tokens", "?")
            ct = usage.get("completion_tokens", "?")
            results.append({"model": model, "actual": actual_model, "status": "OK",
                "time": elapsed, "prompt_tokens": pt, "completion_tokens": ct,
                "response": content})
            print(f"  OK [{actual_model}] {elapsed:.1f}s {pt}/{ct}t → {content[:120]}", flush=True)
        else:
            try:
                resp = json.loads(r.stdout)
                err = resp.get("error", {}).get("message", r.stdout[:200])
                results.append({"model": model, "actual": "-", "status": "ERROR",
                    "time": elapsed, "error": err})
                print(f"  ERR {err[:120]}", flush=True)
            except:
                results.append({"model": model, "actual": "-", "status": "PARSE_FAIL",
                    "time": elapsed, "raw": r.stdout[:200]})
                print(f"  FAIL parse error", flush=True)
    except Exception as e:
        elapsed = time.time() - start
        results.append({"model": model, "actual": "-", "status": "EXCEPTION",
            "time": elapsed, "error": str(e)})
        print(f"  EXC {str(e)[:120]}", flush=True)

# Summary
print("\n" + "="*80)
for r in results:
    if r["status"] == "OK":
        print(f"  {r['model']} [{r['actual']}] {r['time']:.1f}s {r['prompt_tokens']}/{r['completion_tokens']}t")
        print(f"    {r['response'][:200]}")
    else:
        print(f"  {r['model']} {r['status']}: {r.get('error', r.get('raw', ''))[:150]}")
    print()

print(f"Total: {len(MODELS)} | OK: {sum(1 for r in results if r['status']=='OK')} | Failed: {sum(1 for r in results if r['status']!='OK')}")

# Save JSON
with open("/tmp/9router_test_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nFull results: /tmp/9router_test_results.json")