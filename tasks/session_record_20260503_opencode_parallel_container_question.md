# Session Record: OpenCode Parallel Container Feasibility

Date: 2026-05-03

## User Request

Dr. Frost asked whether the OpenCode formal experiment can now start serial execution, and whether the OpenCode Docker container can be duplicated to run multiple model experiments concurrently because running many models at `limit=20` one by one may take a long time.

## Files And Context Checked

- `experiments/AgentCallInterface/agents/agent_callers.py`
- `experiments/scripts/coding_agents/reset_opencode_zero_skill_state.sh`
- `experiments/AgentCallInterface/coding_evaluation/opencode_add_skill_preflight.py`
- Current Docker container list from `docker ps`

## Findings

- The Gate 4-8 framework is ready for conservative serial formal runs.
- Current OpenCode caller defaults to container `opencode`, but it already supports container override through `OPENCODE_CONTAINER_NAME` and task input container naming.
- The zero-skill reset script already supports `OPENCODE_CONTAINER`, so reset can target cloned containers without rewriting the reset logic.
- The current preflight/formal harness calls OpenCode through the default container path and uses helper checks that are still hardcoded to `opencode` in places. Running the existing harness concurrently without modification would risk shared workspace contamination.
- Multiple OpenCode-derived containers are already running on the host, so the environment can technically host cloned OpenCode containers.

## Answer Summary

Parallel cloned-container execution is feasible, but should be introduced as controlled worker-level parallelism:

- one Docker container per worker;
- no shared `/opencode` workspace between workers;
- reset the worker container before every case;
- write each case to a unique output directory;
- pass `OPENCODE_CONTAINER_NAME` or task input container override for every OpenCode call;
- update monitor and timeout cleanup helpers so they inspect the assigned worker container instead of hardcoded `opencode`;
- start with low concurrency, likely 2 workers, before scaling.

Recommended formal-experiment path:

1. Run a small serial official sanity slice first, such as 1 model x 2 tasks, using the current framework.
2. Add a parallel runner wrapper that creates or reuses `opencode_worker_0`, `opencode_worker_1`, etc.
3. Run a 2-worker smoke test with 2 models x 2 tasks and compare metrics/log structure against serial output.
4. If no cross-case contamination appears, use model-level or case-level concurrency with a conservative cap.

## Result

No code was changed beyond this record. The practical recommendation is: yes, cloned OpenCode containers can be used for parallelism, but the current formal runner should receive a small worker-container abstraction before a large concurrent run.
