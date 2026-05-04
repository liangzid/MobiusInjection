# 2026-05-04 - Plan B experiment-shape clarification

## User Request

Dr. Frost asked, based on the 2026-05-02 Research Plan B, what the final
exported experiments for evaluating Mobius Injection would look like.

## Files Inspected

- `tasks/research_plan_0502_ddos_b_network_stealth_ids.md`
- `tasks/session_record_20260503_agent_ddos_curve.md`
- `tasks/session_record_20260503_opencode_time_window_free_run.md`
- `WORKLOG.md`

## Actions Performed

- Identified Plan B as the network-traffic stealth and classical DoS/IDS
  contrast plan.
- Extracted the planned traffic classes, observability layers, detector
  baselines, concrete experiments, metrics, and expected paper outputs.
- Prepared a Chinese summary for the user explaining the final experiment form.

## Result

Plan B exports a controlled local-lab experiment suite comparing benign agent
traffic, Mobius stealth traffic, Mobius aggressive traffic, and classical local
SYN/HTTP-flood-like baselines. The main outputs are a detector-layer comparison
table, a traffic feature-space plot, and a detection-timing-by-layer figure.
