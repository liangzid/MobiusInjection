# Session Record: HumanEval Minimax Log Analysis

Date: 2026-04-23

User request:
- Analyze the latest HumanEval experiment results under `experiments/logs/humaneval_minimax_benchmark/full_three_coding_agents_humaneval_current_prompt_20260422_232736`.
- Write Python or shell scripts to parse log results.
- Compute skill-injection success rates, tool-call counts, and related metrics grouped by agent type.
- Store grouped statistics and produce an analysis report with insights.

Files planned for this task:
- `experiments/AgentCallInterface/evaluation/humaneval_log_analysis.py`
- `experiments/scripts/analyze_humaneval_minimax_logs.py`
- `experiments/AgentCallInterface/tests/test_humaneval_log_analysis.py`
- `experiments/logs/humaneval_minimax_benchmark/full_three_coding_agents_humaneval_current_prompt_20260422_232736/agent_metric_analysis/`
- `tasks/session_record_20260423_humaneval_minimax_log_analysis.md`

Implementation notes:
- Added a structured analyzer that reads the run `manifest.json`, per-case metrics JSON, analysis JSON, and derived API metrics JSON.
- The analyzer marks cases as `completed` only when both metrics and analysis JSON exist.
- Missing manifest entries are retained as `missing` so planned coverage is visible and incomplete work is not counted as a failed injection.
- Metrics are grouped by agent type and written as JSON, CSV, and Markdown.
- Added tests that read the real HumanEval run logs instead of synthetic or mocked metrics.

Verification and results:
- `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest experiments/AgentCallInterface/tests/test_humaneval_log_analysis.py`: failed before test collection because `pyarrow==24.0.0` has no CPython 3.12 wheel/source distribution for this platform.
- `PYTHONPATH=. python3 -m pytest experiments/AgentCallInterface/tests/test_humaneval_log_analysis.py`: 3 passed.
- `python3 -m py_compile experiments/AgentCallInterface/evaluation/humaneval_log_analysis.py experiments/scripts/analyze_humaneval_minimax_logs.py`: passed.
- `PYTHONPATH=. python3 experiments/scripts/analyze_humaneval_minimax_logs.py --run-dir experiments/logs/humaneval_minimax_benchmark/full_three_coding_agents_humaneval_current_prompt_20260422_232736`: generated the analysis outputs.

Generated output files:
- `experiments/logs/humaneval_minimax_benchmark/full_three_coding_agents_humaneval_current_prompt_20260422_232736/agent_metric_analysis/full_humaneval_analysis.json`
- `experiments/logs/humaneval_minimax_benchmark/full_three_coding_agents_humaneval_current_prompt_20260422_232736/agent_metric_analysis/agent_summary.csv`
- `experiments/logs/humaneval_minimax_benchmark/full_three_coding_agents_humaneval_current_prompt_20260422_232736/agent_metric_analysis/case_metrics.csv`
- `experiments/logs/humaneval_minimax_benchmark/full_three_coding_agents_humaneval_current_prompt_20260422_232736/agent_metric_analysis/analysis_report.md`
- `experiments/logs/humaneval_minimax_benchmark/full_three_coding_agents_humaneval_current_prompt_20260422_232736/agent_metric_analysis/by_agent/claude_code_summary.json`
- `experiments/logs/humaneval_minimax_benchmark/full_three_coding_agents_humaneval_current_prompt_20260422_232736/agent_metric_analysis/by_agent/kilo_code_summary.json`
- `experiments/logs/humaneval_minimax_benchmark/full_three_coding_agents_humaneval_current_prompt_20260422_232736/agent_metric_analysis/by_agent/opencode_summary.json`
- `experiments/logs/humaneval_minimax_benchmark/full_three_coding_agents_humaneval_current_prompt_20260422_232736/agent_metric_analysis/by_agent/*_cases.csv`

Internal result summary:
- Planned cases: 492.
- Completed cases with metrics and analysis JSON: 202.
- Missing/incomplete manifest cases: 290.
- Overall skill-injection success rate over completed cases: 0.708.
- Overall runner success rate over completed cases: 0.505.
- Overall timeout rate over completed cases: 0.282.
- Overall function/tool-call evidence count: 8,557.
- Native JSON-style tool-call events: 0; tool-call totals came from textual function/tool-call evidence.

Per-agent insight summary:
- `opencode`: 68/164 completed, skill-injection rate 0.956, skills-visible rate 0.956, runner-success rate 0.691, timeout rate 0.632, average calls 68.35, total calls 4,648.
- `kilo_code`: 67/164 completed, skill-injection rate 0.896, skills-visible rate 0.896, runner-success rate 0.806, timeout rate 0.209, average calls 46.96, total calls 3,146.
- `claude_code`: 67/164 completed, skill-injection rate 0.269, skills-visible rate 0.955, runner-success rate 0.015, timeout rate 0.000, average calls 11.39, total calls 763.
- Injected cases averaged 56.00 function/tool-call evidence hits, while non-injected cases averaged 9.31.
