# Kilo Code Eval Diagnostics - 2026-04-21

## User Request

Dr. Frost asked to inspect `experiments/logs/basic_eval_20260421_103115.log`, summarize what code changes would be needed to fix the Kilo Code run issues, and run tests if needed before proposing changes for review.

## Files and Areas Inspected

- `experiments/logs/basic_eval_20260421_103115.log`
- `experiments/logs/basic_eval_20260421_103115_summary.txt`
- `experiments/logs/basic_eval_20260421_103115_kilo_code_output.txt`
- `experiments/logs/basic_eval_20260421_103115_kilo_code_followup.txt`
- `experiments/logs/basic_eval_20260421_103115_kilo_code_metrics.json`
- `experiments/logs/basic_eval_20260421_103115_kilo_code_injection.txt`
- `experiments/logs/individual_test_kilo_code_20260420_132946.txt`
- `experiments/logs/injection_test_kilo_code_20260420_160150.txt`
- `experiments/AgentCallInterface/agents/agent_callers.py`
- `experiments/scripts/1.0.0.run_basic_eval.sh`
- `experiments/scripts/1.0.1.run_basic_eval_v3.sh`
- `Env/setup/05_kilo_code.sh`
- `Env/agent_containers_quickref.md`
- `Env/openrouter_free_models_setup_guide.md`

## Diagnostic Actions

- Read the target log and related Kilo output, follow-up, metrics, and injection files.
- Inspected the Kilo caller implementation and the basic eval summary-writing code.
- Checked the running `kilo_code` container and Kilo CLI version/help.
- Checked Kilo container config keys without printing secrets.
- Ran real short Kilo CLI calls:
  - `kilo run -m kilo/openrouter/free --auto 'Reply exactly: OK'`
  - `kilo run -m kilo/nvidia/nemotron-3-super-120b-a12b:free --auto 'Reply exactly: OK'`
- Ran the current `KiloCodeCaller` against short prompts for both `openrouter/free` and `nvidia/nemotron-3-super-120b-a12b:free`.
- Re-ran the exact logged injection prompt through `KiloCodeCaller` with a 120-second timeout.
- Checked `/proc` inside the container after timeout and found Kilo/Node child processes remained alive after the host-side timeout.
- Cleaned up only the two diagnostic Kilo/Node PIDs created by this session.
- Ran targeted unit tests for existing agent caller coverage.

## Results

- The target log shows Kilo injection timed out after 300 seconds with no stdout/stderr, but `basic_eval_20260421_103115_summary.txt` still marks Kilo as `✅ Success`.
- `experiments/scripts/1.0.0.run_basic_eval.sh` writes `✅ Success` unconditionally in the summary row, so timed-out Kilo runs are misreported.
- Historical Kilo logs from 2026-04-20 also show 180-second timeouts for the same `nvidia/nemotron-3-super-120b-a12b:free` injection path, so this is reproducible rather than a one-off.
- Short real Kilo calls succeeded:
  - `kilo/openrouter/free` returned `OK` in about 5 seconds.
  - `kilo/nvidia/nemotron-3-super-120b-a12b:free` returned `OK` in about 4 seconds via direct CLI.
  - `KiloCodeCaller` short prompts returned `OK` for both tested model inputs.
- The exact injection prompt reproduced the no-output timeout at 120 seconds.
- After `subprocess.run(..., timeout=...)`, Kilo/Node processes were still alive inside the container. This means current timeout handling can leave orphaned agent processes that contaminate later resource metrics, checkpoint images, and persistence tests.
- The container Kilo config has `claudeApiKey` set to the literal string `${ANTHROPIC_API_KEY}` and no Anthropic/OpenAI env key present. `OPENROUTER_API_KEY` is present. This should be cleaned up for correctness, even though OpenRouter short calls work.
- Targeted tests passed: `14 passed in 1.04s` for `test_agent_callers.py` and `test_opencode_caller.py`.

## Proposed Code Changes for Review

1. Add a dedicated Kilo command builder and runner in `KiloCodeCaller`, similar to `OpenCodeCaller`, instead of calling generic `_run_command` directly.
2. On timeout, actively terminate leftover Kilo/Node processes inside the `kilo_code` container that match the current run/session marker, then return `success=False` with captured partial output and stderr.
3. Pass the prompt via base64-decoded environment variable through `bash -lc`, not as a raw Docker exec argument, to avoid huge prompt arguments leaking into `/proc/*/cmdline` and to make process matching safer.
4. Add Kilo model normalization tests:
   - `openrouter/free` should become `kilo/openrouter/free`.
   - Already-prefixed `kilo/openrouter/free` should not become `kilo/kilo/openrouter/free`.
   - `nvidia/nemotron-3-super-120b-a12b:free` should become `kilo/nvidia/nemotron-3-super-120b-a12b:free`.
5. Add Kilo timeout tests using a local Python subprocess fixture to prove partial output is preserved and timeout cleanup is invoked.
6. Fix `experiments/scripts/1.0.0.run_basic_eval.sh` so summary `Injection Success` comes from `response.success` or the saved API metrics, not a hard-coded success row.
7. Consider moving Kilo into the newer `1.0.1.run_basic_eval_v3.sh` structured evidence path, or create a coding-agent v3 path with the same run-status logic, state capture, stderr/error capture, and notes.
8. Fix `Env/setup/05_kilo_code.sh` to write OpenRouter config using actual environment expansion and the documented `openrouterApiKey` / `openrouterModel` keys, while avoiding secret leakage in logs.

## Current State

No production code was modified in this diagnostic pass. Only this record file was added.
