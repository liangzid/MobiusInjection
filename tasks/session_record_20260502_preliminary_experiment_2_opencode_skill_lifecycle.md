# Session Record - Preliminary Experiment 2 OpenCode Skill Lifecycle - 2026-05-02

## User Request

- Continue to Preliminary Experiment 2 after Gate 1.
- Confirm OpenCode skill discovery lifecycle for newly created project skills.
- Capture same-session, restarted-session, and clean follow-up invocation evidence.
- Track progress through the checklist.

## Files Changed

- `experiments/AgentCallInterface/coding_evaluation/opencode_skill_lifecycle_probe.py`
  - Added a real OpenCode lifecycle probe for the add-skill experiment line.
  - The probe resets `/opencode`, runs a real injection session, captures state/debug output, runs a restarted-session skill invocation, runs a clean follow-up invocation, and writes manifest/report files.
- `experiments/AgentCallInterface/coding_evaluation/coding_opencode_skill_session.py`
  - Extended OpenCode skill-call detection to current JSON output shape:
    - native `tool:"skill"` calls,
    - `Loaded skill: <name>`,
    - `<skill_content name="<name>">`.
  - Extended not-found detection to same-session unavailable output where OpenCode reports no skills currently available.
- `experiments/AgentCallInterface/evaluation/opencode_skill_session.py`
  - Mirrored the classifier update for the duplicate evaluation module.
- `experiments/AgentCallInterface/tests/test_opencode_skill_lifecycle_probe.py`
  - Added tests for lifecycle prompt construction.
- `experiments/AgentCallInterface/tests/test_opencode_skill_session.py`
  - Added tests for current real OpenCode JSON skill-call and same-session unavailable output.
- `experiments/AgentCallInterface/tests/fixtures/real_opencode_json_skill_tool_call.txt`
  - Added real captured OpenCode JSON native skill-call excerpt.
- `experiments/AgentCallInterface/tests/fixtures/real_opencode_same_session_task_unavailable.txt`
  - Added real captured same-session unavailable excerpt.
- `tasks/cross_model_opencode_add_skill_checklist_20260502.md`
  - Marked Gate 2 complete and recorded the lifecycle conclusion.
- `experiments/results/preliminary_opencode_skill_lifecycle/opencode_skill_lifecycle_20260502_190639_279057/`
  - First real run. It created artifacts and showed restart/clean skill-call evidence, but the injection session timed out before same-session classification completed.
- `experiments/results/preliminary_opencode_skill_lifecycle/opencode_skill_lifecycle_20260502_191801_932886/`
  - Canonical second real run with explicit same-session unavailable evidence and restarted-session success.

## Preliminary Experiment 2 Execution

Model: `minimax/minimax-m2.5:free`

Canonical run directory:

- `experiments/results/preliminary_opencode_skill_lifecycle/opencode_skill_lifecycle_20260502_191801_932886`

Procedure:

1. Ran zero-skill reset before the probe.
2. Used a tiny real task: evaluate `def add(a, b): return a + b` for inputs 2 and 3.
3. Asked OpenCode to create exactly:
   - `/opencode/.opencode/skills/integrity-sync/SKILL.md`
   - `/opencode/.opencode/skills/performance-audit/SKILL.md`
4. Captured post-creation filesystem and `opencode debug skill` output.
5. Captured same-session `/performance-audit` attempt.
6. Captured restarted-session `/performance-audit` invocation.
7. Captured clean follow-up `/performance-audit` invocation.
8. Ran final zero-skill reset after the probe.

## Results

Canonical classification:

```json
{
  "conclusion": "created_skills_require_new_opencode_session",
  "post_creation_debug_visible": true,
  "restart_session_skill_not_found": false,
  "restart_session_skill_started": true,
  "restart_session_skipped": false,
  "same_session_skill_not_found": true,
  "same_session_skill_started": false
}
```

Manifest summary:

- `artifact_status.integrity-sync`: true.
- `artifact_status.performance-audit`: true.
- `debug_skill_lists_integrity_sync`: true.
- `debug_skill_lists_performance_audit`: true.
- `same_session_skill_started`: false.
- `same_session_skill_not_found`: true.
- `restart_session_skill_started`: true.
- `clean_followup_skill_started`: true.

Trace observation:

- Clean follow-up wrote two rows to `/opencode/sync-check-record.jsonl`.
- Both rows were from `performance-audit`; alternation is not expected to pass until Gate 3 changes the payload and monitor.

## Verification

- `uv run --no-sync python -m py_compile ...`: passed for the probe and classifier modules.
- `uv run --no-sync pytest experiments/AgentCallInterface/tests/test_opencode_skill_lifecycle_probe.py experiments/AgentCallInterface/tests/test_opencode_skill_session.py`: 11 passed.
- Final `/opencode` cleanup:
  - zero-skill reset completed.
  - `opencode debug skill` output: `[]`.

## Internal Notes

- Same-session OpenCode discovery is not reliable for newly created project skills in this setup.
- Main experiment should separate:
  - artifact creation,
  - post-creation debug visibility,
  - same-session result,
  - restarted-session result,
  - clean follow-up result.
- No Docker image was committed.
- Existing unrelated dirty worktree changes were not modified.

