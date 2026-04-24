# Session Record: Free-Model HumanEval Injection Benchmark Wrapper

Date: 2026-04-24

## User Request

Create a new experiment script based on `experiments/scripts/1.0.2.run_minimax_humaneval_injection_benchmark.sh` with these changes:

- Limit HumanEval execution to the first 50 tasks instead of the full set.
- Try additional free models such as Qwen and DeepSeek.
- Run the three different coding-agent containers concurrently, while keeping tasks serial within the same agent/container.
- Ask clarifying questions by interview only if requirements are unclear.

## Files Changed

- `experiments/scripts/1.0.3.run_free_models_humaneval_injection_benchmark.sh`
- `experiments/AgentCallInterface/tests/test_free_models_humaneval_benchmark_script.py`
- `tasks/session_record_20260424_free_models_humaneval_benchmark.md`

## Implementation Notes

- Added a new `1.0.3` wrapper rather than modifying the existing MiniMax-only wrapper.
- Set default `LIMIT=50`, so the manifest loader selects `HumanEval/0` through `HumanEval/49` unless overridden.
- Added default model list:
  - `openrouter/minimax/minimax-m2.5:free`
  - `openrouter/qwen/qwen3-coder:free`
  - `openrouter/deepseek/deepseek-r1-distill-qwen-32b:free`
- Kept model batches serial because the underlying eval script uses fixed Docker container names.
- Added one background worker per agent inside each model batch, so `opencode`, `kilo_code`, and `claude_code` run concurrently.
- Kept each worker serial over its own manifest entries, so tasks do not overlap inside the same agent/container.
- Wrote separate per-agent worker logs under each model run directory to reduce concurrent log interleaving.
- Preserved eval-script snapshot behavior for reproducibility.

## Verification

- `uv run pytest experiments/AgentCallInterface/tests/test_free_models_humaneval_benchmark_script.py experiments/AgentCallInterface/tests/test_humaneval_benchmark_script.py`
  - Failed before test execution because `pyarrow==24.0.0` has no installable wheel/source for the current CPython 3.12 environment.
- `uv run --no-sync pytest experiments/AgentCallInterface/tests/test_free_models_humaneval_benchmark_script.py experiments/AgentCallInterface/tests/test_humaneval_benchmark_script.py`
  - Passed: 7 tests.

## External Model Check

- Checked OpenRouter free-model documentation and model pages on 2026-04-24.
- OpenRouter documents that free model availability changes frequently and recommends checking current model pages.
- Qwen3 Coder free and DeepSeek R1 Distill Qwen 32B free were selected as fixed `:free` model ids instead of using `openrouter/free`, because random routing would reduce experiment reproducibility.
