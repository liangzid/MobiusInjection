# 2026-05-04 Remove Queue-Externality Figure 5

## User Request

Dr. Frost asked to delete Figure 5 because the single-column distribution figure
was visually weak and repeated information already expressed by the bar chart.

## Files

- `/home/zi/paper_mobius/exper.tex`
- `/home/zi/paper_mobius/main.pdf`
- `tasks/session_record_20260504_remove_queue_externality_figure5.md`
- `WORKLOG.md`

## Actions

- Removed the single-column `figure` environment that included
  `curves/agent_ddos_queue_externality_timeline.pdf`.
- Removed the label `fig:agent-ddos-queue-externality-timeline` from the paper.
- Changed the surrounding text from a two-figure reference to a single reference
  to `fig:agent-ddos-queue-externality-bars`.
- Left the generated timeline/distribution artifact files in place as experiment
  outputs, but they are no longer included in the paper.

## Verification

- Searched `exper.tex` for the removed label and caption text; no matches remain.
- Ran `latexmk -pdf main.tex` in `/home/zi/paper_mobius`.

## Results

- `/home/zi/paper_mobius/main.pdf` now has 11 pages again.
- The queue-externality result is represented only by Figure 4, the `1x3` bar
  chart.
- Remaining LaTeX warnings are existing unresolved citations/references outside
  this change.
