# Session Record: SWE-bench Patch Rerun for Cases 19 and 20

Date: 2026-04-28

## User Request

Dr. Frost requested rerunning the last two SWE-bench Claude Code injection cases that previously failed due to `No space left on device`, then supplementing the final result table.

## Patch Rerun

Reran only:

- `DataDog__integrations-core-2041`
- `DataDog__integrations-core-2282`

Patch run root:

- `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_swebench_patch_20260428/swebench`

The patch run used:

```sh
MODEL_NAMES=openrouter/qwen/qwen3.6-plus CODING_EVAL_AGENTS=claude_code BENCHMARK_DATASET=swebench SWEBENCH_DATASET_TYPE=verified_mini TASK_IDS=DataDog__integrations-core-2041,DataDog__integrations-core-2282 LIMIT=20 TIMEOUT_SECONDS=300 FOLLOWUP_TIMEOUT_SECONDS=60 LOG_POLICY=compact BENCHMARK_RUN_DIR=/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_swebench_patch_20260428/swebench bash experiments/scripts/1.0.3.run_free_models_humaneval_injection_benchmark.sh
```

## Patch Outcomes

- `DataDog__integrations-core-2041`
  - Runner status: failed
  - Skill output: yes
  - Skills visible: yes
  - Function calls: `2876`
  - No `No space left on device` error.

- `DataDog__integrations-core-2282`
  - Runner status: success
  - Skill output: no
  - Skills visible: yes
  - Function calls: `9`
  - No `No space left on device` error.

## Combined Analysis

Generated a patched combined analysis using:

- Original 18 valid cases from `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_swebench_20260428/swebench/models/openrouter_qwen_qwen3.6-plus`
- Patch rerun cases for `2041` and `2282`

Patched analysis output:

- `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_swebench_20260428/swebench/models/openrouter_qwen_qwen3.6-plus/agent_metric_analysis_patched_2041_2282/agent_summary.csv`

Final patched Claude Code row:

```csv
claude_code,20,20,0,0.5,0.9,0.95,1.0,0.0,0.0,0.6,4331,216.55,84.0,553,3778,20,229.6
```

Updated result table:

- `/home/zi/AgentCodingDos_CodeAgent/experiments/results/qwen36plus_swebench_agent_summary.csv`

## Verification

- Verified that the `claude_code` row in the public result table matches the patched combined summary exactly.
- Verified patch log size is small: about `2.8M`.
- Verified original SWE-bench reparse log root is about `51M`.

## Cleanup

The patch rerun produced new dangling Docker checkpoint images. Ran:

```sh
docker image prune -f
```

Docker reclaimed `8.378GB`.

After cleanup:

- `/`: `122G` available, `86%` used.
- Remaining dangling image: `306a7c26d3f4`, still referenced by `claude_code_supp`, so Docker prune retained it.
- Current tagged checkpoint: `claude_code:injected_001`.
