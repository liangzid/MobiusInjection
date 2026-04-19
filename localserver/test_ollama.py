#!/usr/bin/env python3
"""
Ollama Deployment Test Script
============================
Tests the locally deployed Ollama service on port 11435 with qwen2.5:14b model.
"""

import requests
import json
import sys

OLLAMA_HOST = "http://127.0.0.1:11435"
MODEL_NAME = "qwen2.5:14b"


def test_api_tags():
    """Test listing models via API"""
    print("[TEST 1] Testing /api/tags endpoint...")
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        print(f"  ✓ Success: {len(data.get('models', []))} model(s) available")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_simple_chat():
    """Test simple chat request"""
    print("[TEST 2] Testing simple chat request...")
    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": "Say 'Hello' in one word"}],
            "stream": False
        }
        resp = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "")
        print(f"  ✓ Response: '{content}'")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_math_question():
    """Test mathematical reasoning"""
    print("[TEST 3] Testing math reasoning...")
    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": "What is 2+2? Answer with just the number."}],
            "stream": False
        }
        resp = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "").strip()
        print(f"  ✓ Response: '{content}'")
        return content == "4"
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def main():
    print("=" * 60)
    print("OLLAMA DEPLOYMENT TEST")
    print(f"Host: {OLLAMA_HOST}")
    print(f"Model: {MODEL_NAME}")
    print("=" * 60)

    results = []
    results.append(test_api_tags())
    results.append(test_simple_chat())
    results.append(test_math_question())

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 60)

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())