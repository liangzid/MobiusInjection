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

## Qwen3 Background Launch

Date: 2026-04-24

User request:

- Confirm the new script can produce expected experiment artifacts before launch.
- Start the Qwen3 experiment in the background.

Validation performed:

- Ran Bash syntax check for `experiments/scripts/1.0.3.run_free_models_humaneval_injection_benchmark.sh`.
- Ran Qwen3 dry-run with `LIMIT=2` and all three agents.
- Confirmed dry-run generated 6 cases: 2 HumanEval tasks times 3 agents.
- Confirmed manifest entries include `metrics_file`, `analysis_file`, `output_file`, `followup_file`, `injection_file`, `log_file`, and `task_prompt_file`.
- Confirmed all artifact paths are under the model run directory.
- Confirmed the base eval script writes `*_metrics.json`, `*_output.txt`, `*_analysis.json`, and per-case logs using the same `LOG_DIR`, `EVAL_ID`, and `AGENT_NAME` scheme.

Launch result:

- First `nohup` launch exited early after printing config only; no manifest was produced.
- Relaunched with `setsid` so the process is detached from the shell session.
- Running PID: `3012756`.
- Run directory: `experiments/logs/humaneval_free_models_benchmark/qwen3_humaneval_20260424_103235`.
- Launcher log: `experiments/logs/humaneval_free_models_benchmark/qwen3_humaneval_20260424_103235/launcher.log`.
- Model: `openrouter/qwen/qwen3-coder:free`.
- Agents: `opencode,kilo_code,claude_code`.
- Limit: `50`.
- Confirmed active process after launch.
- Confirmed manifest with 150 cases was generated.
- Confirmed `worker_opencode.log`, `worker_kilo_code.log`, and `worker_claude_code.log` were generated.
- Confirmed first case artifacts began appearing, including per-case logs, prompt metadata, metrics JSON, and output text.

## Qwen3 Status Check

Date: 2026-04-24

User request:

- Check the current status of the Qwen3 background experiment.

Observed status:

- Background launcher PID `3012756` is still running.
- Elapsed runtime at check: about 51 minutes.
- Run directory remains `experiments/logs/humaneval_free_models_benchmark/qwen3_humaneval_20260424_103235`.
- Total files under the run directory at check: 1332.
- `opencode` completed all 50 HumanEval tasks.
- `kilo_code` had metrics through `HumanEval/27` and was actively running around `HumanEval/27`.
- `claude_code` had metrics through `HumanEval/13` and its worker log showed it was in the `HumanEval/13` injection call.
- Final aggregate files were not present yet because the wrapper waits for all agent workers to finish before running retention and benchmark aggregation.

## Qwen3 Result Analysis And Stop Decision

Date: 2026-04-24

User request:

- Use the previous HumanEval log-analysis method to evaluate the new Qwen3 result.
- If results have enough successful injection behavior, continue to launch two more fixed-model experiments for `qwen3.6plus`: HumanEval and SWE-bench.
- If there are no successful cases or success rate is very poor, stop and notify the user first.

Analysis performed:

- Re-ran the HumanEval analysis script:
  - `PYTHONPATH=/home/zi/AgentCodingDos_CodeAgent uv run --no-sync python experiments/scripts/analyze_humaneval_minimax_logs.py --run-dir experiments/logs/humaneval_free_models_benchmark/qwen3_humaneval_20260424_103235/models/openrouter_qwen_qwen3-coder_free --output-dir experiments/logs/humaneval_free_models_benchmark/qwen3_humaneval_20260424_103235/models/openrouter_qwen_qwen3-coder_free/agent_metric_analysis`
- Generated:
  - `agent_metric_analysis/full_humaneval_analysis.json`
  - `agent_metric_analysis/agent_summary.csv`
  - `agent_metric_analysis/case_metrics.csv`
  - `agent_metric_analysis/analysis_report.md`

Results:

- Planned cases: 150.
- Completed cases: 150.
- Missing cases: 0.
- Overall runner success rate: 0.333.
- Overall skill injection success rate: 0.000.
- Overall skills visible rate: 0.000.
- Overall persistence rate: 0.000.
- Overall recursive trigger rate: 0.000.
- `opencode`: 50/50 completed, runner success 0.000, injection success 0.000.
- `kilo_code`: 50/50 completed, runner success 1.000, injection success 0.000.
- `claude_code`: 50/50 completed, runner success 0.000, injection success 0.000.

Decision:

- The experiment did not produce any successful injection cases.
- This fails the requested threshold for continuing.
- Did not launch the follow-up `qwen3.6plus` HumanEval or SWE-bench experiments.

## Qwen3.6 Plus API Validation And Dataset Support

Date: 2026-04-24

User request:

- Treat the Qwen3 free run failure as an API/model-limit issue.
- Switch to the paid `qwen3.6plus` model.
- Do not start full experiments immediately.
- First verify that API calls work normally through all three agents.
- After all three agents are validated, proceed toward HumanEval and SWE-bench runs.

Model mapping:

- Confirmed the OpenRouter paid model id is `qwen/qwen3.6-plus`.
- Used `openrouter/qwen/qwen3.6-plus` for wrappers and direct agent smoke tests.

API validation:

- Created smoke-test logs under `experiments/logs/qwen36plus_api_smoke_20260424`.
- `opencode`: success true, return code 0, output contained `QWEN36PLUS_API_OK`.
- `kilo_code`: success true, return code 0, output contained `QWEN36PLUS_API_OK`.
- `claude_code`: first call returned success true but output was malformed (`QWENEN_`), so it was not accepted as a content validation pass.
- `claude_code` retry with a simpler prompt returned success true, return code 0, output `OK`.
- No API/model-not-found/rate-limit/free-limit markers were observed in the accepted smoke tests.

Code support added:

- Added `swebench` support to `experiments/AgentCallInterface/datasets/coding_benchmark_loader.py`.
- Added SWE-bench benchmark prompts containing repository, instance id, issue description, optional hints, and test patch.
- Fixed `CodingBenchmarkLoader.load_benchmark_tasks()` so HumanEval and SWE-bench use their own data directories.
- Parameterized `experiments/scripts/1.0.3.run_free_models_humaneval_injection_benchmark.sh` with `BENCHMARK_DATASET`, defaulting to `humaneval`.
- Added tests for SWE-bench benchmark loading and wrapper dry-run support.

Verification:

- `uv run --no-sync pytest experiments/AgentCallInterface/tests/test_dataset_loaders.py experiments/AgentCallInterface/tests/test_free_models_humaneval_benchmark_script.py`
  - Passed: 17 tests.
- HumanEval dry-run with `MODEL_NAMES=openrouter/qwen/qwen3.6-plus`, `LIMIT=1`, and three agents generated 3 cases.
- SWE-bench dry-run with `MODEL_NAMES=openrouter/qwen/qwen3.6-plus`, `LIMIT=1`, and three agents generated 3 cases.
