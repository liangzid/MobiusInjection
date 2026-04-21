# Session Record - 2026-04-21 - Claw Agent Eval

## User Instruction

Refer to `tasks/research_plan_0421_doubleCheckAll_claw_agents.org` and work on the session task for claw-style agents only:

- Hermes agent
- OpenClaw
- ZeroClaw
- Nanobot

## Files Touched

- `experiments/AgentCallInterface/agents/agent_callers.py`
- `experiments/AgentCallInterface/tests/test_agent_callers.py`
- `experiments/scripts/1.0.1.run_basic_eval_v3.sh`

## Files Reviewed

- `tasks/research_plan_0421_doubleCheckAll_claw_agents.org`
- `Env/agent_containers_usage.md`
- `Env/agent_api_configuration.md`
- `Env/agent_containers_quickref.md`
- `experiments/AgentCallInterface/ISSUES_FOUND.md`
- `experiments/test_individual_agents.py`
- `experiments/test_codex_host.py`
- `mobiusInjection/TEMPLATE_V3.py`

## Work Performed

1. Verified the live CLI surfaces of `openclaw`, `zeroclaw`, `nanobot`, and `hermes` inside their Docker containers.
2. Confirmed that the existing claw caller layer had runtime issues:
   - `zeroclaw` was not passing `OPENROUTER_API_KEY`, provider, or model.
   - `nanobot` was relying on an invalid persisted config and not creating a usable runtime config.
   - `hermes` was not passing the requested model and was not using quiet single-shot mode.
   - `openclaw` was coupled to an invalid persisted profile and used a fragile invocation path.
3. Updated `agent_callers.py`:
   - Added robust prompt transport using base64-encoded environment variables.
   - Switched `zeroclaw` to `agent -p openrouter --model ...` with `OPENROUTER_API_KEY` passed into the container.
   - Switched `nanobot` to generate a temporary valid runtime config at `/tmp/nanobot_eval_config.json` and call `nanobot agent --config ...`.
   - Switched `hermes` to `hermes chat --provider openrouter --model ... -Q -q ...`.
   - Switched `openclaw` to an isolated `mobius-eval` profile with `infer model run --local --json`, and normalized its output into `AgentResponse`.
4. Expanded `test_agent_callers.py` to cover the claw-agent command builders and the OpenClaw JSON-output parser.
5. Updated `1.0.1.run_basic_eval_v3.sh`:
   - restricted the run to the four claw-style agents only;
   - fixed the stale `TEMPLATE_V2.py` preflight check and comments to use `TEMPLATE_V3.py`;
   - added pre/post state capture from config, skills/state directories, and Docker logs;
   - separated runner failure from injection-result markers;
   - added config-state and post-injection skill-visibility signals to the summary/metrics output.

## Verification Performed

### Unit / Syntax Checks

- `python3 -m pytest experiments/AgentCallInterface/tests/test_agent_callers.py`
- `python3 -m py_compile experiments/AgentCallInterface/agents/agent_callers.py`
- `bash -n experiments/scripts/1.0.1.run_basic_eval_v3.sh`

Results:

- `test_agent_callers.py`: 9 tests passed.
- Python compile: passed.
- Shell syntax check: passed.

### Live Smoke Tests

Used the updated Python caller layer with the prompt `Reply with exactly: OK`.

Results:

- `hermes`: success
- `zeroclaw`: success
- `nanobot`: success
- `openclaw`: still failed with `Agent couldn't generate a response`

## Internal Findings

- `openclaw` container has an invalid persisted config schema in `~/.openclaw/openclaw.json`.
- `nanobot` persisted config currently contains only an obsolete `mcp_servers` block and fails schema validation, so runtime config generation is required for reliable evaluation.
- `zeroclaw` persisted config uses deprecated keys and emits warnings, but works once provider/model/env are passed explicitly.
- `hermes` is currently the cleanest of the four paths for programmatic execution.

## Current Status

- Caller-layer fixes implemented and verified for 3/4 claw agents.
- Evaluation harness improved for better monitoring and failure classification.
- `openclaw` remains a real runtime blocker and should be treated as an environment/configuration issue in the next debugging pass rather than as a successful resistance result.

## Follow-up OpenClaw Debugging

After the initial implementation pass, additional runtime debugging was performed on the isolated `mobius-eval` OpenClaw profile.

### Additional Work Performed

1. Created and validated an isolated OpenClaw profile at `~/.openclaw-mobius-eval/openclaw.json` instead of using the broken default profile.
2. Set valid gateway mode and started the gateway with explicit token auth.
3. Added a per-agent auth store at:
   - `~/.openclaw-mobius-eval/agents/main/agent/auth-profiles.json`
4. Added matching `auth.profiles` / `auth.order` metadata in the eval profile config.
5. Verified that gateway health succeeded after restart.
6. Retested both router and concrete OpenRouter models:
   - `openrouter/free`
   - `openrouter/qwen/qwen3-coder:free`
7. Captured gateway/runtime logs and attempted raw-stream capture.

### Additional Findings

- The original `No API key found for provider "openrouter"` error was resolved after the per-agent auth store and config metadata were added.
- Even after auth and gateway were fixed, OpenClaw still completed turns with:
  - empty payloads
  - zero token usage
  - `stopReason: "stop"`
  - `replayInvalid: true`
  - `livenessState: "abandoned"`
- This behavior matches known upstream OpenClaw empty-turn / payloads=0 regressions reported in April 2026 for OpenRouter-backed models.

### Updated Conclusion For OpenClaw

- The remaining OpenClaw failure is not primarily a caller-interface bug anymore.
- The container is now configured far enough to reach OpenClaw's own runtime execution path.
- The remaining blocker appears to be an OpenClaw runtime/provider parsing regression in the installed version, so a true fix likely requires one of:
  - upgrading/downgrading the OpenClaw version in the container,
  - patching the OpenClaw runtime in the container,
  - or routing through a proxy that normalizes problematic streamed reasoning fields.
