# Session Record: Paper Metrics Analysis

Date: 2026-04-28

## User Request

Create a new result file under `experiments/results` for paper-ready metrics from the existing injection experiment outputs:

1. Measure task execution behavior in injection experiments and determine whether baseline execution should be used.
2. Measure whether skills were injected and whether skill files were produced.
3. Compare regular function/tool calls with skill calls after injection, including call frequency and loop evidence.

The user also asked to copy or create a separate Python/shell script if current analysis methods are insufficient, and to inspect agent-specific output formats.

## Files Added

- `experiments/AgentCallInterface/evaluation/paper_metrics.py`
- `experiments/scripts/analyze_paper_metrics.py`
- `experiments/AgentCallInterface/tests/test_paper_metrics.py`
- `experiments/results/paper_metrics/qwen36plus_final/paper_metrics.json`
- `experiments/results/paper_metrics/qwen36plus_final/paper_case_metrics.csv`
- `experiments/results/paper_metrics/qwen36plus_final/paper_agent_metrics.csv`
- `experiments/results/paper_metrics/qwen36plus_final/paper_metrics_report.md`
- `tasks/session_record_20260428_paper_metrics_analysis.md`

## Actions Performed

- Inspected existing `experiments/results` CSV summaries and current analysis code in `benchmark_analysis.py`, `humaneval_log_analysis.py`, and `mobius_monitor.py`.
- Inspected real qwen36plus baseline and injection manifests, metrics JSON files, API metrics, follow-up files, and raw agent output logs.
- Confirmed existing analysis already reports runner success, skill injection, skill file creation, recursive markers, and coarse function/tool-call totals.
- Confirmed existing analysis does not provide a paper-focused combined file that:
  - matches injection cases to baseline task execution by dataset/task/agent;
  - separates skill file creation from skill calls;
  - separates regular native tool calls from native skill-tool calls and explicit slash-skill invocation evidence.
- Added a standalone paper metrics module and CLI wrapper.
- Implemented agent-aware raw output parsing for Claude Code JSON stream logs and opencode/kilo JSONL logs.
- Added `path#agents=...` run specs so paper metrics can combine final selected agents without double-counting reruns.
- Added tests using real experiment artifacts only.

## Results

- Generated paper metrics in `experiments/results/paper_metrics/qwen36plus_final/`.
- Final generated summary:
  - total cases: 300
  - completed cases: 291
  - task run success rate: 0.7628865979381443
  - skill injection rate: 0.6219931271477663
  - skill file creation rate: 0.6735395189003437
  - regular tool calls: 5378
  - skill call events: 515
  - loop suspected rate: 0.8865979381443299

## Internal Notes

- Task execution is currently measured as existing runner/API success, not HumanEval/SWE-bench correctness. The available generated artifacts do not contain a separate correctness-pass metric.
- Baseline execution is matched by `(dataset, task_id, agent)` when baseline directories are supplied.
- Native skill-tool calls are separate from slash-skill evidence. In the inspected samples, native `Skill` tool calls are rare or absent; many skill-call signals are explicit slash-skill evidence in assistant/follow-up text.
- `uv run` without `--no-sync` failed because dependency resolution selected `pyarrow==24.0.0`, which has no Linux wheel for this platform. Validation and generation used `uv run --no-sync` because the new module uses only the Python standard library.

## Verification

- `env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=/home/zi/AgentCodingDos_CodeAgent uv run --no-sync pytest experiments/AgentCallInterface/tests/test_paper_metrics.py -q`
- Result: 3 passed in 0.28s
