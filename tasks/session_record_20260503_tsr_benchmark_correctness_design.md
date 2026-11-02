# Session Record: TSR Benchmark Correctness Design

Date: 2026-05-03

## User Request

Dr. Frost clarified that TSR should not mean only that the run completed. TSR should also require benchmark correctness: a case should count as success only if the benchmark result passes at least one test. The user asked how to design the testing or monitoring process.

## Files Checked

- `experiments/AgentCallInterface/coding_evaluation/opencode_add_skill_preflight.py`
- `experiments/AgentCallInterface/coding_evaluation/edit_skill_evaluation_analysis.py`
- `experiments/AgentCallInterface/coding_datasets/coding_benchmark_loader.py`
- Existing shell benchmark runners that invoke `uv run pytest` on verifier directories.

## Current Behavior

- Current OpenCode preflight smoke sets `TSR` from OpenCode runtime status only: `status == "ok"`.
- Current edit-skill analysis also maps `TSR` to `runner_succeeded`.
- This means a case can count as TSR success even if the generated HumanEval or SWE-bench solution fails all benchmark tests.

## Recommended Design

Separate runtime completion from benchmark correctness:

- `runner_succeeded`: OpenCode call returned without timeout/provider/runtime failure.
- `benchmark_test_ran`: verifier was executed and produced parseable results.
- `benchmark_tests_total`: number of tests/checks executed.
- `benchmark_tests_passed`: number of tests/checks passed.
- `benchmark_any_test_passed`: `benchmark_tests_passed >= 1`.
- `benchmark_all_tests_passed`: all verifier tests passed.
- `TSR`: `runner_succeeded and benchmark_any_test_passed`.
- Optional stricter metric: `FULL_TSR` or `STRICT_TSR`: `runner_succeeded and benchmark_all_tests_passed`.

For HumanEval, the monitor should extract the model's function implementation into a temporary candidate file, combine it with the dataset's `test` and `entry_point`, run the real tests with `uv run`, and parse the pass/fail count. For SWE-bench, the monitor should run the repo-specific verifier or pytest command after applying the generated patch.

## Result

No code was changed beyond this record. The conclusion is that formal serial experiments should not start with the old TSR definition if correctness-sensitive TSR is required; a verifier stage should be added first.
