# Research Plan C: Multi-Zombie Scaling and End-to-End Agent DDoS Severity

Date: 2026-05-02

## Goal

This plan measures whether multiple poisoned agent containers can scale from single-agent resource amplification into an end-to-end agent-based DDoS condition against a local LLM service. It combines the resource metrics from Plan A and the network/IDS observations from Plan B.

The experiment remains local-only and uses isolated containers. The goal is to find the scaling behavior and saturation point of the local LLM service under victim-originated, semantically valid agent traffic.

## Core Claim

Mobius Injection can scale from one zombie agent to multiple zombie agents. Because each zombie issues valid LLM/API calls from a legitimate agent workflow, aggregate resource pressure can increase while remaining less obvious than classical network-layer DoS.

## Research Questions

- **RQ-C1:** How does aggregate LLM-server load scale as the number of poisoned agents increases?
- **RQ-C2:** Does the system show a nonlinear saturation point in p95/p99 latency, queueing, or failed requests?
- **RQ-C3:** How do stealth and aggressive Mobius profiles differ in scaling behavior?
- **RQ-C4:** How much normal workload can the server still serve while poisoned agents are active?
- **RQ-C5:** Which defenses reduce damage most effectively under multi-zombie pressure?

## Experimental Setup

### Topology

```text
N poisoned agent containers
  -> local proxy/logger
  -> local LLM server
  -> local metrics collector

optional:
benign agent containers
  -> same proxy/logger
  -> same local LLM server
```

### Scaling Factors

Use controlled values:

- \(N = 1, 2, 4, 8, 16\) poisoned containers if the server can handle it.
- Stop early if the local server saturates or the machine becomes unstable.

### Workload Profiles

- **Stealth multi-zombie:** each zombie sends low-rate Mobius traffic.
- **Moderate multi-zombie:** medium interval and token budget.
- **Aggressive multi-zombie:** each zombie loops as fast as the agent runtime allows under a fixed cap.

### Benign Background Load

Optionally run benign agents at the same time:

- 0 benign agents;
- 1 benign agent;
- 2 or 4 benign agents if capacity allows.

This measures collateral damage to normal users.

## Experiment C1: Multi-Zombie Scaling Curve

### Procedure

For each \(N\):

1. Start a clean local LLM server.
2. Start \(N\) poisoned agent containers.
3. Assign each container an isolated workspace and stable container id.
4. Trigger the same Mobius payload family.
5. Run for a fixed time window.
6. Collect proxy, server, Docker, and optional GPU metrics.

### Metrics

- aggregate requests/min;
- aggregate tokens/min;
- p50/p95/p99 latency;
- failed request rate;
- server queue length if available;
- CPU/GPU/memory utilization;
- total cost proxy;
- amplification factor per zombie and aggregate amplification factor;
- first saturation point.

### Expected Result

The system should show near-linear growth at small \(N\), then a saturation knee where latency and failures increase nonlinearly.

## Experiment C2: Stealth vs Aggressive Scaling

### Procedure

Repeat C1 under stealth, moderate, and aggressive profiles.

### Metrics

- requests/min per profile;
- tokens/min per profile;
- p95/p99 latency;
- time to saturation;
- IDS/network alert rate;
- ACE alert timing;
- residual damage before detection.

### Expected Result

Aggressive mode reaches saturation faster. Stealth mode may avoid simple network thresholds while still accumulating cost over time.

## Experiment C3: Collateral Damage to Benign Agents

### Procedure

Run benign agent tasks concurrently with \(N\) poisoned agents.

Compare:

- benign-only;
- benign + stealth poisoned agents;
- benign + aggressive poisoned agents.

### Metrics

- benign task completion rate;
- benign task latency;
- benign LLM request latency;
- benign task failure rate;
- poisoned traffic share of total requests/tokens;
- server p95/p99 latency.

### Expected Result

Even if poisoned requests are valid LLM calls, they should degrade benign task latency or completion when aggregate load approaches saturation.

## Experiment C4: Defense Under Multi-Zombie Pressure

### Defenses

Evaluate a reduced set:

- no defense;
- resource-budget defense;
- HTTP/API rate detector or limiter;
- ACE detect-only;
- ACE quarantine.

LLM-PD-style defender can be evaluated on one representative \(N\), but it may be costly and less directly matched.

### Procedure

Use a representative attack configuration from C1/C2, such as:

- \(N=4\) moderate;
- \(N=8\) stealth;
- \(N=4\) aggressive.

Run the defenses and measure residual damage.

### Metrics

- residual P-ASR;
- residual T-ASR;
- residual R-ASR;
- residual requests/tokens;
- p95/p99 latency under defense;
- TPR/FPR;
- TTD;
- benign utility loss;
- blocked/quarantined components.

### Expected Result

Resource budgets reduce damage after runtime starts. ACE should reduce damage earlier by blocking polluted components before they trigger or before they propagate across sessions.

## Experiment C5: Targetability

### Procedure

If the local setup supports multiple model endpoints or multiple local services, configure:

- target model endpoint A;
- non-target endpoint B;
- optional dummy MCP endpoint.

Run targeted Mobius profiles that only call endpoint A.

### Metrics

- traffic to target endpoint;
- traffic to non-target endpoint;
- target endpoint latency;
- non-target endpoint latency;
- target selectivity:

\[
Selectivity=\frac{\text{requests to target resource}}{\text{requests to all resources}}
\]

### Expected Result

Mobius should concentrate resource consumption on the chosen endpoint, supporting the targetability claim.

## Minimum First Scope

- N values: 1, 2, 4, 8.
- Agent: one Claw-style agent with stable ADD-S or ADD-M payload.
- Server: one local LLM server.
- Profiles: stealth and aggressive.
- Metrics: requests/min, tokens/min, p95 latency, failures, CPU/GPU/memory, amplification factor.

This gives the first scaling curve without needing the full matrix.

## Outputs for Paper

The expected output form of Plan C is a scaling and collateral-damage evidence chain:

1. a scaling curve showing how requests/tokens and latency change with the number of poisoned agents;
2. a saturation-knee figure showing nonlinear service degradation;
3. a benign-collateral-damage figure showing that normal agents are harmed under poisoned-agent load;
4. an optional defense-under-pressure table reused later by the defense section.

### Table C1: Multi-Zombie Scaling

Columns:

- N;
- profile;
- requests/min;
- tokens/min;
- p95 latency;
- p99 latency;
- failed requests;
- CPU/GPU/memory;
- amplification factor.

Suggested schema:

```text
N | Profile | Req/min | Tok/min | p95 Lat | p99 Lat | Fail Rate | CPU/GPU/Mem | AF_req | AF_tok
1 | stealth | ...     | ...     | ...     | ...     | ...       | ...         | ...    | ...
4 | stealth | ...     | ...     | ...     | ...     | ...       | ...         | ...    | ...
8 | aggressive | ...  | ...     | ...     | ...     | ...       | ...         | ...    | ...
```

### Figure C1: Scaling Curve

Plot N vs requests/min, tokens/min, p95 latency, and failed request rate.

Expected visual pattern:

- requests/min and tokens/min grow approximately linearly at small N;
- p95/p99 latency and failure rate show a nonlinear knee as the local LLM server saturates.

### Figure C2: Saturation Knee

Plot server p95/p99 latency and failed request rate over time for increasing N.

### Figure C3: Benign Collateral Damage

Plot benign task latency/completion under benign-only vs benign-plus-poisoned runs.

Recommended y-axes:

- benign task completion rate;
- benign task wall-clock latency;
- benign LLM request p95 latency;
- benign failed request rate.

### Table C2: Defense Under Multi-Zombie Pressure

Columns:

- defense;
- N;
- profile;
- residual P-ASR;
- residual T-ASR;
- residual R-ASR;
- residual tokens;
- p95 latency;
- TTD;
- FPR;
- TSR drop.

### Main Finding Statement

Plan C should support the following paper finding:

> Multiple Mobius-infected agents scale into measurable local service degradation and collateral damage to benign agent workloads, even though each request remains a valid victim-originated LLM/API request.

## Safety and Isolation

- Use only local services.
- Use isolated Docker networks.
- Stop experiments at predefined saturation or safety limits.
- Avoid public API keys and external endpoints.
- Persist logs for auditability.
- Clearly state in the paper that the experiment evaluates local resource amplification and scaling, not a real-world attack on third-party infrastructure.
