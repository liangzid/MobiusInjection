## Task

Estimate disk-space usage for the ResearchPlan A ADD_S batch experiment.

## Files / Artifacts Consulted

- `/home/zi/AgentCodingDos/experiments/scripts/effectivenss_injection_claw_0.2.context_injection_add_s.sh`
- `/home/zi/AgentCodingDos/experiments/configs/context_injection_add_s_taskset_plan_a.toml`
- Existing Docker checkpoint image sizes observed from prior ADD_S runs
- Partial run artifacts under `/home/zi/agentcodingdos_context_injection_runs/`

## What I checked

1. Confirmed the `0.2` runner defaults to:
   - agents: `openclaw zeroclaw hermes`
   - variants: `poisoned`
2. Confirmed the main loop is serial, not parallel.
3. Counted the Plan A taskset:
   - `4` categories
   - `11` tasks each
   - `44` tasks total
   - `132` total runs (`44 tasks * 3 agents * 1 variant`)
4. Confirmed `pre_run` checkpoints are now disabled, but `post_run` checkpoints are still written.
5. Checked partial artifact sizes:
   - staging for partial Plan A run was only `5.7M`
   - partial logs / exports / verifier directories were tiny compared with Docker image usage

## Estimate

Primary persistent disk usage for a full Plan A run comes from `post_run` checkpoint images.

Representative post-run image sizes from observed ADD_S runs:

- OpenClaw post-run: about `0.94 GB`
- ZeroClaw post-run: about `0.26 GB`
- Hermes post-run: about `3.0 GB`

Projected full-run checkpoint storage:

- OpenClaw: `44 * 0.94 GB ~= 41 GB`
- ZeroClaw: `44 * 0.26 GB ~= 11.5 GB`
- Hermes: `44 * 3.0 GB ~= 132 GB`

Projected total for `post_run` images alone:

- about `184.5 GB`

Non-image artifacts are much smaller:

- staging: likely well under `1 GB`
- logs + exported workspaces + verifier results + manifests: likely on the order of a few GB, not tens of GB

## Conclusion

Reasonable planning estimate for one full Plan A run with the current `0.2` script and no `pre_run` checkpoints:

- lower-bound practical estimate: about `185 GB`
- safer working estimate: about `190-200 GB`

The dominant cost is Hermes `post_run` images.
