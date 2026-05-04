# Session Record: Defense Under Queue Pressure

Date: 2026-05-04

## User Request

Dr. Frost rejected the proposed benign-agent collateral-damage experiment as
likely weak because task failure may not be high enough. The requested next
step was to try the second recommendation instead and put the comparison into
the defense subsection as a new subsubsection.

## Files Touched

- `/home/zi/paper_mobius/exper.tex`
- `/home/zi/paper_mobius/main.pdf`
- `experiments/results/opencode_queue_externality_20260504/build_defense_under_pressure.py`
- `experiments/results/opencode_queue_externality_20260504/test_build_defense_under_pressure.py`
- `experiments/results/opencode_queue_externality_20260504/defense_under_pressure.csv`
- `experiments/results/opencode_queue_externality_20260504/defense_under_pressure.md`
- `tasks/session_record_20260504_defense_under_queue_pressure.md`
- `WORKLOG.md`

## Actions

- Added a measured-load replay script that derives a defense-under-pressure
  comparison from the existing real queue-externality measurements.
- Added tests for the replay table generation and metric calculations.
- Generated CSV and Markdown outputs for the defense comparison.
- Added `\subsubsection{Defense Under Queue Pressure}` to the paper defense
  subsection.
- Added a paper table comparing no defense, runtime caps, and ACE quarantine
  under measured queue pressure.
- Described the table as a measured-load replay rather than a new online
  defense implementation.

## Results

The generated comparison table is:

| Defense policy | Residual poisoned nodes | Benign p95 | >10s probes | Max queue | p95 excess removed |
| --- | ---: | ---: | ---: | ---: | ---: |
| No defense | 4 | 113.0s | 100.0% | 11 | 0.0% |
| Runtime cap (`N<=2`) | 2 | 18.9s | 13.8% | 5 | 83.7% |
| Runtime cap (`N<=1`) | 1 | 10.2s | 5.6% | 3 | 91.3% |
| ACE quarantine | 0 | 0.49s | 0.0% | 1 | 100.0% |

Internal interpretation:

- The no-defense row uses the observed `N=4` queue-externality run.
- The runtime-cap rows use measured `N=2` and `N=1` load levels as proxies.
- ACE quarantine maps to the measured `N=0` baseline because the suspicious
  component is blocked before trigger-time invocation.
- `p95 excess removed` is computed relative to the `N=4` attack and `N=0`
  baseline.

## Verification

- `uv run pytest experiments/results/opencode_queue_externality_20260504 -q`
  passed: `17 passed in 0.04s`.
- `latexmk -pdf main.tex` in `/home/zi/paper_mobius` completed with
  `All targets (main.pdf) are up-to-date`.
