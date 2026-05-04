# 2026-05-04 Split Queue-Externality Figure

## User Request

Dr. Frost asked to make the first three queue-externality subfigures less
monotonic by converting them into a `1x3` bar chart, marking the `0` poisoned
node baseline with dashed horizontal reference lines and multiplier labels, and
moving the fourth subfigure into a single-column `1x1` figure.

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
- `tasks/session_record_20260504_split_queue_externality_figure.md`
- `WORKLOG.md`

## Actions

- Added separate queue-externality plotting outputs for:
  - a double-column `1x3` bar chart over poisoned-node counts `N=0,1,2,4`;
  - a single-column `1x1` benign-probe latency timeline.
- Added dashed `N=0` baseline reference lines to the bar chart.
- Added multiplier labels where a multiplier is defined:
  - benign probe p95 latency: `21x`, `38x`, `229x`;
  - inferred queue occupancy: `3x`, `5x`, `11x`.
- Used absolute percentage labels for the SLA violation panel because the
  `N=0` baseline is `0%`, so a finite multiplier is undefined.
- Kept the original `2x2` combined figure output for reproducibility.
- Copied and cropped the new PDFs into `/home/zi/paper_mobius/curves/`.
- Updated `/home/zi/paper_mobius/exper.tex` to use:
  - `fig:agent-ddos-queue-externality-bars` as a double-column bar figure;
  - `fig:agent-ddos-queue-externality-timeline` as a single-column timeline
    figure.

## Verification

- `uv run pytest experiments/results/opencode_queue_externality_20260504 -q`
  passed with `10` tests.
- `uv run --with matplotlib python experiments/results/opencode_queue_externality_20260504/plot_opencode_queue_externality.py`
  regenerated all queue-externality PDF/PNG artifacts.
- `latexmk -pdf main.tex` completed in `/home/zi/paper_mobius` and produced
  `main.pdf`.
- Rendered pages `10` and `11` of `main.pdf` with `pdftoppm` and visually
  inspected the placement.

## Results

- The bar figure appears as Figure 4 on page 10 and is readable in the compiled
  PDF.
- The timeline appears as Figure 5 on page 11 as a single-column `1x1` figure.
- The new labels `fig:agent-ddos-queue-externality-bars` and
  `fig:agent-ddos-queue-externality-timeline` resolve after recompilation.
- Remaining LaTeX warnings are pre-existing unresolved citations/references:
  `Liu-Prompt`, `Greshake-Not`, `Abdelnabi-Not`, `clawbench`, `swebench`,
  `humaneval`, `fig:`, and `fig:mobius-example`.
