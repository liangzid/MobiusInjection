#!/usr/bin/env python3
"""Web test script to validate Ollama connection."""

import sys
import requests

HOST = "http://127.0.0.1:11435"
MODEL = "qwen2.5:14b"


def test_connection():
    print(f"Testing connection to {HOST}...")
    try:
        resp = requests.get(f"{HOST}/api/tags", timeout=5)
        resp.raise_for_status()
        print("✓ API is responding")
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def test_chat():
    print("Testing chat API...")
    try:
        resp = requests.post(
            f"{HOST}/api/chat",
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": "Say 'OK' in one word"}],
                "stream": False
            },
            timeout=30
        )
        resp.raise_for_status()
        msg = resp.json().get("message", {}).get("content", "")
        print(f"✓ Chat works, response: '{msg}'")
        return True
    except Exception as e:
        print(f"✗ Chat failed: {e}")
        return False


if __name__ == "__main__":
    ok = test_connection() and test_chat()
    sys.exit(0 if ok else 1)