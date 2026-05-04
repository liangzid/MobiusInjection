# 2026-05-04 Revise Queue-Externality Plot

## User Request

Dr. Frost asked to revise the queue-externality figures so that:

- bar-chart amplification labels keep one decimal place instead of pure integers;
- the benign probe latency timeline does not mislead readers into thinking the
  Mobius loop naturally stops or that latency follows a continuous decreasing
  trajectory;
- the figure remains rigorous and honest while still communicating the value of
  the result.

## Files

- `experiments/results/opencode_queue_externality_20260504/plot_opencode_queue_externality.py`
- `experiments/results/opencode_queue_externality_20260504/test_plot_opencode_queue_externality.py`
- `experiments/results/opencode_queue_externality_20260504/opencode_queue_externality_bars.pdf`
- `experiments/results/opencode_queue_externality_20260504/opencode_queue_externality_bars.png`
- `experiments/results/opencode_queue_externality_20260504/opencode_queue_externality_timeline.pdf`
- `experiments/results/opencode_queue_externality_20260504/opencode_queue_externality_timeline.png`
- `/home/zi/paper_mobius/curves/agent_ddos_queue_externality_bars.pdf`
- `/home/zi/paper_mobius/curves/agent_ddos_queue_externality_timeline.pdf`
- `/home/zi/paper_mobius/exper.tex`
- `/home/zi/paper_mobius/main.pdf`
- `tasks/session_record_20260504_revise_queue_externality_plot.md`
- `WORKLOG.md`

## Actions

- Changed bar-chart multiplier labels to one decimal place:
  - latency: `20.8x`, `38.2x`, `229.1x`;
  - queue occupancy: `3.0x`, `5.0x`, `11.0x`.
- Kept absolute percentage labels for the SLA panel because its `N=0`
  baseline is `0%`, so finite multiplicative growth is undefined.
- Replaced the single-column timeline line plot with a log-scale sample plot:
  - only real attack-window benign probe samples are plotted;
  - samples are not connected by interpolated lines;
  - vertical stems show measured latency;
  - the `10s` SLA threshold is marked;
  - timed-out probes are marked with crosses.
- Updated the paper caption and surrounding text to state that the poisoned
  OpenCode processes are bounded by the 180-second measurement timeout in this
  experiment, so the figure does not claim this run observes an unbounded attack.

## Verification

- `uv run pytest experiments/results/opencode_queue_externality_20260504 -q`
  passed with `12` tests.
- `uv run --with matplotlib python experiments/results/opencode_queue_externality_20260504/plot_opencode_queue_externality.py`
  regenerated all queue-externality artifacts.
- Copied and cropped the revised PDFs into `/home/zi/paper_mobius/curves/`.
- `latexmk -pdf main.tex` completed in `/home/zi/paper_mobius`.
- Rendered pages `10` and `11` of `/home/zi/paper_mobius/main.pdf` and
  visually inspected Figures 4 and 5.

## Results

- Figure 4 now uses one-decimal multiplier labels and remains readable.
- Figure 5 now presents the real attack-window samples without a misleading
  connected curve or recovery-drain implication.
- Remaining LaTeX warnings are existing unresolved citations/references outside
  this figure revision: `Liu-Prompt`, `Greshake-Not`, `Abdelnabi-Not`,
  `clawbench`, `swebench`, `humaneval`, `fig:`, and `fig:mobius-example`.
