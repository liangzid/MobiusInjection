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

## Run Tests
```bash
python3 test_ollama.py
```