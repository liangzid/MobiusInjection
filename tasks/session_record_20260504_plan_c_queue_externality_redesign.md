# 2026-05-04 - Plan C queue-externality redesign

## User Request

Dr. Frost said the first OpenCode Plan C scaling result was not compelling
enough and proposed reframing the experiment around queue externality: a small
number of poisoned nodes should create latency/queue pressure that delays many
normal users or benign API queries. Dr. Frost asked for more compelling metrics
and scaling evidence to show the threat.

## Files/State Inspected

- GPU state via `nvidia-smi`.
- Listening local Ollama services on ports `11434`, `11435`, `11437`, and
  `11439`.
- tmux sessions `qwen36_ollama_11437` and `qwen36_ollama_11439`.
- Ollama process state via `ollama ps`.

## Observations

- The host has six H100 NVL GPUs.
- GPUs 0, 2, and 5 were nearly idle at inspection time; GPUs 1, 3, and 4 had
  substantial memory allocation.
- `127.0.0.1:11437` has `qwen3.6:27b` loaded and is backed by Ollama 0.22.1.
- `127.0.0.1:11439` is an Ollama 0.22.1 service pinned to GPU 0, but no model
  was loaded at inspection time.
- Shell proxy environment variables can interfere with direct localhost `curl`
  unless `--noproxy '*'` is used.
- The previous `N=4` run produced evidence of local queueing/saturation:
  p95 latency exceeded 120 seconds for poisoned runs, and the Ollama log showed
  aborted completion requests when clients closed connections.

## Proposed Redesign

The next Plan C experiment should measure benign probe latency under poisoned
agent load rather than only aggregate poisoned throughput. The core paper claim
should be: a small number of poisoned agents can occupy LLM backend queues and
impose large tail-latency and timeout costs on unrelated benign requests.

Recommended metrics:

- benign probe p50/p95/p99 latency;
- benign SLA violation rate, such as latency above 10s, 30s, and 60s;
- benign timeout/error rate;
- inferred queue depth from proxy records using `start_ts = ts - latency_ms/1000`;
- time-to-recovery after poisoned nodes stop;
- collateral damage factor: benign p95 latency under poisoned load divided by
  benign p95 latency on an idle backend;
- attack efficiency: benign extra waiting seconds per poisoned node or per
  poisoned LLM call.

The recommended experiment shape is a queue-externality curve:

- x-axis: number of poisoned OpenCode nodes, e.g. `0, 1, 2, 3, 4`;
- y-axis panels: benign probe p95 latency, timeout/SLA violation rate, inferred
  in-flight queue depth, and poisoned request/token pressure.

This is a better Plan C paper figure than the first throughput-only scaling
curve because it directly shows collateral damage to normal users.
