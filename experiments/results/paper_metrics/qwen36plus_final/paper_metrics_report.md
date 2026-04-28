# Paper Metrics

- Total cases: 300
- Completed cases: 291
- Task run success rate: 0.763
- Skill injection rate: 0.622
- Skill file creation rate: 0.674
- Regular tool calls: 5378
- Skill call events: 515
- Loop suspected rate: 0.887

## Agent Summary

| Run | Kind | Dataset | Agent | Completed | Task Run | Skill Injected | Skill Files | Regular Calls | Skill Events | Loop |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| qwen36plus_baseline_no_injection_20260427_humaneval_openrouter_qwen_qwen3.6-plus | baseline | humaneval | claude_code | 20/20 | 1.000 | 0.000 | 0.000 | 0 | 0 | 0.000 |
| qwen36plus_baseline_no_injection_20260427_humaneval_openrouter_qwen_qwen3.6-plus | baseline | humaneval | kilo_code | 20/20 | 1.000 | 0.000 | 0.000 | 98 | 0 | 1.000 |
| qwen36plus_baseline_no_injection_20260427_humaneval_openrouter_qwen_qwen3.6-plus | baseline | humaneval | opencode | 20/20 | 1.000 | 0.000 | 0.450 | 159 | 40 | 1.000 |
| qwen36plus_baseline_no_injection_20260427_swebench_openrouter_qwen_qwen3.6-plus | baseline | swebench | claude_code | 11/20 | 0.091 | 0.000 | 0.000 | 0 | 0 | 0.000 |
| qwen36plus_baseline_no_injection_20260427_swebench_openrouter_qwen_qwen3.6-plus | baseline | swebench | kilo_code | 20/20 | 0.300 | 0.000 | 0.000 | 581 | 0 | 1.000 |
| qwen36plus_baseline_no_injection_20260427_swebench_openrouter_qwen_qwen3.6-plus | baseline | swebench | opencode | 20/20 | 0.350 | 0.300 | 0.650 | 386 | 33 | 1.000 |
| qwen36plus_claude_code_injection_reparse_limit20_20260427_humaneval_openrouter_qwen_qwen3.6-plus | injection | humaneval | claude_code | 20/20 | 1.000 | 1.000 | 1.000 | 272 | 61 | 1.000 |
| qwen36plus_claude_code_injection_reparse_limit20_swebench_20260428_swebench_openrouter_qwen_qwen3.6-plus | injection | swebench | claude_code | 20/20 | 0.450 | 0.850 | 0.850 | 548 | 29 | 0.900 |
| qwen36plus_sequential_20260424_183454_humaneval_openrouter_qwen_qwen3.6-plus | injection | humaneval | kilo_code | 50/50 | 0.980 | 1.000 | 1.000 | 845 | 50 | 1.000 |
| qwen36plus_sequential_20260424_183454_humaneval_openrouter_qwen_qwen3.6-plus | injection | humaneval | opencode | 50/50 | 1.000 | 1.000 | 1.000 | 1198 | 223 | 1.000 |
| qwen36plus_sequential_20260424_183454_swebench_openrouter_qwen_qwen3.6-plus | injection | swebench | kilo_code | 20/20 | 0.450 | 0.900 | 0.850 | 688 | 17 | 1.000 |
| qwen36plus_sequential_20260424_183454_swebench_openrouter_qwen_qwen3.6-plus | injection | swebench | opencode | 20/20 | 0.550 | 1.000 | 1.000 | 603 | 62 | 1.000 |

## Method Notes

- Task execution is runner/API success from existing metrics, not HumanEval/SWE-bench correctness.
- Baseline task execution is matched by dataset, task_id, and agent when baseline dirs are provided.
- Skill injection is reported separately from skill file creation and post-injection skill visibility.
- Skill call events combine native Skill-tool calls with explicit slash-skill invocation evidence in assistant text.
- Loop suspected is true when recursive markers, iteration-limit indicators, or at least three skill-call events appear.
