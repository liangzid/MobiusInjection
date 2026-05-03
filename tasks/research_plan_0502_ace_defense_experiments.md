# Research Plan: ACE Defense Experiments for Mobius Injection

Date: 2026-05-02

## Goal

This plan designs the defense experiment section for Mobius Injection. The main claim is that existing LLM/API DoS defenses operate at the request, generation, traffic, or prompt boundary, while Mobius Injection exploits persistent agent components. We therefore evaluate mainstream defenses and propose **Agent Component Entropy (ACE)** as a component-layer defense under the paper's agent execution graph abstraction.

## Paper Context

The current paper formalizes task-level agent execution as a message-labeled directed graph:

\[
\mathcal{G}_{\mathcal{A}}=(\mathcal{V},\mathcal{E},\mu)
\]

where vertices are agent components, directed edges are component invocations, and edge labels carry messages. The relevant vertex classes are:

- \(u, \pi\): user and agent policy.
- \(\mathcal{X}\): mutable extensions, including skills, plugins, MCP tool descriptions, memory entries, configuration files, slash commands, and workflow templates.
- \(\mathcal{D}\): resource vertices, including LLM APIs, MCP servers, model gateways, plugin marketplaces, web services, and other paid/rate-limited backends.
- \(\mathcal{I}\): ingress vertices, including web fetchers, repository readers, document loaders, email readers, shell-mediated retrieval, and metadata loaders.

Mobius Injection starts from an adversarial ingress message \(m^\star\), induces policy \(\pi\) to add or edit mutable components \(X^\star \subseteq \mathcal{X}\), and creates a recursive path that repeatedly reaches \(\mathcal{D}\). The defense section should therefore evaluate whether a defense can stop the attack at three stages:

- **Pre-grafting:** before \(m^\star\) becomes a mutable component.
- **Post-grafting / pre-trigger:** after a component is polluted, but before recursive execution starts.
- **Runtime recurrence:** after recursive execution begins and resources are already being consumed.

ACE's main value should be framed as early detection at the post-grafting / pre-trigger stage.

## Baseline Defenses

### B0. No Defense

Run the existing Mobius experiment unchanged. This establishes the reference TSR, P-ASR, T-ASR, R-ASR, calling count, tokens, and cost.

### B1. Resource-Budget Defense

This is the engineering baseline derived from OWASP LLM Model DoS / Unbounded Consumption recommendations:

- max input/output tokens per call;
- max tool calls per task;
- max recursive invocations per component;
- max wall-clock duration;
- max queued actions;
- per-user or per-agent rate limit;
- circuit breaker for repeated calls to the same resource vertex \(d \in \mathcal{D}\).

Expected behavior:

- It should reduce resource damage and residual \#C/cost.
- It may not reduce P-ASR because component pollution can still happen.
- It may not reduce T-ASR if the payload triggers before the budget is exhausted.

Experiment adaptation:

- Implement as a wrapper around agent execution logs and tool/API call counters where direct framework-level limits are not available.
- Use the same clean and injected runs; compare residual ASR and resource consumption.

### B2. LLM-PD-Style Proactive DoS Defense

Baseline from *Toward Intelligent and Secure Cloud: Large Language Model Empowered Proactive Defense* (LLM-PD, arXiv:2412.21051 / IEEE Communications Magazine accepted). LLM-PD is designed for cloud-network DoS defense through LLM-driven data reconstruction, risk assessment, decision-making, deployment, and feedback.

Experiment adaptation:

- Treat the agent runtime as the monitored "cloud service".
- Feed execution summaries to a defender LLM:
  - recent tool/API calls;
  - resource usage;
  - invoked component names;
  - high-level task goal;
  - observed repeated resource access.
- Ask the defender to classify whether the run is a DoS risk and propose mitigation.

Expected behavior:

- It may detect aggressive runtime DoS symptoms.
- It is unlikely to detect dormant or stealthy component grafting unless component diffs are explicitly provided.
- It is a strong contrast point: proactive defense at infrastructure/behavior level vs. ACE at component-graph level.

### B3. RecurrentDetector / Loop-Detection Defense

Baseline from *Breaking the Loop* (arXiv:2503.00416). The original RecurrentDetector is white-box and detects recurrent generation using activation-state similarity. Since our target agents mostly use black-box APIs, we evaluate a deployable proxy:

- repeated output n-grams;
- repeated tool-call sequences;
- repeated resource vertex \(d\) invocations;
- repeated semantic intent labels over consecutive steps;
- response-length and token-growth anomaly.

Expected behavior:

- It should detect simple self-loop or repetitive response patterns.
- It may miss Mobius strips that use semantic closure: each local step appears terminal or semantically different, while global recurrence persists.
- It operates mainly at runtime, so it cannot prevent P-ASR.

### B4. Prompt-Injection Boundary Defense

Use one or both of the following:

- **PromptArmor-style sanitizer:** detect and remove injected instructions before the agent processes the input.
- **StruQ-style structured separation:** separate trusted task instructions from untrusted data and prevent untrusted data from becoming executable instructions.

Experiment adaptation:

- Apply the defense to ingress messages \(\mu(i,\pi)\) before the agent sees retrieved task documents, issue text, README content, tool metadata, or MCP descriptions.
- For structured separation, mark external content as `UNTRUSTED_DATA` and instruct the agent that it cannot create/edit skills, memory, MCP configs, or workflow templates based solely on such content.

Expected behavior:

- It should reduce P-ASR for direct context injection.
- It may be weaker against structured extension and protocol-driven service vectors where malicious text is embedded inside apparently legitimate component metadata.
- It may have utility cost if it blocks benign component creation or update tasks.

## Proposed Defense: Agent Component Entropy (ACE)

### Core Idea

ACE monitors the evolution of the agent execution graph at the component layer. Instead of only checking whether the agent is consuming too many resources, ACE asks whether the graph is becoming structurally and semantically abnormal around mutable components \(\mathcal{X}\).

ACE should not be framed as generic text entropy. The score should combine multiple component-level signals:

1. **Component Mutation Entropy**
   - Measures how edits are distributed across mutable components.
   - Signals sudden addition/editing of skills, memory, configs, MCP entries, slash commands, or workflow templates.
   - Captures ADD/EDIT grafting before runtime recursion starts.

2. **Instruction Density Shift**
   - Measures the increase in imperative, persistent, recursive, or tool-execution language inside components.
   - Example signals: "always", "on every", "continue", "call", "invoke", "run", "repeat", "fallback", "audit", "quality pass", "runner line", "closing pass".

3. **Execution-Affordance Delta**
   - Measures whether a component gained new ability to create edges in the graph:
     - new tool calls;
     - new MCP server/tool definitions;
     - new shell/API invocation instructions;
     - new hooks tied to common events;
     - new follow-up command extraction patterns.

4. **Cross-Component Propagation Entropy**
   - Measures whether similar directives, marker phrases, or closure-calling templates appear across multiple component classes \(S, M, C\).
   - Mobius payloads should leave propagation structure because they need persistence and triggerability.

5. **Temporal Persistence Score**
   - Measures whether suspicious component changes survive across tasks/sessions.
   - This separates benign one-off task output from persistent agent compromise.

6. **Runtime Graph Entropy**
   - Measures the entropy of component invocations and resource calls over a sliding window.
   - Benign tasks should show diverse but task-bounded expansion.
   - Mobius strips may show local semantic variation but repeated reachability to resource vertices \(\mathcal{D}\).

### ACE Score

For each run \(r\), compute:

\[
ACE(r)=w_m H_m + w_i \Delta I + w_a \Delta A + w_p H_p + w_t P_t + w_g H_g
\]

where:

- \(H_m\): component mutation entropy;
- \(\Delta I\): instruction density shift;
- \(\Delta A\): execution-affordance delta;
- \(H_p\): cross-component propagation score;
- \(P_t\): temporal persistence score;
- \(H_g\): runtime graph entropy / recurrence score.

Weights should first be uniform to avoid overfitting. A later ablation can show which signal matters most. Thresholds should be calibrated from clean runs only, per agent family, using percentile-based thresholds such as p95 or p99.

### ACE Intervention Modes

Evaluate ACE in three modes:

- **Detect-only:** report alerts without blocking.
- **Quarantine:** prevent newly added or edited suspicious components from being invoked until approved.
- **Rollback / sanitize:** restore the previous clean component snapshot or remove suspicious closure-calling lines.

The main paper experiment can use detect-only and quarantine. Rollback can be a discussion or appendix because it may be framework-specific.

## Experimental Matrix

### Agents

Use the agents already evaluated in the paper:

- Claw-style agents: OpenClaw, ZeroClaw, Hermes.
- Coding agents: start with one representative agent if time is limited, then extend to Claude Code / OpenCode / Kilo Code if available.

### Component Classes

Use the current Mobius injection taxonomy:

- ADD-S, EDIT-S;
- ADD-M, EDIT-M;
- ADD-C, EDIT-C;
- optionally ADD-MCP / EDIT-MCP if folded into C or separately represented.

### Task Sets

Minimum plan:

- ClawBench 44-task Plan-A taskset for Claw-style agents.
- One coding-agent taskset such as HumanEval or SWE-Bench Lite Mini for coding agents.

The defense study does not need to rerun the full attack matrix initially. It can replay representative successful attack cases selected from prior logs:

- high-success component class: ADD-S or ADD-M;
- lower-success but realistic stealth class: EDIT-S;
- config/protocol-oriented class: ADD-C or EDIT-C.

### Runs

For each selected agent/task/component condition:

1. Clean run, no attack, no defense.
2. Attack run, no defense.
3. Attack + B1 resource-budget defense.
4. Attack + B2 LLM-PD-style defender.
5. Attack + B3 loop detector.
6. Attack + B4 prompt-injection boundary defense.
7. Attack + ACE detect-only.
8. Attack + ACE quarantine.

If time is limited, prioritize:

- no defense;
- B1;
- B3;
- B4;
- ACE quarantine.

LLM-PD can be evaluated on fewer representative cases because it requires extra defender LLM calls and is less directly matched to agent-component compromise.

## Metrics

Reuse existing attack metrics:

- TSR: task success rate.
- P-ASR: component pollution success rate.
- T-ASR: trigger success rate.
- R-ASR: recursive execution success rate.
- \#C: injected component/tool calling times.
- API calls, generated tokens, estimated victim-side cost, wall-clock duration, local CPU/memory.
- Amplification factor relative to one-time injection cost.

Add defense metrics:

- Detection rate / TPR.
- False positive rate on clean runs.
- Time to detection (TTD), measured as:
  - before component write;
  - after component write but before trigger;
  - after trigger but before second recursive call;
  - after resource budget damage.
- Residual P-ASR, T-ASR, R-ASR.
- Residual cost and residual \#C.
- Utility loss: TSR drop under clean defended runs.
- Component rollback/quarantine precision: fraction of quarantined components that actually contain Mobius logic.

The most important ACE-specific metric is **pre-trigger detection rate**, because this is where existing resource and loop defenses are weakest.

## Expected Results and Claims

Expected qualitative outcomes:

- B1 should reduce cost but not P-ASR.
- B2 should detect visible DoS symptoms but may miss dormant component grafting.
- B3 should catch explicit loops but miss semantic-closure Mobius strips.
- B4 should reduce direct context injection, but may struggle with structured extension/protocol-driven component metadata.
- ACE should reduce P-ASR/T-ASR/R-ASR by detecting abnormal component mutation and execution affordance before recursive runtime damage.

Target paper claim:

> ACE complements existing DoS defenses by moving detection from resource exhaustion to agent-component graph drift. It detects Mobius-style persistence before the attack manifests as repeated API calls or token consumption.

## Suggested Tables and Figures

### Table 1: Defense Comparison

Columns:

- Defense;
- Observation layer;
- Requires model internals?;
- Detects P-ASR?;
- Detects T/R-ASR?;
- Blocks before resource consumption?;
- Expected weakness.

Rows:

- Resource-budget defense;
- LLM-PD;
- RecurrentDetector / loop detector;
- PromptArmor / StruQ;
- ACE.

### Table 2: Defense Evaluation

Columns:

- Agent;
- Attack type;
- Defense;
- TSR;
- P-ASR;
- T-ASR;
- R-ASR;
- \#C;
- Cost;
- TPR;
- FPR;
- TTD.

### Figure 1: Defense Placement on Agent Execution Graph

Show:

- ingress \(i\);
- policy \(\pi\);
- mutable components \(\mathcal{X}\);
- resource vertices \(\mathcal{D}\);
- recursive Mobius path;
- where each baseline observes:
  - B4 at \(\mu(i,\pi)\);
  - B1/B3 near runtime path to \(\mathcal{D}\);
  - B2 around resource behavior summaries;
  - ACE around \(\mathcal{X}\) mutation and graph drift.

### Figure 2: Detection Timing

Timeline:

1. Ingress text retrieved.
2. Component added/edited.
3. Trigger invoked.
4. Recursive path reaches \(\mathcal{D}\).
5. Resource exhaustion/cost accumulation.

Plot detection timing distribution for B1/B3/B4/ACE.

## Implementation Notes

### Data Collection

Do not use mocked data. Collect all signals from real agent runs:

- pre-run and post-run snapshots of skills, memory, configs, MCP/tool registries;
- file diffs;
- tool/API call logs;
- session transcript;
- resource counters;
- verifier outputs for P-ASR/T-ASR/R-ASR.

### ACE Prototype

Start with an offline verifier over existing logs:

1. Parse component snapshots before and after each run.
2. Extract component diffs and invocation traces.
3. Compute ACE features.
4. Calibrate clean thresholds.
5. Score attack runs.
6. Report detection timing and residual ASR under simulated quarantine.

Then implement online quarantine for one agent family:

- before the agent invokes a newly added/edited component, ACE checks the component diff;
- if score exceeds threshold, the component is quarantined and the run proceeds without invoking it.

### Minimal Scope for First Experiment

Recommended first defensible scope:

- Agents: OpenClaw, ZeroClaw, Hermes.
- Tasks: ClawBench Plan-A.
- Attacks: ADD-S, EDIT-S, ADD-M, ADD-C.
- Baselines: no defense, B1, B3, B4, ACE detect-only, ACE quarantine.
- Metrics: TSR, P-ASR, T-ASR, R-ASR, \#C, cost proxy, TPR, FPR, TTD.

This scope is enough to show the core claim without expanding too early into every coding-agent framework.

## Risks and Controls

- **Risk: ACE sounds like simple entropy.**
  - Control: define ACE as a component-graph drift score, not raw Shannon entropy over text.

- **Risk: normal tasks legitimately edit components.**
  - Control: include clean defended runs and component-maintenance benign tasks; report FPR and TSR drop.

- **Risk: thresholds overfit one agent.**
  - Control: calibrate per agent family on clean runs; report cross-task generalization.

- **Risk: ACE blocks useful self-improvement.**
  - Control: compare detect-only and quarantine; add an approval-gate interpretation for production deployment.

- **Risk: LLM-PD adaptation is unfair.**
  - Control: explicitly state that LLM-PD is a cloud-network DoS defense baseline and is adapted to the closest available agent telemetry; the comparison illustrates layer mismatch, not inferiority of LLM-PD in its original domain.

## Next Steps

1. Finalize the defense baseline list in the paper.
2. Implement an offline ACE scorer over existing Mobius run logs.
3. Build clean-run calibration sets for OpenClaw, ZeroClaw, and Hermes.
4. Replay representative attack logs to estimate detect-only ACE performance.
5. Implement online ACE quarantine for one agent and rerun selected attacks.
6. Add defense evaluation table and graph-placement figure to `exper.tex`.
