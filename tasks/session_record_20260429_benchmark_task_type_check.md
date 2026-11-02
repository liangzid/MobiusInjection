# Session Record: Benchmark Task Type Check

## User Request

Dr. Frost asked whether HumanEval and SWE-bench have subdivisions by task type in the current experiment data.

## Files Checked

- `experiments/AgentCallInterface/coding_datasets/coding_benchmark_loader.py`
- `experiments/AgentCallInterface/evaluation/benchmark_manifest.py`
- `experiments/AgentCallInterface/datasets/HumanEval.jsonl`
- `experiments/AgentCallInterface/datasets/swebench_data/verified_mini.json`
- `experiments/results/qwen36_v10_limit20_20260428/case_metrics.csv`
- `experiments/results/qwen36_v10_limit20_20260428/task_metrics.csv`

## Result

- HumanEval has no explicit task type/category/difficulty field in the current loader or source fixture. Available fields are `task_id`, `prompt`, `canonical_solution`, `test`, and `entry_point`.
- SWE-bench verified mini in the current run has no explicit task type/category/difficulty field. Available fields include `instance_id`, `repo`, `problem_statement`, `hints`, `created_at`, `test_patch`, `repo_version`, and `HW_COST`.
- The current SWE-bench limit-20 sample is all from `DataDog/integrations-core`, so the only reliable built-in coarse grouping is repository, and it is not useful for this sample because all 20 tasks share the same repo.
- Any finer task-type analysis would need to be added as a derived annotation from issue text, affected files, tests, or repository metadata; it is not currently present in the metrics.
