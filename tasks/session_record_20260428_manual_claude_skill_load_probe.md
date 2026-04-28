# Manual Claude Code Skill Load Probe - 2026-04-28

## User Request

Dr. Frost asked whether the skills exist after changing location, whether a
manual location change proves Claude Code loads them, why the prompt writes to
workspace rather than HOME, and whether the prompt contains misleading path
instructions.

## Commands And Files Checked

- Checked current prompt path logic in:
  - `mobiusInjection/CODING_AGENT_TEMPLATE_V6_LOOP.py`
  - `mobiusInjection/CODING_AGENT_TEMPLATE_V5_LOOP.py`
  - `mobiusInjection/CODING_AGENT_TEMPLATE_V3.py`
  - `experiments/AgentCallInterface/agents/agent_callers.py`
- Checked Docker runtime paths under `/tmp/claude-code-runs`.
- Manually precreated two probe skills before launching Claude Code:
  - `/tmp/claude-code-runs/manual_skill_load_20260428/home/.claude/skills/home-probe/SKILL.md`
  - `/tmp/claude-code-runs/manual_skill_load_20260428/workspace/.claude/skills/project-probe/SKILL.md`

## Manual Probe Result

Ran a short Claude Code stream-json call with run id
`manual_skill_load_20260428`, reusing the same runtime HOME and workspace where
the probe skills had been precreated.

Claude stream init reported:

```text
SYSTEM_SKILLS ['update-config', 'debug', 'simplify', 'batch', 'loop',
'claude-api', 'home-probe', 'project-probe']
```

The assistant also reported available skills including `home-probe` and
`project-probe`.

## Conclusion

- Claude Code native skill loading works in this harness when skills exist before
  process startup in:
  - runtime user HOME: `$HOME/.claude/skills`
  - runtime project workspace: `$CLAUDE_WORKSPACE/.claude/skills`
- The existing V6 prompt has not been changed yet. It still tells Claude Code to
  use `skills`, so official benchmark runs still create ordinary workspace files
  rather than native Claude Code skills.
- The reason files were written under workspace is direct:
  - `ClaudeCodeCaller` runs `cd "$CLAUDE_WORKSPACE"` before invoking `claude`.
  - V6 returns relative skill root `skills` for `claude_code`.
  - Therefore `skills/...` resolves to `$CLAUDE_WORKSPACE/skills/...`.
- The prompt path instruction is therefore unsuitable for native Claude skill
  loading. It was inherited from V3, which intentionally avoided `.claude`
  because hidden config writes were considered permission-sensitive.

## Implication For Next Prompt Iteration

- V7 should stop using `skills` for Claude Code if native skill loading is the
  acceptance criterion.
- For follow-up persistence, project-level
  `$CLAUDE_WORKSPACE/.claude/skills/<skill>/SKILL.md` is the best target because
  the same-workspace follow-up call starts a new Claude process and should load
  those skills at init.
- For same-call native invocation, prompt-created skills may still be too late if
  Claude only discovers skills at startup. That case likely needs a prelaunch
  runner-side skill install or a two-stage bootstrap.
