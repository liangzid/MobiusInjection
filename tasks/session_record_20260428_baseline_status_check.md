# Session Record: Baseline and Interrupted Run Status Check

Date: 2026-04-28

## User Request

Dr. Frost asked whether the previous baseline runs were still running after an interrupted turn.

## Checks Performed

- Checked process table for qwen36plus baseline, Claude baseline, injection rerun, agent CLI, and benchmark runner processes.
- Counted completed analysis files from the relevant manifests:
  - `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_baseline_no_injection_20260427`
  - `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_baseline_raw_limit20_20260427`
  - `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_20260427`
- Checked latest file timestamps in the interrupted Claude Code injection rerun root.

## Results

- No baseline-related runner or agent CLI processes were still running.
- No `claude --dangerously-skip-permissions`, `opencode run`, or `kilo run` process from those runs remained.
- Baseline completion status:
  - All-agent no-injection baseline HumanEval: complete for `opencode`, `kilo_code`, and `claude_code`.
  - All-agent no-injection baseline SWE-bench: complete for `opencode` and `kilo_code`; Claude row in that root is partial, superseded by the separate Claude raw baseline.
  - Claude raw no-injection baseline HumanEval and SWE-bench: complete 20/20.
- The interrupted Claude Code injection reparse run completed HumanEval 20/20 in the background after the interruption.
- The corresponding SWE-bench injection reparse run had not been started yet.
