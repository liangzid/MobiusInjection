# Cross-Model OpenCode Add-Skill Experiment Checklist - 2026-05-02

Source requirement: `tasks/session_record_20260502_cross_model_opencode_add_skill_requirements.md`

## Scope

- Fixed agent environment: OpenCode only.
- Variable under comparison: backbone model only.
- Attack surface: add exactly two OpenCode project skills, `integrity-sync` and `performance-audit`.
- Recursive behavior evidence: two skills alternately append structured rows to `sync-check-record.jsonl`.
- Per-case invariant: reset `/opencode` to a zero-skill state before each task.
- Cleanup invariant: do not commit Docker images; remove runtime artifacts after each case.

## Gate Checklist

- [x] Gate 1: Zero Skill Reset purity preliminary experiment.
  - [x] Add OpenCode-only zero-skill reset script.
  - [x] Add dry-run and static tests for the reset script.
  - [x] Pollute `/opencode` with project skills, ledgers, instruction hooks, and temp skill roots.
  - [x] Run reset once and verify all targeted roots/artifacts/hooks are absent or empty.
  - [x] Run `opencode debug skill` and verify this experiment's project-created skills are absent.
  - [x] Run reset a second time and verify idempotence.
- [x] Gate 2: OpenCode skill discovery lifecycle preliminary experiment.
  - [x] Use one known working model and a tiny real task.
  - [x] Capture same-session, restarted-session, and clean follow-up invocation evidence.
  - [x] Classify OpenCode skill discovery behavior for T-ASR/R-ASR definitions.
- [ ] Gate 3: V10 two-skill recursive JSONL write preliminary experiment.
  - [ ] Adapt the V10 payload to create exactly two skills.
  - [ ] Validate directory names and YAML `name` fields.
  - [ ] Validate alternating JSONL trace rows by `run_id` and monotonic `seq`.
  - [ ] Distinguish native skill-call evidence from weak marker-only evidence.
- [ ] Gate 4: External model configuration dry run.
  - [ ] Build a manifest with model label, exact OpenRouter model ID, dataset, task ID, agent, timeout, and run directory.
  - [ ] Fail before execution for unresolved model labels.
  - [ ] Confirm wrapper dispatches OpenCode only.
- [ ] Gate 5: Model connectivity matrix.
  - [ ] Run one minimal real OpenCode request per candidate model.
  - [ ] Classify failures as auth, unavailable model, rate limit, timeout, provider error, or network error.
- [ ] Gate 6: Timeout and cleanup preliminary experiment.
  - [ ] Confirm hung `opencode run --dir /opencode` processes are killed.
  - [ ] Confirm repeated runs do not grow Docker images or fill `/`.
- [ ] Gate 7: Result aggregation smoke test.
  - [ ] Produce current-style result files plus per-model comparison tables.
  - [ ] Keep timeout/runtime failures in denominators.
- [ ] Gate 8: Cost, rate-limit, and scheduling preliminary experiment.
  - [ ] Record latency and rate-limit behavior for all candidate models.
  - [ ] Set final timeout/scheduling policy.

## Preliminary Experiment 1 Result

- Status: passed.
- Script: `experiments/scripts/coding_agents/reset_opencode_zero_skill_state.sh`.
- Tests: `experiments/AgentCallInterface/tests/test_reset_opencode_zero_skill_state_script.py`.
- Detailed record: `tasks/session_record_20260502_preliminary_experiment_1_zero_skill_reset.md`.
- Live container: `opencode`.
- Verification:
  - `/opencode/.opencode/skills`, `/opencode/.agents/skills`, `/opencode/.claude/skills`, `/opencode/.kilo/skills`, `/opencode/.kilocode/skills`, `/opencode/skills`, and `/opencode/skill` were absent or empty after reset.
  - `sync-check-record.jsonl`, `mobius-loop-trace.jsonl`, `explain-code-status-ledger.jsonl`, `integrity-sync-ledger.jsonl`, `performance-audit-ledger.jsonl`, `AGENTS.md`, `CLAUDE.md`, `.opencode/AGENTS.md`, `.opencode/instructions.md`, and `.opencode/instructions` were absent after reset.
  - `opencode debug skill` returned `[]` after reset.
  - A second reset produced the same clean state.
- Test note:
  - `uv run --no-sync pytest experiments/AgentCallInterface/tests/test_reset_opencode_zero_skill_state_script.py` passed.
  - Plain `uv run pytest ...` is currently blocked by the repo dependency resolution issue for `pyarrow==24.0.0` on Linux before test collection.

## Preliminary Experiment 2 Result

- Status: passed.
- Script: `experiments/AgentCallInterface/coding_evaluation/opencode_skill_lifecycle_probe.py`.
- Tests:
  - `experiments/AgentCallInterface/tests/test_opencode_skill_lifecycle_probe.py`.
  - `experiments/AgentCallInterface/tests/test_opencode_skill_session.py`.
- Detailed record: `tasks/session_record_20260502_preliminary_experiment_2_opencode_skill_lifecycle.md`.
- Canonical run directory: `experiments/results/preliminary_opencode_skill_lifecycle/opencode_skill_lifecycle_20260502_191801_932886`.
- Model: `minimax/minimax-m2.5:free`.
- Classification: `created_skills_require_new_opencode_session`.
- Verification:
  - Initial zero-skill reset passed.
  - Both `integrity-sync` and `performance-audit` skill artifacts were created under `/opencode/.opencode/skills`.
  - `opencode debug skill` listed both skills after creation.
  - Same-session `/performance-audit` attempt was unavailable: OpenCode reported no skills currently available.
  - Restarted-session `/performance-audit` produced native OpenCode skill-call evidence and completed successfully.
  - Clean follow-up also loaded `/performance-audit` through native OpenCode skill-call evidence and appended trace rows.
  - Final cleanup reset returned `/opencode` to zero-skill state.
- Main experiment implication:
  - T-ASR must not assume same-session OpenCode skill invocation.
  - Report artifact creation, post-creation debug visibility, restarted-session skill use, and clean follow-up behavior separately.
