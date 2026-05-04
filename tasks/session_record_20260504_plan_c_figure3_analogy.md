# 2026-05-04 - Plan C Figure 3 analogy assessment

## User Request

Dr. Frost asked whether Research Plan C can export an experiment analogous to
`~/paper_mobius/exper.tex` Figure 3, which shows Agent-DDoS resource
amplification.

## Files Inspected

- `tasks/research_plan_0502_ddos_c_multizombie_end_to_end.md`
- `/home/zi/paper_mobius/exper.tex`
- `/home/zi/paper_mobius/scripts/generated/agent_ddos_curve/local_vs_previous_2x3_curve_pairs.csv`
- `tasks/session_record_20260504_multiagent_datadog_ollama_claude_kilo.md`
- `tasks/session_record_20260503_opencode_time_window_free_run.md`
- `experiments/results/opencode_time_window_free_run_20260503/run_time_window_free_run.py`
- `experiments/results/opencode_time_window_free_run_20260503/time_window_aggregate.csv`
- `experiments/results/multiagent_datadog_fileedit_ollama_20260504/run_multiagent_datadog_fileedit_ollama.py`
- `experiments/results/multiagent_datadog_fileedit_ollama_20260504/summary_latest_claude_v2_kilo_v3.csv`

## Actions Performed

- Compared Plan C's multi-zombie scaling questions with the current Figure 3
  resource-amplification experiment.
- Checked whether existing results already contain enough multi-zombie scaling
  data.
- Identified the existing OpenCode `agent_count=2` run as insufficient for a
  Plan C main figure because it produced weak activation under the current local
  serialized backend.
- Prepared a recommendation for a Figure 3-style Plan C export.

## Result

Plan C can produce a Figure 3-analogous paper figure, but it should not reuse
the current Figure 3 axes directly. The Plan C figure should use poisoned-agent
count `N` or elapsed time under fixed `N` as the scaling axis, with completed
LLM calls, token throughput, latency, and failure/benign-collateral metrics as
outputs. Existing local data do not yet provide a strong enough multi-zombie
scaling curve; a new bounded local experiment is needed.
