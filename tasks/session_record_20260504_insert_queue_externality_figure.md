# 2026-05-04 - Insert queue-externality figure into paper

## User Request

Dr. Frost asked to add the planned queue-externality figure into the paper.

## Files Modified

- `/home/zi/paper_mobius/curves/agent_ddos_queue_externality.pdf`
- `/home/zi/paper_mobius/exper.tex`
- `/home/zi/paper_mobius/main.pdf`
- `tasks/session_record_20260504_insert_queue_externality_figure.md`
- `WORKLOG.md`

## Actions Performed

- Copied the generated queue-externality PDF from
  `experiments/results/opencode_queue_externality_20260504/opencode_queue_externality.pdf`
  into `/home/zi/paper_mobius/curves/agent_ddos_queue_externality.pdf`.
- Cropped the copied PDF with `pdfcrop`.
- Inserted a new `figure*` into `exper.tex` after the existing Agent-DDoS
  resource-amplification figure and before the defense section.
- Added caption text reporting the key queue-externality results:
  - no poisoned node: benign probe p95 `0.49s`;
  - one poisoned node: benign probe p95 `10.25s`;
  - two poisoned nodes: benign probe p95 `18.86s`;
  - four poisoned nodes: benign probe p95 `112.99s`;
  - four poisoned nodes: all benign probes exceed 10 seconds and two-thirds
    exceed 30 seconds;
  - inferred queue occupancy grows from `1` to `11`.
- Added a short paragraph explaining that the figure demonstrates collateral
  tail-latency damage to unrelated benign requests sharing the same backend.

## Verification

- Ran `latexmk -pdf main.tex` in `/home/zi/paper_mobius`.
- Rendered page 10 and page 11 of `main.pdf` to PNG for visual inspection.

## Result

- The new queue-externality figure appears as Figure 4 on page 11.
- The figure and caption are readable and do not overlap other content.
- `latexmk` completed successfully.
- Existing unresolved citations/references remain unchanged outside this work:
  `Liu-Prompt`, `Greshake-Not`, `Abdelnabi-Not`, `clawbench`, `swebench`,
  `humaneval`, `fig:`, and `fig:mobius-example`.
