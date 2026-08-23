#!/usr/bin/env python3
"""Auto login to Google Flow via Playwright. Saves profile for gflow-cli.

WARNING: Google blocks Playwright/CDP browsers on headless servers.
This script works on machines with a REAL display only.
For headless servers, auth on a real machine and copy the profile
(see references/gflow-cli-google-flow.md).

KNOWN ISSUE: When run via `terminal(background=true)`, the background subshell
may not find the `playwright` module even though it's installed. Run in foreground
mode (`terminal(command=...)` without background=true) instead. This is a Hermes
background subshell environment quirk, not a Python or pip bug.

Usage:
    DISPLAY=:0 python3 gflow_auto_login.py <PASSWORD>
"""

import os, sys, time

os.environ['DISPLAY'] = os.environ.get('DISPLAY', ':0')

from playwright.sync_api import sync_playwright

GFLOW_PROFILE = os.path.expanduser("~/.local/share/gflow-cli/profile_default")
EMAIL = os.environ.get('GFLOW_EMAIL', 'safrizalt6@gmail.com')
FLOW_URL = "https://labs.google/fx/tools/flow"


def main():
    password = sys.argv[1] if len(sys.argv) > 1 else None
    if not password:
        print("Usage: python3 gflow_auto_login.py <PASSWORD>")
        sys.exit(1)

    os.makedirs(GFLOW_PROFILE, exist_ok=True)
    print(f"[*] Profile: {GFLOW_PROFILE}")
    print(f"[*] Email: {EMAIL}")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            GFLOW_PROFILE,
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ],
            viewport={'width': 1280, 'height': 800},
        )
        page = context.new_page()

        try:
            print("[1] Going to Google Flow...")
            page.goto(FLOW_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            print(f"    URL: {page.url[:120]}")

            # Check if already signed in (Flow editor loaded)
            if "labs.google/fx/tools/flow" in page.url:
                signin_btn = page.locator(
                    'a:has-text("Sign in"), button:has-text("Sign in"), '
                    'a:has-text("Get started"), button:has-text("Get started"), '
                    'button:has-text("Create with Google Flow")'
                )
                if signin_btn.count() > 0 and signin_btn.first.is_visible():
                    print("[*] Clicking sign-in...")
                    signin_btn.first.click()
                    time.sleep(4)
                else:
                    editor = page.locator('textarea, [contenteditable="true"]')
                    if editor.count() > 0:
                        print("[✓] Already signed in to Flow editor!")
                        return

            print(f"    After sign-in click: {page.url[:120]}")

            # Handle Google sign-in form
            if "accounts.google.com" in page.url:
                time.sleep(2)

                # Fill email
                email_input = page.locator(
                    'input[type="email"], input#identifierId'
                )
                if email_input.count() > 0:
                    print(f"[2] Filling email: {EMAIL}")
                    email_input.first.click()
                    email_input.first.fill(EMAIL)
                    time.sleep(1)
                    page.locator(
                        '#identifierNext, button:has-text("Next")'
                    ).first.click()
                    print("    Clicked Next")
                    time.sleep(4)

                print(f"    After email: {page.url[:120]}")

                # Fill password
                time.sleep(2)
                pwd_input = page.locator(
                    'input[type="password"], input[name="Passwd"]'
                )
                if pwd_input.count() > 0:
                    print("[3] Filling password...")
                    pwd_input.first.click()
                    pwd_input.first.fill(password)
                    time.sleep(1)
                    page.locator(
                        '#passwordNext, button:has-text("Next")'
                    ).first.click()
                    print("    Clicked Next")
                    time.sleep(5)

                print(f"    After password: {page.url[:120]}")

                # Handle 2FA
                time.sleep(3)
                if any(kw in page.url.lower() for kw in
                       ['challenge', 'verify', '2fa', 'authenticator']):
                    print("[!] 2FA required! Waiting 120s for manual input...")
                    page.screenshot(path="/tmp/2fa_screen.png")
                    time.sleep(120)

                # Wait for Flow editor
                print("[4] Waiting for Google Flow editor...")
                for i in range(60):
                    if ("labs.google/fx/tools/flow" in page.url
                            and "accounts.google.com" not in page.url):
                        print(f"    Flow loaded! ({i*2}s)")
                        break
                    time.sleep(2)

                if "labs.google/fx/tools/flow" not in page.url:
                    page.goto(FLOW_URL, wait_until="domcontentloaded",
                              timeout=30000)
                    time.sleep(5)

                print(f"    Final URL: {page.url[:120]}")

                try:
                    page.wait_for_selector(
                        'textarea, [contenteditable="true"]', timeout=10000
                    )
                    print("[✓] Flow editor detected!")
                except Exception:
                    print("[!] Editor not detected, but session may be valid")

            time.sleep(3)
            print(f"[✓] Session saved to: {GFLOW_PROFILE}")

        except Exception as e:
            print(f"[!] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            page.close()
            context.close()
            print("[✓] Done. Try: gflow video t2v 'test' --model veo-fast")


if __name__ == "__main__":
    main()