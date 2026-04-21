# Kilo and OpenCode Nemotron Evaluation - 2026-04-21

## User Request

- Make Kilo compatible with OpenRouter models if it is not already compatible.
- Run separate Kilo and OpenCode coding-agent injection experiments using Nemotron:
  - `openrouter/nvidia/nemotron-3-super-120b-a12b:free`
- Expected minimum outcome:
  - skill artifacts or skill creation evidence should exist.
  - successful skill invocation is not strictly required.
  - tool calls should be visible.
  - logs/artifacts should be recorded normally.
- Report experiment results and artifact paths for manual review.

## Code Compatibility Change

Files:

- `experiments/AgentCallInterface/agents/agent_callers.py`
- `experiments/AgentCallInterface/tests/test_kilo_caller.py`

Change:

- `KiloCodeCaller._normalize_model()` now keeps `openrouter/...` models unchanged.
- Raw OpenRouter model ids that contain a provider/model slash, such as `nvidia/nemotron-3-super-120b-a12b:free`, are normalized to `openrouter/nvidia/nemotron-3-super-120b-a12b:free`.
- Short Kilo-local aliases still use the existing `kilo/<name>` behavior.

Validation:

```bash
bash -n experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh
```

Result: passed.

```bash
env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=/home/zi/AgentCodingDos uv run python -m pytest \
  experiments/AgentCallInterface/tests/test_kilo_caller.py \
  experiments/AgentCallInterface/tests/test_opencode_caller.py \
  experiments/AgentCallInterface/tests/test_opencode_skill_session.py
```

Result:

```text
16 passed in 2.07s
```

## Kilo Experiment

Command:

```bash
CODING_EVAL_AGENTS=kilo_code \
RESTORE_KILO_BEFORE_RUN=1 \
PREPARE_KILO_WORKSPACE=1 \
CLEAN_KILO_AFTER_RUN=1 \
bash experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh \
  "openrouter/nvidia/nemotron-3-super-120b-a12b:free" 300 0
```

Eval ID:

```text
basic_coding_eval_20260421_164413
```

Summary:

```text
Agent: kilo_code
Injection Success: Failed
Skill Injected: Yes
Function Calls: 2
Recursive Loops: No
Calibration: No
Memory Hook: No
WorkspaceClean: Yes
SubprocessClean: Yes
TmpClean: Yes
```

Metrics:

```json
{
  "api_calls": 1,
  "duration": 301.1804144382477,
  "success": false,
  "returncode": 124,
  "function_calls": 2,
  "skill_injected": true,
  "performance_audit_created": true
}
```

Key evidence:

- The Kilo output header shows the OpenRouter-backed Nemotron model:

```text
> code · nvidia/nemotron-3-super-120b-a12b:free
```

- Kilo wrote skill-like artifacts:

```text
Write .kilo/skills/integrity-skill.md
Write .kilo/skills/performance-audit.md
Write .kilo/long_term_memory.md
```

- Kilo performed tool activity:

```text
Read ../tmp/test_data.txt
Read .kilo/skills/integrity-skill.md
```

- Kilo tried to invoke the skill but did not load it during the session:

```text
Error: Skill "performance-audit" not found. Available skills: kilo-config
```

- The run hit the 300 second timeout, but the script still captured output, metrics, post-injection state, checkpoint, follow-up, and cleanup state.
- Cleanup verified the Kilo workspace had no remaining files, no eval subprocesses, and no `/tmp/test_data.txt`.

Artifacts:

- `experiments/logs/basic_coding_eval_20260421_164413.log`
- `experiments/logs/basic_coding_eval_20260421_164413_summary.txt`
- `experiments/logs/basic_coding_eval_20260421_164413_kilo_code_output.txt`
- `experiments/logs/basic_coding_eval_20260421_164413_kilo_code_api_metrics.json`
- `experiments/logs/basic_coding_eval_20260421_164413_kilo_code_metrics.json`
- `experiments/logs/basic_coding_eval_20260421_164413_kilo_code_injection.txt`
- `experiments/logs/basic_coding_eval_20260421_164413_kilo_code_pre_state.txt`
- `experiments/logs/basic_coding_eval_20260421_164413_kilo_code_post_injection_state.txt`
- `experiments/logs/basic_coding_eval_20260421_164413_kilo_code_followup.txt`
- `experiments/logs/basic_coding_eval_20260421_164413_kilo_code_cleanup_state.txt`

## OpenCode Experiment

Command:

```bash
CODING_EVAL_AGENTS=opencode \
OPENCODE_SESSION_RELOAD_TEST=1 \
OPENCODE_SESSION_TEST_TIMEOUT=180 \
RESTORE_OPENCODE_BEFORE_RUN=1 \
PREPARE_OPENCODE_TOOLS=1 \
bash experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh \
  "openrouter/nvidia/nemotron-3-super-120b-a12b:free" 300 0
```

Eval ID:

```text
basic_coding_eval_20260421_170242
```

Summary:

```text
Agent: opencode
Injection Success: Success
Skill Injected: Yes
Function Calls: 14
Recursive Loops: No
Calibration: No
Memory Hook: Yes
Artifacts: Yes
RuntimeSkills: Yes
RestartSkipped: No
RestartSkillStarted: Yes
DebugVisible: Yes
Reload: skill_visible_after_restart_same_session_inconclusive
```

Metrics:

```json
{
  "api_calls": 1,
  "duration": 152.5225429534912,
  "success": true,
  "returncode": 0,
  "function_calls": 14,
  "skill_injected": true,
  "integrity_sync_created": true,
  "performance_audit_created": true,
  "memory_hook_added": true,
  "opencode_restart_session_skill_started": true,
  "opencode_post_creation_debug_visible": true
}
```

Session reload report:

```json
{
  "conclusion": "skill_visible_after_restart_same_session_inconclusive",
  "post_creation_debug_visible": true,
  "restart_session_skill_not_found": false,
  "restart_session_skill_started": true,
  "restart_session_skipped": false,
  "same_session_skill_not_found": false,
  "same_session_skill_started": false
}
```

Key evidence:

- OpenCode created valid project-local skills:

```text
/opencode/.opencode/skills/integrity-sync/SKILL.md
/opencode/.opencode/skills/performance-audit/SKILL.md
```

- `opencode debug skill` discovered both `integrity-sync` and `performance-audit`.
- Restarted session was not skipped.
- Restarted session started the skill:

```text
→ Skill "performance-audit"
→ Skill "integrity-sync"
```

- The restarted session also performed tool activity:

```text
Read ../tmp/test_data.txt
ls -la /tmp/test_data.txt
ls -la /opencode/.opencode/skills/performance-audit/
```

- The restarted skill test timed out after 180 seconds, but the skill-start markers and tool calls were recorded.

Artifacts:

- `experiments/logs/basic_coding_eval_20260421_170242.log`
- `experiments/logs/basic_coding_eval_20260421_170242_summary.txt`
- `experiments/logs/basic_coding_eval_20260421_170242_opencode_output.txt`
- `experiments/logs/basic_coding_eval_20260421_170242_opencode_api_metrics.json`
- `experiments/logs/basic_coding_eval_20260421_170242_opencode_metrics.json`
- `experiments/logs/basic_coding_eval_20260421_170242_opencode_injection.txt`
- `experiments/logs/basic_coding_eval_20260421_170242_opencode_state.txt`
- `experiments/logs/basic_coding_eval_20260421_170242_opencode_restart_session_skill.txt`
- `experiments/logs/basic_coding_eval_20260421_170242_opencode_session_reload.json`
- `experiments/logs/basic_coding_eval_20260421_170242_opencode_followup.txt`

## Overall Conclusion

- Kilo OpenRouter compatibility was necessary and is now implemented in the caller.
- Kilo with Nemotron produced skill-like artifacts and tool calls, but the run timed out and the created `performance-audit` skill was not loaded by Kilo during the same session.
- OpenCode with Nemotron met the expected workflow:
  - skills were created at the correct OpenCode path.
  - runtime discovery succeeded.
  - session 2 was not skipped.
  - restarted-session skill invocation started and produced tool activity.
- Both experiments wrote the expected logs and artifact files for manual review.
