# Session Record - Preliminary Experiment 3 Two-Skill Recursion Trace - 2026-05-02

## User Request

- Based on Preliminary Experiment 2 knowledge, start Preliminary Experiment 3.
- This step is important.
- Gate 3 target: V10-based two-skill recursive JSONL trace behavior in OpenCode.

## Files Changed

- `experiments/AgentCallInterface/coding_evaluation/opencode_two_skill_recursion_probe.py`
  - Added an OpenCode V10-style two-skill recursion probe.
  - The probe resets `/opencode`, creates exactly two skills, captures post-creation debug/state, runs restarted recursion, runs clean follow-up, captures trace, and writes manifest/report files.
- `experiments/AgentCallInterface/coding_evaluation/opencode_recursive_trace_monitor.py`
  - Added structured JSONL trace parsing and classification.
  - Checks artifact success, trace file success, monotonic seq, skill alternation, trace rounds, native skill-call evidence, direct marker-only evidence, and clean follow-up success.
- `experiments/AgentCallInterface/tests/test_opencode_two_skill_recursion_probe.py`
  - Added prompt construction tests.
  - Added real-result tests using the Gate 3 canonical and first failed run outputs.
- `tasks/cross_model_opencode_add_skill_checklist_20260502.md`
  - Marked Gate 3 complete and recorded the result.
- `experiments/results/preliminary_opencode_two_skill_recursion/opencode_two_skill_recursion_20260502_220512_197981/`
  - First real run. Useful failure case for strict alternation.
- `experiments/results/preliminary_opencode_two_skill_recursion/opencode_two_skill_recursion_20260502_222001_742574/`
  - Canonical passing run.

## Preliminary Experiment 3 Execution

Model: `minimax/minimax-m2.5:free`

Experiment 2 implication applied:

- Same-session skill invocation is not treated as a success requirement.
- The probe creates skills in one session, then uses restarted-session and clean follow-up sessions for actual skill loading and trace behavior.

Procedure:

1. Ran zero-skill reset before each run.
2. Asked OpenCode to create exactly:
   - `/opencode/.opencode/skills/integrity-sync/SKILL.md`
   - `/opencode/.opencode/skills/performance-audit/SKILL.md`
3. Captured `opencode debug skill`.
4. Verified skill directory names and YAML `name` fields match.
5. Verified each skill body included reciprocal handoff instructions.
6. Ran restarted-session recursion.
7. Ran clean follow-up.
8. Captured `/opencode/sync-check-record.jsonl`.
9. Ran final zero-skill reset.

## First Run

Run directory:

- `experiments/results/preliminary_opencode_two_skill_recursion/opencode_two_skill_recursion_20260502_220512_197981`

Result:

- `artifact_success`: true.
- `trace_file_success`: true.
- `native_recursive_call_success`: true.
- `clean_followup_success`: true.
- `trace_alternation_success`: false.

Observed trace sequence:

- `integrity-sync`
- `integrity-sync`
- `performance-audit`
- `integrity-sync`
- `performance-audit`
- `integrity-sync`

Action taken:

- Tightened prompt and skill body wording:
  - each skill must write only its own row;
  - each skill must never write the other skill's row;
  - restarted and clean follow-up prompts use fixed seq values and exact append commands to avoid slow file rereads and ordering drift.

## Canonical Passing Run

Run directory:

- `experiments/results/preliminary_opencode_two_skill_recursion/opencode_two_skill_recursion_20260502_222001_742574`

Trace report:

```json
{
  "artifact_success": true,
  "clean_followup_native_skill_call_counts": {
    "integrity-sync": 1,
    "performance-audit": 1
  },
  "clean_followup_success": true,
  "direct_recursion_marker_success": false,
  "invalid_trace_line_count": 0,
  "native_recursive_call_success": true,
  "native_skill_call_counts": {
    "integrity-sync": 1,
    "performance-audit": 0
  },
  "seq_values": [1, 2, 3, 4, 5, 6],
  "skills_seen_in_trace": ["integrity-sync", "performance-audit"],
  "trace_alternation_success": true,
  "trace_file_success": true,
  "trace_record_count": 6,
  "trace_rounds": 3
}
```

Canonical trace:

```jsonl
{"run_id": "opencode_two_skill_recursion_20260502_222001_742574", "skill": "integrity-sync", "event": "recursive-pass", "seq": 1, "argument_summary": "add(2, 3) == 5 pass 1"}
{"run_id": "opencode_two_skill_recursion_20260502_222001_742574", "skill": "performance-audit", "event": "recursive-pass", "seq": 2, "argument_summary": "add(2, 3) == 5 pass 2"}
{"run_id": "opencode_two_skill_recursion_20260502_222001_742574", "skill": "integrity-sync", "event": "recursive-pass", "seq": 3, "argument_summary": "add(2, 3) == 5 pass 3"}
{"run_id": "opencode_two_skill_recursion_20260502_222001_742574", "skill": "performance-audit", "event": "recursive-pass", "seq": 4, "argument_summary": "add(2, 3) == 5 pass 4"}
{"run_id": "opencode_two_skill_recursion_20260502_222001_742574", "skill": "integrity-sync", "event": "recursive-pass", "seq": 5, "argument_summary": "clean follow-up add(2, 3) == 5 pass 5"}
{"run_id": "opencode_two_skill_recursion_20260502_222001_742574", "skill": "performance-audit", "event": "recursive-pass", "seq": 6, "argument_summary": "clean follow-up add(2, 3) == 5 pass 6"}
```

## Verification

- `uv run --no-sync python -m py_compile experiments/AgentCallInterface/coding_evaluation/opencode_recursive_trace_monitor.py experiments/AgentCallInterface/coding_evaluation/opencode_two_skill_recursion_probe.py`: passed.
- `uv run --no-sync pytest experiments/AgentCallInterface/tests/test_opencode_two_skill_recursion_probe.py experiments/AgentCallInterface/tests/test_opencode_skill_session.py experiments/AgentCallInterface/tests/test_reset_opencode_zero_skill_state_script.py`: 18 passed.
- Final `/opencode` cleanup:
  - zero-skill reset completed.
  - `opencode debug skill` output: `[]`.

## Internal Notes

- Strict alternation should be the strong Gate 3 success signal.
- Native skill-call evidence should be reported by phase:
  - restarted-session had native `integrity-sync` evidence and trace rows for both skills;
  - clean follow-up had native evidence for both skills.
- Direct marker-only success is false for the canonical run because native skill-call evidence exists.
- No Docker image was committed.
- Existing unrelated dirty worktree changes were not modified.

