# Plan A local LLM smoke results - 2026-05-02

## Goal

Validate the smallest safe Plan A loop before any poisoned-agent or DDoS-style
run:

1. local Ollama server on the host,
2. local proxy/logger for request metrics,
3. one agent container routed to the local model,
4. benign one-turn prompt only.

No attack workload was executed in this smoke.

## Network result

- Host Ollama service: `127.0.0.1:11435`.
- Proxy/logger: `172.17.0.1:11436`, upstreaming to `127.0.0.1:11435`.
- Host access to `http://172.17.0.1:11436/api/tags`: success.
- Existing bridge-network containers to `172.17.0.1:11436`: timeout.
- New experiment containers with `--network host` to
  `http://172.17.0.1:11436/api/tags`: success.

Practical implication: Plan A local-agent runs should use fresh experiment
containers with `--network host`, or the host firewall/Docker bridge policy must
be changed separately. I did not change firewall rules.

## Hermes result

Config file:

- `experiments/configs/ddos_plan_a/hermes_ollama_smoke_config.yaml`

Result:

- `hermes chat -Q --max-turns 1 -q "Reply with exactly: PLAN_A_SMOKE_OK"`
  succeeded.
- Output included `PLAN_A_SMOKE_OK`.
- Session id: `20260502_073630_9f5e3d`.

Important caveats:

- Hermes requires at least a 64K configured context window. The local
  `qwen2.5:14b` Ollama runtime reports 32,768 tokens, so the smoke config uses
  `context_length: 65536` only to pass Hermes initialization for a short prompt.
- Hermes uses streaming internally even when terminal streaming display is off.
  Ollama's streaming OpenAI-compatible response did not include `usage`, so the
  proxy can record request count, latency, and bytes for Hermes, but exact token
  counts are unavailable on the Hermes streaming path unless we add a tokenizer
  or patch/force non-streaming behavior.

## OpenClaw result

Config files:

- `experiments/configs/ddos_plan_a/openclaw_ollama_config_set.json`
- `experiments/configs/ddos_plan_a/openclaw_ollama_openai_compat_config_set.json`
- `experiments/configs/ddos_plan_a/openclaw_localollama_openai_compat_config_set.json`

Results:

- Native `ollama/qwen2.5:14b` model registration succeeded; OpenClaw listed it
  as available.
- Generic `localollama/qwen2.5:14b` OpenAI-compatible registration also
  succeeded; OpenClaw listed it as available.
- OpenClaw agent turns failed with HTTP 400:
  `provider rejected the request schema or tool payload`.

Interpretation:

- Network and model discovery are not the blocker for OpenClaw.
- The blocker is likely request/tool-schema compatibility between OpenClaw's
  full agent tool payload and the current `qwen2.5:14b` Ollama endpoint.
- This suggests `qwen2.5:14b` is adequate for a Hermes smoke, but not yet
  adequate as a drop-in OpenClaw agent backend without disabling/simplifying
  tools or switching to a newer local model with stronger tool-call compatibility.

## Proxy/logger changes verified

Updated:

- `localserver/ollama_proxy_logger.py`
- `experiments/AgentCallInterface/tests/test_ollama_proxy_logger.py`

Verification:

- `uv run pytest experiments/AgentCallInterface/tests/test_ollama_proxy_logger.py -q`
  passed: 4 tests.
- `python3 -m py_compile localserver/ollama_proxy_logger.py` passed.

Log file:

- `experiments/logs/ddos_plan_a/ollama_proxy_bridge_20260502.jsonl`
- 14 records after the smoke attempts.

## Next decision

For the first real Plan A micro-benchmark, Hermes is the viable starting agent.
The next run should compare:

1. direct local Ollama request baseline,
2. Hermes benign one-turn baseline,
3. Hermes poisoned-agent one-turn or short-window ADD-S/Mobius behavior,

all under strict time limits and with the proxy/logger enabled.

OpenClaw should be revisited after either selecting a better tool-calling local
model or reducing the OpenClaw tool schema for local smoke runs.
