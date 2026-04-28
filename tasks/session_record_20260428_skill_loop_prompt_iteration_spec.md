# Session Record: Skill Loop Prompt Iteration Spec

Date: 2026-04-28

## User Request

Dr. Frost asked to convert the prior discussion and plan into a spec document.
The document should guide future work step by step, so that if a researcher or
agent encounters a problem mid-process, the document can verify whether the
current behavior still matches the experiment goal and which step is active.

## Files Changed

- Added `tasks/spec_20260428_skill_loop_prompt_iteration.md`
- Added `tasks/session_record_20260428_skill_loop_prompt_iteration_spec.md`

## Actions

- Wrote a spec that separates installation success, activation success, loop
  success, persistence success, and baseline-adjusted loop success.
- Added current diagnosis from the reviewed prompt and curated result metrics.
- Defined evidence hierarchy so future analysis does not confuse prompt or
  `SKILL.md` text with runtime skill execution.
- Added a stepwise plan:
  - freeze current long-prompt baseline;
  - define a short sync/check loop prompt;
  - add strict loop metrics;
  - run a small A/B pilot;
  - compare results and decide next iteration.
- Added prompt-design and analysis checklists plus a reporting template.

## Result

The spec is ready as the checkpoint document for the next experiment iteration.
No experiment code, prompt template, or metric implementation was changed in
this step.

## Verification

- Documentation-only change.
- No tests were run because no executable code changed.
