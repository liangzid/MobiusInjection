# Session Record: Qwen 3.6 Plus Curated Results

Date: 2026-04-28

## User Request

The user reported that the Claude Code result references were wrong because some earlier Claude Code result artifacts were missing and later baseline/injection runs were added. The user asked to organize the true data used for the paper into one folder under `experiments/results`.

Required final data composition:

1. Baseline, no injection: two benchmarks, three agents, limit 20.
2. Injection: two benchmarks, opencode and kilo_code limit 50, claude_code only valid later supplemented limit 20 data, including SWE-bench 18+2 patched cases.

## Files Changed

- Updated `experiments/AgentCallInterface/evaluation/paper_metrics.py`
- Updated `experiments/AgentCallInterface/tests/test_paper_metrics.py`
- Added `experiments/results/qwen36plus_curated_paper/README.md`
- Added `experiments/results/qwen36plus_curated_paper/source_selection.json`
- Added regenerated curated metrics under `experiments/results/qwen36plus_curated_paper/`
- Removed old incorrect generated files under `experiments/results/paper_metrics/qwen36plus_final/`
- Added `tasks/session_record_20260428_qwen36plus_curated_results.md`

## Source Selection

Baseline:

- HumanEval opencode/kilo_code: `qwen36plus_baseline_no_injection_20260427/humaneval`
- HumanEval claude_code: `qwen36plus_claude_baseline_raw_limit20_20260427/humaneval`
- SWE-bench opencode/kilo_code: `qwen36plus_baseline_no_injection_20260427/swebench`
- SWE-bench claude_code: `qwen36plus_claude_baseline_raw_limit20_20260427/swebench`

Injection:

- HumanEval opencode/kilo_code: `qwen36plus_sequential_20260424_183454/humaneval`
- HumanEval claude_code: `qwen36plus_claude_code_injection_reparse_limit20_20260427/humaneval`
- SWE-bench opencode/kilo_code: `qwen36plus_sequential_20260424_183454/swebench` using `manifest.json` plus `manifest_supplement_20260426.json`
- SWE-bench claude_code: `qwen36plus_claude_code_injection_reparse_limit20_swebench_20260428/swebench` excluding `DataDog__integrations-core-2041` and `DataDog__integrations-core-2282`, plus patch results from `qwen36plus_claude_code_injection_reparse_limit20_swebench_patch_20260428/swebench`

## Actions Performed

- Rechecked completion counts for every source manifest.
- Confirmed the earlier SWE-bench Claude baseline in `qwen36plus_baseline_no_injection_20260427` was incomplete at 11/20.
- Confirmed `qwen36plus_claude_baseline_raw_limit20_20260427` has complete Claude baseline data for both HumanEval and SWE-bench.
- Confirmed SWE-bench opencode/kilo_code limit 50 requires main manifest 20 plus supplement manifest 30.
- Extended `paper_metrics.py` to support:
  - direct manifest JSON paths;
  - `#agents=...` filters;
  - `#tasks=...` filters;
  - `#exclude_tasks=...` filters;
  - aggregated agent summaries by `(run_kind, dataset, agent)`.
- Regenerated the curated result folder.

## Results

Curated output folder:

- `experiments/results/qwen36plus_curated_paper/`

Generated summary:

- total cases: 360
- completed cases: 360
- baseline cases: 120
- injection cases: 240
- task run success rate: 0.7138888888888889
- skill injection rate: 0.6638888888888889
- skill file creation rate: 0.7055555555555556
- regular tool calls: 8204
- skill call events: 581
- loop suspected rate: 0.9583333333333334

## Verification

- `env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=/home/zi/AgentCodingDos_CodeAgent uv run --no-sync pytest experiments/AgentCallInterface/tests/test_paper_metrics.py -q`
- Result: 4 passed in 0.28s

