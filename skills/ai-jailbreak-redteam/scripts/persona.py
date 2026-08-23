#!/usr/bin/env python3
"""Print a persona prompt by name. Usage: python3 persona.py <name>"""
import sys
# This is a lightweight version — the full arsenal is at /home/ubuntu/jailbreak-arsenal.py
print("Use the full arsenal: python3 /home/ubuntu/jailbreak-arsenal.py prompt " + sys.argv[1] if len(sys.argv) > 1 else "list")