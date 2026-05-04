# Session Record: Defense Experiment Result Shape

Date: 2026-05-04

## User Request

Dr. Frost asked to look up the corresponding research plan in `tasks` for the
defense experiments and explain, in Chinese, what the expected results could
look like: a table, a figure, or multiple artifacts.

## Files Checked

- `tasks/research_plan_0502_ace_defense_experiments.md`
- `tasks/defense_literature.md`
- `tasks/research_plan_0502_ddos_b_network_stealth_ids.md`

## Actions

- Searched `tasks` for defense, experiment, and research-plan references.
- Read the ACE defense experiment plan and the defense-literature note.
- Checked the network-stealth IDS plan section that references ACE as a
  component-layer detector.

## Result

The directly corresponding plan is
`tasks/research_plan_0502_ace_defense_experiments.md`.

The planned paper results should be multiple artifacts, not a single table or
figure:

- a defense-comparison table;
- a quantitative defense-evaluation table;
- an agent-execution-graph placement figure;
- a detection-timing figure;
- optionally an ACE ablation/signal-contribution table or figure;
- optionally a resource-consumption/residual-damage curve or bar chart.

Internal conclusion: the core claim needs both quantitative metrics and visual
timing/placement evidence. A single table would be insufficient because ACE's
main claim is pre-trigger component-layer detection, which is clearer as a
timeline/graph-placement result in addition to ASR/cost metrics.
