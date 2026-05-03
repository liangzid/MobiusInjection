# Plan A Preflight: Local LLM DDoS Efficiency Trial

Date: 2026-05-02

## Purpose

This note records the hardware and local Ollama environment assessment before the first Plan A trial. The goal is to decide whether this server can support a local LLM resource-amplification experiment and what configuration should be used first.

## Hardware Environment

- CPU: 2 sockets, 96 physical cores / 192 threads.
- CPU model: Intel Xeon Platinum 8457C.
- Memory: 503 GiB total, about 163 GiB available during inspection.
- Swap: 2 GiB total, fully used during inspection.
- GPU: 6 x NVIDIA H100 NVL, each with about 95.8 GiB VRAM.
- GPU availability during inspection:
  - GPU 0: idle, about 4 MiB used.
  - GPU 1: idle before Ollama test, then about 15.3 GiB used by qwen2.5:14b.
  - GPU 2: idle, about 4 MiB used.
  - GPU 3: occupied by a VLLM engine, about 69.4 GiB used.
  - GPU 4: occupied by a VLLM engine, about 36.8 GiB used.
  - GPU 5: mostly idle, about 48 MiB used.
- Disk:
  - `/`: 879 GiB total, 77 GiB available, 91% used.
  - `/home`: 14 TiB total, 456 GiB available, 97% used.

## Current Load and Risk

- The machine has high available compute capacity, but it is already busy.
- `top` showed about 7,272 tasks, 107 zombie processes, and load average around 32.
- Several long-running Docker/mobile-world containers are active.
- Disk pressure is the main operational risk: `/home` is 97% used.
- Plan A should write compact logs and avoid storing large raw transcripts or packet captures during the first run.

## Local Ollama Environment

- Ollama version: 0.16.1.
- Existing local service:
  - `127.0.0.1:11435`, owned by user `zi`, configured by `localserver/start_ollama.sh`.
  - `127.0.0.1:11434`, owned by system user `ollama`.
- Existing model on `11435`:
  - `qwen2.5:14b`
  - size: about 9.0 GB on disk.
  - model family: qwen2.
  - parameters: about 14.8B.
  - quantization: Q4_K_M.
- Runtime after validation:
  - `qwen2.5:14b` loaded as about 17 GB runtime size.
  - processor: 100% GPU.
  - context: 32768.
  - GPU 1 memory rose to about 15.3 GiB.

## Proxy Issue Found

The shell environment defines:

- `http_proxy=http://127.0.0.1:10808`
- `https_proxy=http://127.0.0.1:10808`
- `all_proxy=socks5://127.0.0.1:10808`

Without `NO_PROXY`/`no_proxy`, local HTTP clients such as `curl` and Python `requests` route `127.0.0.1:11435` through the proxy and receive `502 Bad Gateway`.

Use:

```bash
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost
```

for all local Ollama tests and experiment scripts.

## Validation Result

Command:

```bash
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost uv run python localserver/test_ollama.py
```

Result:

- `/api/tags`: passed.
- simple chat: passed, response `Hello`.
- math reasoning: passed, response `4`.
- total: 3/3 tests passed.

## Local Proxy Smoke Result

A lightweight Ollama-compatible proxy/logger was added at:

- `localserver/ollama_proxy_logger.py`

Validation:

- Unit tests passed: `uv run pytest experiments/AgentCallInterface/tests/test_ollama_proxy_logger.py -q`
- Syntax check passed: `python3 -m py_compile localserver/ollama_proxy_logger.py`
- Real local proxy smoke request passed:
  - proxy: `127.0.0.1:11436`
  - upstream: `127.0.0.1:11435`
  - model: `qwen2.5:14b`
  - prompt: `Say OK in one word`
  - response: `OK`

The proxy wrote one JSONL record with:

- `status_code=200`
- `prompt_eval_count=34`
- `eval_count=2`
- `total_tokens=36`
- `latency_ms` about 163.6 ms

This confirms Plan A can collect per-request latency, byte size, status, and Ollama token-count metrics without relying only on Ollama server logs.

## Recommended First Plan A Trial

Use a conservative smoke experiment first:

- Server: existing Ollama on `127.0.0.1:11435`.
- Model: `qwen2.5:14b`, because it is already installed and validated.
- GPU: GPU 1 as currently configured by `localserver/start_ollama.sh`.
- Agent: OpenClaw or Hermes; prefer the one with the most stable ADD-S result from existing effectiveness runs.
- Attack: ADD-S first, because it has high prior effectiveness and gives a clean component-level path.
- Time window:
  - benign run: 5 minutes;
  - poisoned run: 5 minutes;
  - extend to 10 minutes only after log volume and server stability are confirmed.
- Required logging:
  - local LLM request count;
  - latency;
  - prompt/completion token counts if available from Ollama response fields;
  - Docker stats snapshots;
  - `nvidia-smi` snapshots;
  - P-ASR/T-ASR/R-ASR verifier outputs.

## Model Choice Recommendation

For the first trial, use `qwen2.5:14b`.

Rationale:

- already installed;
- validated through Ollama;
- fits comfortably on one H100;
- large enough to produce meaningful latency/token-cost measurements;
- avoids downloading new models while `/home` is already 97% used.

Later model options:

- smaller model for high-N scaling and saturation experiments;
- larger model for latency-sensitive cost amplification if disk and GPU scheduling allow.

## Go / No-Go

Go for a small Plan A smoke run after adding a lightweight local proxy/logger or confirming that Ollama response logs expose enough request/token/latency data.

Do not start multi-zombie scaling until:

- disk log budget is fixed;
- proxy/no-proxy behavior is handled in scripts;
- one benign-vs-poisoned single-zombie run produces clean metrics.
