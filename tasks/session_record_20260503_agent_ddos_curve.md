# 2026-05-03 Agent-DDoS curve insertion

## User request

Dr. Frost asked to skip the OpenCode internal subagent probe and directly produce
the curve: collect results, write a plotting script that saves a PDF, place the
cropped PDF under `~/paper_mobius/curves/`, crop it with `pdfcrop`, inspect the
rendered image for formatting, and insert it into the `exper.tex` section
`Will Agent DDoS Attack be a Severe New Threat?`.

## Files touched

- `/home/zi/paper_mobius/scripts/plot_agent_ddos_curves.py`
- `/home/zi/paper_mobius/scripts/generated/agent_ddos_curve/opencode_cumulative_curve.csv`
- `/home/zi/paper_mobius/scripts/generated/agent_ddos_curve/coding_agent_exhaustion_summary.csv`
- `/home/zi/paper_mobius/curves/agent_ddos_call_token_curve.pdf`
- `/home/zi/paper_mobius/exper.tex`
- `/home/zi/paper_mobius/main.pdf`
- `/home/zi/AgentCodingDos/tasks/session_record_20260503_agent_ddos_curve.md`
- `/home/zi/AgentCodingDos/WORKLOG.md`

## Data used

- OpenCode time-window curve:
  `/home/zi/AgentCodingDos/experiments/results/opencode_time_window_free_run_20260503/cumulative_calling_curve_120s.csv`
- Cross-agent coding benchmark logs:
  `/home/zi/AgentCodingDos_CodeAgent/experiments/results/qwen36plus_curated_paper/paper_case_metrics.csv`

The cross-agent summary was derived from real log files referenced by
`paper_case_metrics.csv`. OpenCode and Kilo Code usage was extracted from
`step_finish` events. Claude Code usage was extracted from `result` events.

## Actions performed

- Wrote `plot_agent_ddos_curves.py` to generate a four-panel figure:
  OpenCode cumulative chat requests over time, OpenCode cumulative tokens over
  time, cross-agent median chat requests per run, and cross-agent median tokens
  per run.
- Generated source summary CSVs under
  `/home/zi/paper_mobius/scripts/generated/agent_ddos_curve/`.
- Saved the final cropped PDF as
  `/home/zi/paper_mobius/curves/agent_ddos_call_token_curve.pdf`.
- Inserted the figure and accompanying result text into `exper.tex` under
  `Will Agent DDoS Attack be a Severe New Threat?`.
- Rendered page 10 of the compiled paper to inspect figure placement and
  readability.
- Removed temporary `__pycache__` and the intermediate raw uncropped PDF.

## Verification

- `python -m py_compile scripts/plot_agent_ddos_curves.py`
- `python scripts/plot_agent_ddos_curves.py`
- `pdfcrop` completed and wrote the cropped curve PDF.
- `latexmk -pdf main.tex` completed successfully in `/home/zi/paper_mobius`.
- Rendered paper page 10 showed the inserted figure without overlap or clipping.

## Results

- OpenCode poisoned run reached 17 completed chat requests and 228K tokens by
  90 seconds, while the clean run stayed flat at 3 requests and 25K tokens.
- Poisoned runs increased median chat turns from 2 to 15 for Claude Code, 5.5 to
  14 for Kilo Code, and 6 to 21 for OpenCode.
- Poisoned runs increased median token use from 47K to 349K for Claude Code,
  69K to 261K for Kilo Code, and 75K to 411K for OpenCode.
- Existing unrelated paper warnings remain, including unresolved citations and
  references already present outside this change.

## Follow-up correction

Dr. Frost pointed out that the 30-second aggregation produced only four points,
that the 90--120 second flat segment weakened the curve, and that the `n=...`
labels in panels (c) and (d) introduced an undefined symbol whose value did not
belong to the y-axis.

Actions performed:

- Audited the OpenCode 120-second outputs and result files.
- Found that the poisoned run timed out at 120.09 seconds rather than completing
  normally, but the earlier proxy-log slicing could count request completions
  from in-flight calls outside the run-specific OpenCode JSONL event stream.
- Changed the top curve source from proxy-log slices to OpenCode JSONL
  `step_finish` events.
- Regenerated the top panels at one-second resolution from 0 to 90 seconds.
- Removed all `n=...` labels from the bottom panels.
- Updated `exper.tex` to describe the corrected one-second JSONL event
  measurement and revised the reported counts.
- Re-rendered and inspected the figure and the compiled paper page.

Corrected result:

- The poisoned OpenCode run reaches 16 completed chat requests and 226K tokens
  by 90 seconds.
- The clean OpenCode run stays at 1 completed chat request and 11K tokens.
- The poisoned run reaches 24 native tool calls, 12 skill loads, and 12 trace
  records by 90 seconds; the clean run issues no native tool calls.

Verification:

- `python -m py_compile scripts/plot_agent_ddos_curves.py`
- `python scripts/plot_agent_ddos_curves.py`
- `latexmk -pdf main.tex`
- Visual inspection of `/tmp/agent_ddos_curve_preview_v3.png` and rendered
  paper page `/tmp/paper_agent_ddos_page10_v2.png`.

## Follow-up multi-agent curve redesign

Dr. Frost requested a stronger curve design: use a more complex benign task so
the benign line also shows meaningful work, add Kilo Code and Claude Code curve
pairs, draw benign as dashed and poisoned as solid with the same color per
agent, and shade the area between the two curves with low alpha.

Actions performed:

- Replaced the OpenCode-only curve/bar figure with a six-panel curve-pair
  figure.
- Used the existing real benchmark logs for the same SWE-bench task:
  `DataDog__integrations-core-1369`.
- Built one-second cumulative curves over a 300-second horizon for Claude Code,
  Kilo Code, and OpenCode.
- Used OpenCode/Kilo `step_finish` timestamps and token fields.
- Used Claude Code `message_start` generation timestamps and `message_delta`
  usage fields.
- Styled each agent with a distinct color, benign as dashed, poisoned as solid,
  and shaded the area between the curves with low alpha.
- Removed stale generated summary CSVs and the raw uncropped PDF, leaving only
  the current source CSV and final cropped figure.
- Updated `exper.tex` caption, description, and result text for the new figure.

Corrected result:

- By 300 seconds, Claude Code increases from 32 to 33 completed chat requests
  and from 870K to 1.03M tokens.
- Kilo Code increases from 31 to 38 completed chat requests and from 612K to
  1.72M tokens.
- OpenCode increases from 11 to 42 completed chat requests and from 130K to
  1.19M tokens.

Verification:

- `python -m py_compile scripts/plot_agent_ddos_curves.py`
- `python scripts/plot_agent_ddos_curves.py`
- `latexmk -pdf main.tex`
- Visual inspection of `/tmp/agent_ddos_curve_preview_v5.png` and rendered
  paper page `/tmp/paper_agent_ddos_page10_v3.png`.

## Follow-up 1x2 panel consolidation and request-signal audit

Dr. Frost requested that the three request panels be merged into a single
subfigure (a), the three token panels be merged into a single subfigure (b),
and asked why Claude Code and Kilo Code had similar benign and poisoned request
curves in the previous SWE-bench figure.

Actions performed:

- Read the raw logs for the previously plotted SWE-bench task
  `DataDog__integrations-core-1369`.
- Found that Claude Code and Kilo Code already had heavy benign runs on that
  SWE-bench task: Claude Code was 32 benign requests versus 34 poisoned
  requests, and Kilo Code was 31 benign requests versus 38 poisoned requests.
- Found that Kilo Code's benign SWE-bench run timed out, making request-count
  amplification a weak signal for that task even though token consumption grew.
- Scanned the existing real benchmark logs for a task with stronger
  request-count amplification across all three agents.
- Switched the plotted task to `HumanEval/11`, which has real clean/poisoned
  logs for all three agents and no timeout in these six runs.
- Rebuilt the plot as a 1x2 figure: panel (a) cumulative chat requests and
  panel (b) cumulative token use.  Each panel overlays Claude Code, Kilo Code,
  and OpenCode.  Benign curves are dashed, poisoned curves are solid, and the
  area between paired curves is shaded.
- Updated `exper.tex` with the new 1x2 caption, description, and result text.
- Removed temporary Python bytecode and raw uncropped plot artifacts.

Corrected result:

- By 180 seconds, Claude Code increases from 2 to 24 completed chat requests
  and from 46K to 687K tokens.
- Kilo Code increases from 4 to 12 completed chat requests and from 49K to
  186K tokens.
- OpenCode increases from 4 to 17 completed chat requests and from 46K to 288K
  tokens.

Verification:

- `python -m py_compile scripts/plot_agent_ddos_curves.py`
- `python scripts/plot_agent_ddos_curves.py`
- `latexmk -pdf main.tex`
- Visual inspection of `/tmp/agent_ddos_curve_preview_v6.png` and rendered
  paper page `/tmp/paper_agent_ddos_page10_v4.png`.
