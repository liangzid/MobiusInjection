# 2026-05-04 Re-read Plan C for Next Experiments

## User Request

Dr. Frost asked to re-read Research Plan C and identify whether there are other
meaningful experiments to run now that the paper keeps only the queue-externality
bar chart as Figure 4.

## Files Inspected

- `tasks/research_plan_0502_ddos_c_multizombie_end_to_end.md`
- `tasks/session_record_20260504_plan_c_figure3_analogy.md`
- `tasks/session_record_20260504_opencode_plan_c_multizombie_scaling.md`
- `tasks/session_record_20260504_opencode_queue_externality.md`
- `experiments/results/opencode_multizombie_scaling_20260504/summary.csv`
- `experiments/results/opencode_queue_externality_20260504/summary.csv`

## Findings

- Figure 4 already covers the strongest current Plan C result: benign API probe
  collateral latency under poisoned OpenCode node counts `N=0,1,2,4`.
- The earlier throughput-only multi-zombie scaling run is weaker as a paper
  figure because throughput saturates by `N=4`; it is useful as supporting
  saturation evidence, not as a main result.
- The most meaningful non-duplicative next experiment is Plan C3 at the
  user-facing task level: run benign agent tasks concurrently with poisoned
  nodes and measure benign completion, wall-clock latency, request p95, and
  failures.
- The second most meaningful next experiment is Plan C4 defense under
  multi-zombie pressure: compare no defense, resource budget/rate limiting, and
  ACE quarantine on residual damage and benign utility.
- Stealth-vs-aggressive profiles and targetability are possible but require more
  setup and are less immediately aligned with the current paper gap.

## Result

Recommended next experiment: a small bounded benign-agent collateral damage
experiment with OpenCode first, using `N=0,1,2` poisoned nodes and one benign
OpenCode task sharing the same local Ollama backend. This directly upgrades the
claim from "benign API probes are delayed" to "normal agent users are delayed or
fail under poisoned-agent pressure."
