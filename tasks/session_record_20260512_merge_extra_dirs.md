# Session Record - Merge Extra CodeAgent Directories

## User Request

Dr. Frost said the repo was ready for publication but extra code/artifacts had
not been merged from sibling directories:

- `/home/zi/AgentCodingDos_CodeAgent*`
- `/home/zi/agentcodingdos_*`

The requested action was to merge those extra directories into
`/home/zi/AgentCodingDos`.

## Source Directories Reviewed

- `/home/zi/AgentCodingDos_CodeAgent`
  - branch: `codeagent/experiments-copy`
  - size before merge: about 836M
- `/home/zi/AgentCodingDos_CodeAgent_ollama_20260502`
  - branch: `plan-a-ollama-codeagent-20260502`
  - size before merge: about 26M
- `/home/zi/agentcodingdos_context_injection_runs`
  - size before merge: about 645M
- `/home/zi/agentcodingdos_targeted_runs`
  - size before merge: about 95M

## Merge Actions

- Copied publishable source, tests, scripts, task records, experiment results,
  and real log fixtures from `/home/zi/AgentCodingDos_CodeAgent`.
- Copied non-overwriting unique files from
  `/home/zi/AgentCodingDos_CodeAgent_ollama_20260502`.
- Preserved the standalone run-output layouts at:
  - `agentcodingdos_context_injection_runs/`
  - `agentcodingdos_targeted_runs/`
- Copied real historical logs under `experiments/logs/` because imported tests
  depended on those real fixtures and project instructions prohibit mock data.
- Excluded local/private/generated state during the merge:
  - `.git`, `.venv`, `.codex`, `.claude`
  - `.pytest_cache`, `.ruff_cache`, `__pycache__`, `*.pyc`
  - `.env`, `privacy_secret*`
  - `pytest-of-zi`, lockfiles, empty shell artifacts `=50`, `=50.`, and
    `explanation-status`
- Updated `.gitignore` to ignore `.env` and `/privacy_secret*`.
- Restored `AGENTS.md` and `localserver/README.md` to the current repo versions
  after the broad copy attempted to replace them with older sibling versions.

## Follow-up Fixes

- Updated `experiments/AgentCallInterface/tests/test_benchmark_analysis.py` to
  use small copied real HumanEval OpenCode metrics/analysis fixtures under
  `experiments/AgentCallInterface/tests/fixtures/`.
- Updated `experiments/AgentCallInterface/tests/test_log_retention.py` to use
  small copied real clean Claude Code baseline fixtures under
  `experiments/AgentCallInterface/tests/fixtures/` for compact-retention
  behavior.
- Updated `mobiusInjection/CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V8_LOOP.py`
  so the V8 prompt includes the expected explicit default-workflow line.
- After Dr. Frost clarified that data already being merged was acceptable, no
  merged artifact or log directories were removed.

## Verification

Commands run with `uv`:

- `uv run pytest experiments/AgentCallInterface/tests/test_agent_callers.py experiments/AgentCallInterface/tests/test_coding_eval_script.py experiments/AgentCallInterface/tests/test_edit_skill_evaluation_monitor.py experiments/AgentCallInterface/tests/test_opencode_caller.py experiments/AgentCallInterface/tests/test_api_keys.py`
  - Result: 66 passed.
- `uv run pytest experiments/AgentCallInterface/tests/test_benchmark_analysis.py experiments/AgentCallInterface/tests/test_benchmark_manifest.py experiments/AgentCallInterface/tests/test_humaneval_log_analysis.py experiments/AgentCallInterface/tests/test_log_retention.py experiments/AgentCallInterface/tests/test_prompt_composer.py experiments/AgentCallInterface/tests/test_edit_skill_evaluation_analysis.py experiments/AgentCallInterface/tests/test_edit_skill_evaluation_scripts.py experiments/AgentCallInterface/tests/test_opencode_add_skill_preflight.py experiments/AgentCallInterface/tests/test_opencode_formal_dryrun.py experiments/AgentCallInterface/tests/test_opencode_formal_results_aggregate.py experiments/AgentCallInterface/tests/test_opencode_realistic_skill_injection_probe.py experiments/AgentCallInterface/tests/test_opencode_two_skill_recursion_probe.py`
  - Initial result: 9 failures from missing real log fixture paths.
  - After importing logs and fixing fixture paths: 68 passed.
- `uv run pytest experiments/AgentCallInterface/tests/test_coding_agent_template*.py experiments/AgentCallInterface/tests/test_coding_agent_injection_template.py`
  - Initial result: 1 V8 prompt assertion failure.
  - After adding the explicit default-workflow line: 233 passed.
- `uv run pytest experiments/AgentCallInterface/tests/test_benchmark_analysis.py experiments/AgentCallInterface/tests/test_log_retention.py`
  - Result after fixture path adjustment: 6 passed.

## Internal Result

- No git commit was created.
- Existing `privacy_secret_openrouter_API_key.txt` and `Env/setup/.env` remain
  in the local workspace but are ignored; no additional `privacy_secret*` files
  were imported.
- The merge added large local artifact directories:
  - `agentcodingdos_context_injection_runs/`: about 622M after copy
  - `agentcodingdos_targeted_runs/`: about 93M after copy
  - `experiments/results/`: about 60M after merge
