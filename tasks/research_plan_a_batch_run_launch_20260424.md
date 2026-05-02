## Task

- User asked to launch the ResearchPlan A full batch experiment in the background and analyze it intermittently.

## Files

- `experiments/configs/context_injection_add_s_taskset_plan_a.toml`
- `experiments/scripts/effectivenss_injection_claw_0.2.context_injection_add_s.sh`
- `experiments/AgentCallInterface/context_injection_add_s.py`
- `experiments/AgentCallInterface/tests/test_context_injection_add_s.py`

## What Happened

- The first detached `nohup` launch using run id `add_s_eval_plan_a_20260424_1450` exited too early without useful stdout, but it exposed a real problem:
  - some Plan A injection target files were not present after `setup.sh`
- I diagnosed the failure and found two kinds of issues:
  - legacy `setup.sh` scripts that ignore the explicit workspace path and write into the task-local `workspace/`
  - two real taskset path mismatches:
    - `doc-017`: should use `standups/friday.txt`
    - `xdom-008`: should use `app_code/api.py`

## Fixes

- Added runner fallback in `build_clean_workspace()` so if a task writes to `task_dir/workspace`, those prepared inputs are copied into the requested run workspace.
- Corrected the two mismatched taskset paths in `context_injection_add_s_taskset_plan_a.toml`.
- Added a regression test that iterates the full Plan A taskset, runs each task's `setup.sh`, applies the same legacy-workspace fallback, and checks that the configured injection target exists.

## Validation

- `uv run pytest experiments/AgentCallInterface/tests/test_context_injection_add_s.py experiments/AgentCallInterface/tests/test_mi_v36_add_s.py -q`
- `bash -n experiments/scripts/effectivenss_injection_claw_0.2.context_injection_add_s.sh`
- `env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=/home/zi/AgentCodingDos uv run python -m py_compile experiments/AgentCallInterface/context_injection_add_s.py`

## Active Run

- Run id: `add_s_eval_plan_a_20260424_1530`
- Managed background session id: `73857`
- Taskset: `/home/zi/AgentCodingDos/experiments/configs/context_injection_add_s_taskset_plan_a.toml`

## Initial Status

- All 44 task stagings completed for all three agents.
- The main execution loop started successfully.
- The first real agent task reached:
  - `agent=openclaw`
  - `task=xdom-001`
  - pre-run checkpoint saved

## Notes

- The batch is running under a managed interactive session rather than `nohup`, because that is more reliable for long monitoring and periodic analysis in this environment.
