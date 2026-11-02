# Session Record: Same-Environment Verifier Design

Date: 2026-05-03

## User Request

Dr. Frost raised a concern that an external monitor may not guarantee the same experimental environment as the agent run.

## Design Response

The concern is valid. Running verification on the host or in a different Python environment can create false failures or false successes due to dependency, interpreter, path, or filesystem differences.

Recommended design:

- Keep the monitor as the orchestrator only.
- Run benchmark verification inside the same OpenCode Docker container used by the case.
- Use the same `/opencode` workspace after the agent run.
- Write public test files into the same workspace before or after the agent run.
- Execute verification with the container's Python/uv environment via `docker exec`.
- Capture verifier stdout, stderr, exit code, and a machine-readable JSON result.
- Use the in-container verifier result as the official TSR evidence.

Recommended TSR formula:

`TSR = runner_succeeded and in_container_verifier_ran and verified_tests_passed >= 2`

Agent self-report remains diagnostic only:

- `agent_reported_tests_total`
- `agent_reported_tests_passed`
- `agent_reported_tests_failed`
- `agent_report_matches_verifier`

## Result

No production code was changed in this step. The result is a refined design: correctness verification should run inside the same OpenCode container and workspace, not in an external host-side environment.
