#!/usr/bin/env python3
"""Check a cron script (and optional prompt) against the Hermes gateway
lifecycle_guard BEFORE creating the job, so a create doesn't fail blind.

Usage:
    python3 check_cron_script.py /path/to/script.py ["optional prompt text"]

If the script lives under ~/.hermes/scripts/, pass the bare name too:
    python3 check_cron_script.py hfm_push_signal.py

Prints PASS, or BLOCKED plus the exact line number(s) whose shell-tokenizer
segment starts with a bare '/', which is the usual false-positive culprit.
"""
import sys
sys.path.insert(0, "/home/ubuntu/.hermes/hermes-agent")
from cron.lifecycle_guard import check_gateway_lifecycle, _iter_command_segments, _read_script_for_scanning


def main():
    args = sys.argv[1:]
    script = args[0] if args else ""
    prompt = args[1] if len(args) > 1 else ""

    try:
        check_gateway_lifecycle(prompt, script)
        print("PASS - no lifecycle-guard block")
        return
    except Exception as e:
        print("BLOCKED:", str(e)[:140])

    # Locate bare-'/' leading segments in the script body.
    try:
        text = _read_script_for_scanning(script) if script else ""
    except Exception:
        text = ""
    if not text:
        print("(could not read script body for line-level diagnosis)")
        return
    found = False
    for i, line in enumerate(text.splitlines(), 1):
        for seg in _iter_command_segments(line):
            if seg and seg[0] == "/":
                print(f"  line {i}: segment starts with bare '/': {line.strip()}")
                found = True
    if not found:
        print("  (no bare-'/' segment; re-check prompt text or referenced .sh scripts)")


if __name__ == "__main__":
    main()
