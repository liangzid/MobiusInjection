# Ollama Deployment Guide

## Overview
Local Ollama LLM API service running on this GPU server.

## Quick Start
```bash
cd ~/AgentCodingDos/localserver && ./start_ollama.sh
```

## Configuration
- **Host**: `127.0.0.1:11435`
- **Model**: `qwen2.5:14b`
- **GPU**: GPU 1 (via `CUDA_VISIBLE_DEVICES=1`)

## Start Script
Run `start_ollama.sh` to start the service. The script sets:
- `OLLAMA_HOST=127.0.0.1:11435`
- `CUDA_VISIBLE_DEVICES=1`

## Direct Start Command
```bash
env OLLAMA_HOST=127.0.0.1:11435 CUDA_VISIBLE_DEVICES=1 ollama serve
```

## API Endpoints

### List Models
```bash
curl http://127.0.0.1:11435/api/tags
```

### Chat API
```bash
curl http://127.0.0.1:11435/api/chat \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5:14b", "messages": [{"role": "user", "content": "Hello"}], "stream": false}'
```

## Files
- `start_ollama.sh` - Service startup script
- `ollama.log` - Server log output
- `test_ollama.py` - Validation test script
- `ollama_proxy_logger.py` - Local API proxy that records request latency,
  byte sizes, status codes, and Ollama token counts to JSONL

## Run Tests
```bash
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost python3 test_ollama.py
```

The server environment may define `http_proxy`, `https_proxy`, and `all_proxy`.
Set `NO_PROXY`/`no_proxy` for localhost requests; otherwise local Ollama API
calls can be routed through the proxy and return `502 Bad Gateway`.

## Local Logging Proxy

For Plan A experiments, run a proxy on a separate local port and point agents to
the proxy instead of directly to Ollama:

```bash
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost \
  uv run python localserver/ollama_proxy_logger.py \
  --host 127.0.0.1 \
  --port 11436 \
  --upstream http://127.0.0.1:11435 \
  --log-path experiments/logs/ddos_plan_a/ollama_proxy.jsonl
```

The proxy preserves normal Ollama API behavior while appending one JSON record
per request.
