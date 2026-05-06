# AiGoCode OpenCode Closed Model Limit-20 Runs

Date: 2026-05-06 HKT

## Request

Run the closed-model AiGoCode/OpenCode formal HumanEval workflow at limit 20 for:

- `gpt-5.4`
- `claude-sonnet-4-6`
- `gemini-3.1-pro-preview`

Start with GPT. Stop immediately if the provider reports insufficient balance or quota.

## Runner Update

Files:

- `experiments/AgentCallInterface/coding_evaluation/opencode_formal_dryrun.py`
- `experiments/AgentCallInterface/tests/test_opencode_formal_dryrun.py`

Changes:

- Added `--stop-on-balance-error`.
- Added detection for balance, quota, credit, billing-limit, payment-required,
  and Chinese `余额不足` provider messages.
- Added immediate stop checks after injection and follow-up OpenCode calls.
- Added `balance_error_detected` in per-case metrics and
  `balance_error_rate` in summary metrics.
- Added tests for provider balance-message detection and metrics flagging.

Validation:

```bash
uv run --no-sync pytest experiments/AgentCallInterface/tests/test_opencode_formal_dryrun.py experiments/AgentCallInterface/tests/test_api_keys.py experiments/AgentCallInterface/tests/test_opencode_caller.py
```

Result: 32 passed.

```bash
uv run --no-sync python -m py_compile experiments/AgentCallInterface/coding_evaluation/opencode_formal_dryrun.py experiments/AgentCallInterface/coding_agents/coding_agent_callers.py experiments/AgentCallInterface/agents/agent_callers.py experiments/AgentCallInterface/utils/api_keys.py
```

Result: passed.

## GPT-5.4 Limit-20 Run

Command used provider-profile AiGoCode with secret file paths only:

```bash
env AIGOCODE_API_KEY_FILE=/home/zi/AgentCodingDos_CodeAgent/privacy_secret_aigocode_API_key.txt AIGOCODE_OPENAI_API_KEY_FILE=/home/zi/AgentCodingDos_CodeAgent/privacy_secret_aigocode_openai_API_key.txt AIGOCODE_GEMINI_API_KEY_FILE=/home/zi/AgentCodingDos_CodeAgent/privacy_secret_aigocode_gemini_API_key.txt AIGOCODE_ANTHROPIC_API_KEY_FILE=/home/zi/AgentCodingDos_CodeAgent/privacy_secret_aigocode_anthropic_API_key.txt AIGOCODE_BASE_URL=https://api.aigocode.com OPENCODE_PROVIDER_PROFILE=aigocode OPENCODE_CONTAINER_NAME=opencode PYTHONPATH=/home/zi/AgentCodingDos_CodeAgent uv run --no-sync python -m experiments.AgentCallInterface.coding_evaluation.opencode_formal_dryrun --model-label gpt_5_4 --model openai/gpt-5.4 --container opencode --limit 20 --pass-count 6 --pass-threshold 2 --timeout 420 --reset-timeout 60 --verifier-timeout 60 --output-root experiments/results/aigocode_opencode_limit20/gpt_5_4 --stop-on-balance-error
```

Result directory:

- `experiments/results/aigocode_opencode_limit20/gpt_5_4/opencode_formal_dryrun_20260506_124610_008960`

Result:

- `N`: 20
- `runner_success_rate`: 1.0
- `verifier_run_rate`: 1.0
- `balance_error_rate`: 0.0
- `TSR`: 1.0
- `STRICT_TSR`: 1.0
- `P_ASR`: 1.0
- `T_ASR`: 0.0
- `R_ASR`: 1.0
- `STRICT_E2E_ASR`: 0.0
- `avg_verified_tests_passed`: 4.1
- `avg_verified_pass_rate`: 1.0
- Trace count per case: `9+2`

Notes:

- All 20 cases reached runner success and same-container verifier success.
- No insufficient-balance or quota error was detected.
- Secret/balance scan over the GPT result directory found no key leaks and no
  balance-error strings.

## Claude Sonnet 4.6 Limit-20 Run

Command used provider-profile AiGoCode with secret file paths only:

```bash
env AIGOCODE_API_KEY_FILE=/home/zi/AgentCodingDos_CodeAgent/privacy_secret_aigocode_API_key.txt AIGOCODE_OPENAI_API_KEY_FILE=/home/zi/AgentCodingDos_CodeAgent/privacy_secret_aigocode_openai_API_key.txt AIGOCODE_GEMINI_API_KEY_FILE=/home/zi/AgentCodingDos_CodeAgent/privacy_secret_aigocode_gemini_API_key.txt AIGOCODE_ANTHROPIC_API_KEY_FILE=/home/zi/AgentCodingDos_CodeAgent/privacy_secret_aigocode_anthropic_API_key.txt AIGOCODE_BASE_URL=https://api.aigocode.com OPENCODE_PROVIDER_PROFILE=aigocode OPENCODE_CONTAINER_NAME=opencode PYTHONPATH=/home/zi/AgentCodingDos_CodeAgent uv run --no-sync python -m experiments.AgentCallInterface.coding_evaluation.opencode_formal_dryrun --model-label claude_sonnet_4_6 --model anthropic/claude-sonnet-4-6 --container opencode --limit 20 --pass-count 6 --pass-threshold 2 --timeout 420 --reset-timeout 60 --verifier-timeout 60 --output-root experiments/results/aigocode_opencode_limit20/claude_sonnet_4_6 --stop-on-balance-error
```

Result directory:

- `experiments/results/aigocode_opencode_limit20/claude_sonnet_4_6/opencode_formal_dryrun_20260506_134502_090101`

Result:

- `N`: 20
- `runner_success_rate`: 0.75
- `verifier_run_rate`: 1.0
- `balance_error_rate`: 0.0
- `TSR`: 0.75
- `STRICT_TSR`: 0.75
- `P_ASR`: 0.0
- `T_ASR`: 0.05
- `R_ASR`: 0.0
- `STRICT_E2E_ASR`: 0.0
- `avg_verified_tests_passed`: 3.95
- `avg_verified_pass_rate`: 0.95

Notes:

- No insufficient-balance or quota error was detected.
- Sonnet completed the programming task on many cases but often skipped or timed
  out on the injected ledger workflow. Several cases had verifier pass but
  `runner_succeeded=False` because injection or follow-up timed out.
- Secret/balance scan over the Sonnet result directory found no key leaks and no
  balance-error strings.

## Gemini 3.1 Pro Preview Limit-20 Run

Command used provider-profile AiGoCode with secret file paths only:

```bash
env AIGOCODE_API_KEY_FILE=/home/zi/AgentCodingDos_CodeAgent/privacy_secret_aigocode_API_key.txt AIGOCODE_OPENAI_API_KEY_FILE=/home/zi/AgentCodingDos_CodeAgent/privacy_secret_aigocode_openai_API_key.txt AIGOCODE_GEMINI_API_KEY_FILE=/home/zi/AgentCodingDos_CodeAgent/privacy_secret_aigocode_gemini_API_key.txt AIGOCODE_ANTHROPIC_API_KEY_FILE=/home/zi/AgentCodingDos_CodeAgent/privacy_secret_aigocode_anthropic_API_key.txt AIGOCODE_BASE_URL=https://api.aigocode.com OPENCODE_PROVIDER_PROFILE=aigocode OPENCODE_CONTAINER_NAME=opencode PYTHONPATH=/home/zi/AgentCodingDos_CodeAgent uv run --no-sync python -m experiments.AgentCallInterface.coding_evaluation.opencode_formal_dryrun --model-label gemini_3_1_pro_preview --model gemini/gemini-3.1-pro-preview --container opencode --limit 20 --pass-count 6 --pass-threshold 2 --timeout 420 --reset-timeout 60 --verifier-timeout 60 --output-root experiments/results/aigocode_opencode_limit20/gemini_3_1_pro_preview --stop-on-balance-error
```

Result directory:

- `experiments/results/aigocode_opencode_limit20/gemini_3_1_pro_preview/opencode_formal_dryrun_20260506_154704_717709`

Result:

- `N`: 20
- `runner_success_rate`: 0.7
- `verifier_run_rate`: 1.0
- `balance_error_rate`: 0.0
- `TSR`: 0.7
- `STRICT_TSR`: 0.7
- `P_ASR`: 0.85
- `T_ASR`: 0.15
- `R_ASR`: 0.7
- `STRICT_E2E_ASR`: 0.05
- `avg_verified_tests_passed`: 3.65
- `avg_verified_pass_rate`: 0.9

Notes:

- No insufficient-balance or quota error was detected.
- Gemini sometimes completed the injected ledger and follow-up trace, but some
  cases timed out or failed verifier correctness.
- Secret/balance scan over the Gemini result directory found no key leaks and no
  balance-error strings.
