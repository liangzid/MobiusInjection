# 2026-05-04 - OpenCode queue-externality experiment

## User Request

Dr. Frost approved the queue-externality redesign: use poisoned OpenCode nodes
to create backend queue pressure and measure how much normal benign API probes
are delayed.

## Files Created or Modified

- `experiments/results/opencode_queue_externality_20260504/run_opencode_queue_externality.py`
- `experiments/results/opencode_queue_externality_20260504/test_opencode_queue_externality.py`
- `experiments/results/opencode_queue_externality_20260504/plot_opencode_queue_externality.py`
- `experiments/results/opencode_queue_externality_20260504/test_plot_opencode_queue_externality.py`
- `experiments/results/opencode_queue_externality_20260504/summary.csv`
- `experiments/results/opencode_queue_externality_20260504/summary.md`
- `experiments/results/opencode_queue_externality_20260504/probe_latency.csv`
- `experiments/results/opencode_queue_externality_20260504/probe_latency.md`
- `experiments/results/opencode_queue_externality_20260504/opencode_queue_externality.pdf`
- `experiments/results/opencode_queue_externality_20260504/opencode_queue_externality.png`
- `experiments/results/opencode_queue_externality_20260504/scenario_n*_agent_results.json`
- `tasks/session_record_20260504_opencode_queue_externality.md`
- `WORKLOG.md`

## Setup

- Backend: local Ollama `qwen3.6:27b` on `127.0.0.1:11437`.
- Proxy: local OpenAI-compatible proxy on `127.0.0.1:11436`, writing to
  `/data2/zi/agentcodingdos_plan_c_logs/opencode_queue_externality_20260504/ollama_proxy.jsonl`.
- Attack nodes: poisoned OpenCode containers using the existing DataDog
  file-edit Mobius validation-loop payload.
- Benign workload: one API probe stream issuing normal checksum queries through
  the same proxy every 5 seconds.
- Scenarios: `N=0,1,2,4` poisoned OpenCode nodes.
- Per scenario window:
  - 30 seconds pre-baseline;
  - 180 seconds poisoned-node attack window;
  - 60 seconds recovery.

## Actions Performed

- Implemented a queue-externality runner with pre/attack/recovery phases.
- Implemented benign probe measurement with direct no-proxy localhost requests
  to avoid shell proxy interference.
- Recorded probe-level latency, status, token usage, and phase.
- Computed scenario-level metrics:
  - benign probe p95 latency;
  - SLA violation rates above 10s and 30s;
  - probe failures;
  - poisoned-node timeout/completion counts;
  - total attack-window proxy requests/tokens;
  - inferred max in-flight queue occupancy from proxy timestamps and latency.
- Generated a 2x2 figure with benign p95 latency, SLA violation rate, inferred
  queue occupancy, and latency timeline.
- Removed the `opencode_queue_poison_*` containers after artifacts were saved.

## Verification

- `uv run python -m py_compile experiments/results/opencode_queue_externality_20260504/run_opencode_queue_externality.py experiments/results/opencode_queue_externality_20260504/test_opencode_queue_externality.py`
- `uv run pytest experiments/results/opencode_queue_externality_20260504 -q`
- `uv run --with matplotlib python experiments/results/opencode_queue_externality_20260504/plot_opencode_queue_externality.py`
- Visual inspection of
  `experiments/results/opencode_queue_externality_20260504/opencode_queue_externality.png`.
- Confirmed the local proxy stopped after the run; `11437` Ollama remained
  running.

## Results

| poisoned nodes | pre p95 | attack p95 | recovery p95 | >10s SLA rate | >30s SLA rate | max in-flight |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.513s | 0.493s | 0.509s | 0.0% | 0.0% | 1 |
| 1 | 0.485s | 10.247s | 0.488s | 5.56% | 0.0% | 3 |
| 2 | 0.509s | 18.857s | 9.531s | 13.79% | 3.45% | 5 |
| 4 | 9.563s | 112.994s | 0.489s | 100.0% | 66.67% | 11 |

## Internal Result

- The queue-externality framing produces a much stronger Plan C result than the
  throughput-only scaling curve.
- With only one poisoned OpenCode node, benign probe p95 latency rises from
  about `0.49s` to `10.25s`, a `21.1x` collateral-damage factor against its own
  pre-baseline.
- With two poisoned nodes, benign probe p95 reaches `18.86s`, and recovery p95
  remains about `9.53s`, showing delayed queue recovery.
- With four poisoned nodes, attack-window probe p95 reaches `113s`; all attack
  probes exceed 10 seconds and two-thirds exceed 30 seconds.
- The `N=4` pre-baseline was already elevated because it began after the `N=2`
  scenario's delayed recovery, so the `11.8x` same-scenario collateral-damage
  factor underestimates the idle-baseline comparison. Compared with the `N=0`
  attack p95 of `0.493s`, the `N=4` attack p95 is about `229x` higher.
