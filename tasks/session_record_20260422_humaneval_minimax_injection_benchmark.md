# HumanEval MiniMax Injection Benchmark Session Record

Date: 2026-04-22

## User Request

Dr. Frost asked to implement the previous agent's MiniMax HumanEval injection
benchmark plan in a fresh context. The target behavior is to place the
HumanEval task prompt before the TEMPLATE_V3/basic injection prompt, run the
coding-agent benchmark with MiniMax, support compact logs, and produce
aggregated JSON/CSV/Markdown results.

## Files Changed

- `experiments/AgentCallInterface/datasets/coding_benchmark_loader.py`
- `experiments/AgentCallInterface/evaluation/prompt_composer.py`
- `experiments/AgentCallInterface/evaluation/benchmark_manifest.py`
- `experiments/AgentCallInterface/evaluation/benchmark_analysis.py`
- `experiments/AgentCallInterface/evaluation/log_retention.py`
- `experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`
- `experiments/scripts/1.0.1.run_minimax_coding_agents_full_eval.sh`
- `experiments/scripts/1.0.2.run_minimax_humaneval_injection_benchmark.sh`
- `experiments/AgentCallInterface/tests/test_dataset_loaders.py`
- `experiments/AgentCallInterface/tests/test_prompt_composer.py`
- `experiments/AgentCallInterface/tests/test_benchmark_manifest.py`
- `experiments/AgentCallInterface/tests/test_coding_eval_script.py`
- `experiments/AgentCallInterface/tests/test_humaneval_benchmark_script.py`
- `experiments/AgentCallInterface/tests/test_log_retention.py`
- `experiments/AgentCallInterface/tests/test_benchmark_analysis.py`
- `experiments/AgentCallInterface/tests/test_minimax_eval_script.py`
- `tasks/session_record_20260422_humaneval_minimax_injection_benchmark.md`

## Implementation Details

- Added `BenchmarkTask` and `load_benchmark_tasks()` for HumanEval.
- HumanEval now reads existing repo data from `HumanEval.jsonl` or the existing
  JSON fixture and does not download data for benchmark loading.
- Added `limit`, `offset`, and `task_ids` filtering.
- Added `compose_benchmark_injection_prompt()` with task-before-injection order,
  a fixed delimiter, and length metadata.
- Added deterministic manifest generation with safe task-id path conversion.
- Added a HumanEval MiniMax wrapper script with `DRY_RUN`, `LIMIT`, `OFFSET`,
  `TASK_IDS`, `CODING_EVAL_AGENTS`, and default MiniMax settings.
- Updated the single-case coding eval script to read composed prompts from a
  file, avoiding inline shell/Python string interpolation of HumanEval docstrings.
- Added benchmark metadata to metrics: dataset, task id, prompt order, delimiter,
  and prompt lengths.
- Added compact log retention decisions that keep raw logs only for failures,
  timeouts, runtime failures, skill visibility/injection, persistence markers, or
  recursive triggers.
- Added benchmark aggregation into `benchmark_summary.json`,
  `benchmark_summary.csv`, and `benchmark_report.md`.
- Updated the existing MiniMax full-eval wrapper to point to the current
  `1.0.1.run_basic_coding_agent_eval_v3.sh` script path.

## Verification

The default uv cache path was read-only under the sandbox, so tests were run
with `UV_CACHE_DIR=/tmp/uv-cache`.

- `uv run --no-sync pytest experiments/AgentCallInterface/tests/test_dataset_loaders.py`
  with writable uv cache: passed, 10 tests.
- `uv run --no-sync pytest experiments/AgentCallInterface/tests/test_prompt_composer.py experiments/AgentCallInterface/tests/test_benchmark_manifest.py`
  with writable uv cache: passed, 6 tests.
- `uv run --no-sync pytest experiments/AgentCallInterface/tests/test_benchmark_analysis.py experiments/AgentCallInterface/tests/test_log_retention.py`
  with writable uv cache: passed, 5 tests.
- `uv run --no-sync pytest experiments/AgentCallInterface/tests/test_coding_eval_script.py experiments/AgentCallInterface/tests/test_humaneval_benchmark_script.py experiments/AgentCallInterface/tests/test_minimax_eval_script.py`
  with writable uv cache: passed, 13 tests.
- Full focused acceptance grouping:
  - dataset/prompt/manifest tests: passed, 16 tests.
  - coding eval + HumanEval wrapper tests: passed, 11 tests.
  - retention + aggregation tests: passed, 5 tests.
- `bash -n experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`: passed.
- `bash -n experiments/scripts/1.0.2.run_minimax_humaneval_injection_benchmark.sh`: passed.
- `DRY_RUN=1 LIMIT=2 CODING_EVAL_AGENTS=opencode bash experiments/scripts/1.0.2.run_minimax_humaneval_injection_benchmark.sh`: passed and listed 2 cases:
  - `HumanEval/0` with `opencode`
  - `HumanEval/1` with `opencode`

## Internal Notes

- The optional real smoke run was not executed automatically because it would
  call OpenRouter with the MiniMax model and operate on Docker containers. The
  dry run verified manifest generation, task prompt files, defaults, and case
  selection without API cost.
- Existing unrelated worktree changes and untracked dataset directories were
  left untouched.
