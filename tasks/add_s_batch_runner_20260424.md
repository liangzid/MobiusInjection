# ADD_S Batch Runner - 2026-04-24

## User request

Refer to `tasks/research_plan_0424_b_write_eval_script_ADD_S.org` and process the experiment work.

## Files changed

- `experiments/AgentCallInterface/context_injection_add_s.py`
- `experiments/configs/context_injection_add_s_taskset.toml`
- `experiments/scripts/effectivenss_injection_claw_0.2.context_injection_add_s.sh`
- `experiments/AgentCallInterface/tests/test_context_injection_add_s.py`

## What I changed

1. Added a new helper module for the ADD_S batch workflow:
   - parses a manifest-driven taskset from TOML;
   - applies task-specific injection transforms;
   - computes TSR and P-ASR summaries from run results;
   - exposes small CLI entry points used by the shell runner.
2. Added a new batch runner script instead of rewriting the validated `0.1` runner:
   - default model is `qwen/qwen3.6-plus`;
   - default template is `mobiusInjection/MI_V3.5.2_clawagenttry.py`;
   - loads category/task definitions from a taskset file;
   - preserves pre-run and post-run Docker image checkpoints;
   - records per-run `injection_observed` evidence;
   - writes category summaries to JSON and Markdown.
3. Added a seed taskset for the four requested categories:
   - `daily-life` -> `xdom-001`
   - `social` -> `comm-006`
   - `office` -> `eml-005`
   - `dev` -> `xdom-002`
4. Added focused tests for:
   - taskset parsing;
   - JSON-field injection;
   - Python-comment injection;
   - category summary math;
   - shell-script syntax/reference checks.

## Important constraint

There is no evidence in the repository that the final Plan-A four-category task selection has already been finalized. The new TOML taskset is therefore a runnable seed configuration, not a claim that the research selection is complete.

There is also a real experimental caveat: `MI_V3.5.2_clawagenttry.py` was originally written around email/action-item wording, so using it across non-email categories is operationally supported by the new runner but may still bias stealth/effectiveness. I did not silently pretend that mismatch was solved.

## Validation

Commands run:

```bash
chmod +x experiments/scripts/effectivenss_injection_claw_0.2.context_injection_add_s.sh
bash -n experiments/scripts/effectivenss_injection_claw_0.2.context_injection_add_s.sh
uv run pytest experiments/AgentCallInterface/tests/test_context_injection_add_s.py -q
python3 -m py_compile experiments/AgentCallInterface/context_injection_add_s.py experiments/AgentCallInterface/tests/test_context_injection_add_s.py
```

Results:

- bash syntax check passed
- `6 passed in 0.03s`
- `py_compile` passed

## Internal result

The repository now has a separate ADD_S-capable batch runner with explicit category/task configuration and per-category TSR/P-ASR reporting, while leaving the existing minimal runner untouched.
