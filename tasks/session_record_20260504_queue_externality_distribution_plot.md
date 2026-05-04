# 2026-05-04 Queue-Externality Distribution Plot

## User Request

Dr. Frost pointed out that the attack-window benign probe sample plot still did
not communicate a clear result and that the samples were too sparse to make a
timeline-style figure meaningful.

## Files

- `experiments/results/opencode_queue_externality_20260504/plot_opencode_queue_externality.py`
- `experiments/results/opencode_queue_externality_20260504/test_plot_opencode_queue_externality.py`
- `experiments/results/opencode_queue_externality_20260504/opencode_queue_externality_timeline.pdf`
- `experiments/results/opencode_queue_externality_20260504/opencode_queue_externality_timeline.png`
- `/home/zi/paper_mobius/curves/agent_ddos_queue_externality_timeline.pdf`
- `/home/zi/paper_mobius/exper.tex`
- `/home/zi/paper_mobius/main.pdf`
- `tasks/session_record_20260504_queue_externality_distribution_plot.md`
- `WORKLOG.md`

## Actions

- Replaced the single-column attack-window sample timeline with a grouped
  latency-distribution plot.
- The revised plot uses only real attack-window benign probe samples and shows:
  - per-node-count point samples;
  - box summaries;
  - black diamond p95 markers;
  - log-scaled latency;
  - 10-second and 30-second service thresholds.
- Updated the paper caption to describe the figure as an attack-window benign
  latency distribution rather than a timeline.

## Verification

- `uv run pytest experiments/results/opencode_queue_externality_20260504 -q`
  passed with `14` tests.
- `uv run --with matplotlib python experiments/results/opencode_queue_externality_20260504/plot_opencode_queue_externality.py`
  regenerated the queue-externality figures.
- Copied and cropped the revised PDF into `/home/zi/paper_mobius/curves/`.
- `latexmk -pdf main.tex` completed in `/home/zi/paper_mobius`.
- Rendered page `11` of `/home/zi/paper_mobius/main.pdf` and visually
  inspected Figure 5.

## Results

- Figure 5 now directly shows that attack-window benign p95 latency rises from
  about `0.5s` at `N=0` to `18.9s` at `N=2` and `113.0s` at `N=4`.
- The figure no longer relies on sparse time samples or an interpolated
  timeline-style visual.
- Remaining LaTeX warnings are existing unresolved citations/references outside
  this figure revision.
