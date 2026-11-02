# Session Record - Table 1/2 remote-API sample expansion - 2026-08-27

## User request

Find existing experiment code under `~/AgentCodingDos*`, understand it, then
expand Table 1/2 remote LLM API evaluations:

- HumanEval full set (164; reuse existing first 20)
- SWE-bench 80
- ClawBench four Table-1 domains at category-complete coverage

## Code locations

- Claw / Table 1: `/home/zi/AgentCodingDos` (`master`)
  - Runner: `experiments/scripts/effectivenss_injection_claw_0.2.context_injection_add_s.sh`
  - Taskset: `experiments/configs/context_injection_add_s_taskset_plan_a.toml`
  - Artifacts: `/home/zi/agentcodingdos_context_injection_runs`
- Coding ADD S. / Table 2: `/home/zi/AgentCodingDos_CodeAgent` (`codeagent/experiments-copy`)
  - Runner: `experiments/scripts/1.0.3.run_free_models_humaneval_injection_benchmark.sh`
  - Template: `CODING_AGENT_TEMPLATE_V10_LOOP`
  - Live ADD S. run: `experiments/logs/humaneval_model_benchmark/qwen36_v10_humaneval_offset20_limit144_20260827_run2`
- Coding EDIT S.: `experiments/scripts/coding_agents/run_edit_skill_evaluation_humaneval_benchmark.sh`
  - Template: `CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V37_LOOP`

## Findings that change the expansion plan

- Local SWE-bench `verified_mini.json` has only 20 instances. 80 tasks uses
  `swebench_80.json` (original 20 DataDog verified_mini + 60 Lite extras).
- Local ClawBench corpus is 319 offline tasks. Table 1 "category complete"
  means remaining tasks in document-editing / communication / email /
  code-assistance plus already-selected cross-domain IDs.
- Coding eval skips agents unless containers named `opencode`, `kilo_code`,
  and `claude_code` are already running.
- `RESTORE_KILO_BEFORE_RUN` defaults to 0. Recreating the image tag does not
  refresh the live `kilo_code` container.
- `--pids-limit=100` makes the native Kilo binary SIGABRT. Use 4096 or omit.
- Kilo's `bash -lc` login shell sources `/root/.bashrc`, which overwrites
  `OPENROUTER_API_KEY` with a stale in-image key. Project `opencode.json`
  must be written from `KILO_EVAL_OPENROUTER_KEY_B64`, not that env var.

## Actions this session

1. HumanEval ADD S. OFFSET=20 LIMIT=144 is running as `..._20260827_run2`
   (OpenCode and Claude Code: real API traces).
2. Diagnosed Kilo empty-success: native abort mapped to exit 0; caller now
   treats empty stdout as failure (`test_kilo_caller.py`).
3. Recreated `kilo_code` with `--pids-limit=4096` so the native CLI runs.
4. Kilo still 401'd because login-shell env overwrote the eval OpenRouter
   key. Caller now writes `opencode.json` / `kilo.json` from a base64 env
   var that bashrc does not clobber. HumanEval/98 is the first valid Kilo
   ADD S. row in run2 (`step_start`, ~16KB, no 401).
5. Expanded Claw `plan_a` to folder-complete Table 1 domains:
   daily-life 19, social 17, office 18, dev 18. Tests: 14 passed.
6. Fixed two setup.sh path bugs (doc-017 standups/, xdom-008 app_code/)
   so injection-target setup matches on-disk data.

## Do not put in the paper

- Run2 Kilo HumanEval/20–97 (empty abort and/or OpenRouter 401). Re-run.
- The first launch dir without `_run2` (all agents skipped).

7. Launched Claw ADD S. + calling on the 28 new plan_a task IDs
   (`RUN_ID=add_s_plan_a_newtasks_qwen36_20260827`, 3 agents, 900s/180s).
   Original 11×4 sample is reused from `add_s_eval_plan_a_20260424_1530`.

8. Queued Table 2 continuation in
   `experiments/scripts/run_table2_expansion_queue.sh`:
   wait for run2 Kilo /163, rerun Kilo HumanEval/20–97, wait for run2, then
   EDIT S. V37 HumanEval OFFSET=20 (600s/600s), SWE-80 ADD S. OFFSET=20
   (600s/180s), SWE-80 EDIT S. V37 OFFSET=20 (600s/600s).
   The queue now `unset`s `OPENROUTER_API_KEY` so queued coding evals use the
   working privacy-file key (the Cursor eval-process env key 401s).

## Next

- Let run2 OpenCode/Claude finish HumanEval/20–163; keep Kilo from /98.
- Queued Kilo 20–97 + EDIT S. + SWE-80; do not start a second coding eval
  against `opencode`/`kilo_code`/`claude_code` until the queue owns them.
- Do not expand the 12-backend HumanEval table.
- Coverage keep/discard: `experiments/scripts/report_table12_expansion_coverage.py`.
- Matrix completion audit: `experiments/scripts/expansion_matrix_coverage.py`
  (HumanEval 164 + SWE-80 + Claw 72×3×6). Original Claw 11×4 is complete
  across all 6 strategies (792/792). New-28 and coding OFFSET=20 are still
  running. ADD C / EDIT C new-28 log dirs are
  `add_c_plan_a_newtasks_qwen36_20260827_{agent}` (batch suffix), not the
  unsuffixed RUN_ID.
- Original Claw 11×4 ADD S. is the kimi v411 44-task runs, not
  `add_s_eval_plan_a_20260424_1530` (aborted probe).
- EDIT S. HumanEval first-20 reuse is minimax, not qwen; queued OFFSET=20
  expansion is qwen. Flag before writing a single-model table.

HE ADD S. run2 still live (PID 217430) ~15:32: OpenCode /84, Kilo /137
(keep 98+ only), Claude /95. Coverage humaneval_add_s 241/492 valid, 0 401
in the keep set. Table 2 queue PID 795031 still waiting for Kilo /163 then
Kilo 20–97 rerun, then EDIT S. V37 OFFSET=20 and SWE-80 OFFSET=20. Do not
start a second coding eval against the named containers.
