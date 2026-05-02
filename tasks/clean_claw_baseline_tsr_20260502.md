# Clean ClawBench TSR Baseline, 2026-05-02

## User Request

Run the batch experiments for the three clean claw-style agent containers as the
baseline TSR values for Table 1 in `~/paper_mobius/exper.tex`.

## Implementation

- Added clean baseline runner:
  - `experiments/scripts/effectiveness_clean_claw_0.1.0.baseline_tsr.py`
- Added tests:
  - `experiments/AgentCallInterface/tests/test_clean_claw_baseline_runner.py`
- Runner behavior:
  - uses the Plan-A 44-task taskset:
    `experiments/configs/context_injection_add_s_taskset_plan_a.toml`;
  - runs clean workspaces only;
  - does not apply any injection payload;
  - does not run reopened MCP calling;
  - writes `results.jsonl`, `batch_metrics.json`, and `batch_metrics.md`;
  - reports clean verifier TSR overall and per ClawBench category.

## Clean Images

- OpenClaw: `openclaw:edit_m_mcp_victim`
- Hermes: `hermes:edit_m_mcp_victim`
- ZeroClaw: `zeroclaw:edit_m_mcp_workspace_victim`

These are clean victim images with the preconfigured benign MCP environment used
for the EDIT_M experiments, but no task payload is injected during this baseline
run.

## Verification

- Command:
  `env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=/home/zi/AgentCodingDos uv run pytest experiments/AgentCallInterface/tests/test_clean_claw_baseline_runner.py -q`
- Result:
  `3 passed in 0.06s`

## Batch Launch

- OpenClaw:
  - tmux session: `clean_tsr_openclaw_planA`
  - run id: `clean_tsr_openclaw_planA_kimi_20260502`
  - log root:
    `/home/zi/agentcodingdos_context_injection_runs/logs/clean_tsr_openclaw_planA_kimi_20260502`
- Hermes:
  - tmux session: `clean_tsr_hermes_planA`
  - run id: `clean_tsr_hermes_planA_kimi_20260502`
  - log root:
    `/home/zi/agentcodingdos_context_injection_runs/logs/clean_tsr_hermes_planA_kimi_20260502`
- ZeroClaw:
  - tmux session: `clean_tsr_zeroclaw_planA`
  - run id: `clean_tsr_zeroclaw_planA_kimi_20260502`
  - log root:
    `/home/zi/agentcodingdos_context_injection_runs/logs/clean_tsr_zeroclaw_planA_kimi_20260502`

## Current Status

- All three clean baseline batch sessions completed.
- Each run produced 44 `results.jsonl` rows.
- A previous direct OpenClaw smoke run was interrupted before it produced
  `results.jsonl`; its orphan clean container was removed and is not counted as
  an experiment result.

## Final Results

- OpenClaw:
  - rows: `44`
  - overall TSR: `24/44 = 0.545`
  - category TSR:
    - Daily Life: `7/11 = 0.636`
    - Social: `8/11 = 0.727`
    - Office: `8/11 = 0.727`
    - Dev: `1/11 = 0.091`
  - caller success: `41/44 = 0.932`
- Hermes:
  - rows: `44`
  - overall TSR: `21/44 = 0.477`
  - category TSR:
    - Daily Life: `6/11 = 0.545`
    - Social: `8/11 = 0.727`
    - Office: `7/11 = 0.636`
    - Dev: `0/11 = 0.000`
  - caller success: `34/44 = 0.773`
- ZeroClaw:
  - rows: `44`
  - overall TSR: `19/44 = 0.432`
  - category TSR:
    - Daily Life: `6/11 = 0.545`
    - Social: `7/11 = 0.636`
    - Office: `5/11 = 0.455`
    - Dev: `1/11 = 0.091`
  - caller success: `32/44 = 0.727`

## Paper Update

- User request: edit these clean baseline results into
  `~/paper_mobius/exper.tex` and re-compile the LaTeX paper.
- Updated file:
  `/home/zi/paper_mobius/exper.tex`
- Updated Table 1 agent baseline rows:
  - OpenClaw: Daily Life `63.6%`, Social `72.7%`, Office `72.7%`,
    Dev `9.1%`, Overall `54.5%`
  - ZeroClaw: Daily Life `54.5%`, Social `63.6%`, Office `45.5%`,
    Dev `9.1%`, Overall `43.2%`
  - Hermes: Daily Life `54.5%`, Social `72.7%`, Office `63.6%`,
    Dev `0.0%`, Overall `47.7%`
- Non-TSR baseline ASR columns were marked `--`, because clean baseline runs do
  not have injection, trigger, or recurse attack-success metrics.
- Compile command:
  `latexmk -pdf -interaction=nonstopmode main.tex`
- Compile result:
  success, regenerated `/home/zi/paper_mobius/main.pdf`.
- Remaining LaTeX warnings:
  existing unresolved citations and references remain, but the compile did not
  fail.
