# Claude Workspace Skill Host Isolation Check - 2026-04-28

## User Request

Dr. Frost asked whether using
`$CLAUDE_WORKSPACE/.claude/skills/<skill>/SKILL.md` could affect `.claude`, and
whether that path is related to the native Claude path on the machine outside
Docker.

## Check Performed

- Inspected the `claude_code` Docker container mounts:

```text
docker inspect claude_code --format '{{json .Mounts}}'
```

Result:

```text
[]
```

## Findings

- The `claude_code` container has no bind mounts configured.
- `$CLAUDE_WORKSPACE` is created inside the container at:
  `/tmp/claude-code-runs/<run_id>/workspace`
- `$CLAUDE_WORKSPACE/.claude/skills` is therefore container-local and per-run.
- It is not the Docker host user's native Claude path.
- It is not directly linked to host paths such as:
  - `~/.claude/skills`
  - `/home/zi/.claude/skills`
  - the host repo workspace
- The only `.claude` file copied by the runner is container-local
  `/home/zi/.claude/settings.json` into the per-run runtime home if present.

## Conclusion

Using `$CLAUDE_WORKSPACE/.claude/skills` in this harness affects only the
container's per-run Claude workspace. It should not affect the Docker host's
native Claude configuration unless a future runner explicitly adds bind mounts
or copies those files out.
