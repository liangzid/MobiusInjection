## Task

- User asked to select the ResearchPlan A batch taskset for the four experiment categories.
- The plan requirement is more than 10 and fewer than 20 tasks per category.

## Files

- `experiments/configs/context_injection_add_s_taskset_plan_a.toml`
- `experiments/AgentCallInterface/context_injection_add_s.py`
- `experiments/AgentCallInterface/tests/test_context_injection_add_s.py`

## Changes

- Added a new ResearchPlan A taskset at `experiments/configs/context_injection_add_s_taskset_plan_a.toml`.
- Selected 11 tasks for each category:
  - `daily-life`
  - `social`
  - `office`
  - `dev`
- Extended the injection helper so `json_field_append` can also target a top-level JSON object, which was needed for tasks such as `comm-001`.
- Added regression coverage for top-level JSON-object append and for the new Plan A task-count requirement.

## Validation

- `uv run pytest experiments/AgentCallInterface/tests/test_context_injection_add_s.py experiments/AgentCallInterface/tests/test_mi_v36_add_s.py -q`
- `env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=/home/zi/AgentCodingDos uv run python -m py_compile experiments/AgentCallInterface/context_injection_add_s.py`
- `env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=/home/zi/AgentCodingDos uv run python experiments/AgentCallInterface/context_injection_add_s.py print-taskset-tsv experiments/configs/context_injection_add_s_taskset_plan_a.toml | awk -F'\t' '{count[$1]++} END {for (k in count) print k, count[k]}' | sort`

## Result

- The new taskset parses successfully.
- Category counts are:
  - `daily-life 11`
  - `social 11`
  - `office 11`
  - `dev 11`

## Notes

- I kept the original seed taskset unchanged so the minimal debug/rerun workflow still exists.
- For the full batch, use `TASKSET_PATH=experiments/configs/context_injection_add_s_taskset_plan_a.toml`.
