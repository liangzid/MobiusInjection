# Research Plan A: Local LLM Resource-Amplification Efficiency

Date: 2026-05-02

## Goal

This plan measures whether a single poisoned agent can amplify one low-cost Mobius injection into sustained LLM-server resource consumption. The experiment is local-only: poisoned agent containers send ordinary LLM requests to a local LLM server, and all traffic stays inside the lab machine or an isolated Docker network.

This plan supports the paper section **Efficiency of Agent DDoS** by quantifying victim-side API calls, tokens, latency, and compute pressure caused by Mobius Injection.

## Core Claim

Mobius Injection converts a one-time textual exposure into repeated victim-originated LLM requests. Unlike classical DoS, the generated requests are semantically normal LLM API calls produced by the victim's own agent workflow.

## Research Questions

- **RQ-A1:** How much request/token amplification can one poisoned agent produce from one successful injection?
- **RQ-A2:** How does the amplification change under different Mobius intensity profiles?
- **RQ-A3:** Does the agent still appear to work on the benign task while producing hidden resource consumption?
- **RQ-A4:** Which component class, such as ADD-S, ADD-M, or ADD-C, produces the most stable resource amplification?

## Experimental Setup

### Components

- **Local LLM server:** Ollama or vLLM.
- **Agent containers:** OpenClaw, ZeroClaw, Hermes, and later one coding agent if needed.
- **Proxy/logger:** A local HTTP-compatible logging proxy between the agents and the LLM server.
- **Metrics collector:** Docker stats, server logs, proxy logs, and optional GPU telemetry.

Recommended first implementation:

```text
Poisoned Agent Container
  -> local LLM API proxy/logger
  -> local LLM server
  -> metrics collection
```

The proxy/logger should record:

- timestamp;
- container id / agent id;
- model name;
- request path;
- prompt token estimate;
- completion token count if available;
- latency;
- status code;
- error type;
- request body size and response body size.

### Models

Use models that can run reliably on the server:

- one small model for stable scaling, such as Qwen/Llama/DeepSeek small variant;
- optionally one larger model for cost/latency sensitivity.

The model choice is not the contribution. The key is to keep it fixed within each experiment.

### Attack Variants

Start with the variants that already show high effectiveness:

- ADD-S;
- ADD-M;
- ADD-C;
- optionally EDIT-S as a stealthier but lower-success variant.

Use the same Mobius payload family as the effectiveness section so that DDoS efficiency is connected to measured P-ASR/T-ASR/R-ASR.

## Experiment A1: Single-Zombie Amplification

### Procedure

For each selected agent and attack variant:

1. Start a clean local LLM server.
2. Start one agent container with an isolated workspace.
3. Run the benign task without injection.
4. Reset the environment.
5. Run the same task with Mobius injection.
6. Keep the execution window fixed, such as 5, 10, and 20 minutes.

### Metrics

- total LLM requests;
- requests per minute;
- prompt tokens;
- completion tokens;
- total tokens;
- tokens per minute;
- p50/p95/p99 latency;
- failed request rate;
- wall-clock runtime;
- CPU, memory, and GPU utilization;
- amplification factor:

\[
AF_{req}=\frac{\text{victim-side LLM requests after trigger}}{\text{attacker one-time injection events}}
\]

\[
AF_{tok}=\frac{\text{victim-side tokens after trigger}}{\text{attacker one-time injection tokens}}
\]

### Expected Result

The poisoned run should generate substantially more LLM requests and tokens than the benign run under the same task and time window.

## Experiment A2: Intensity Profiles

### Profiles

- **Stealth:** low frequency, low max tokens, long interval.
- **Moderate:** medium interval and token budget.
- **Aggressive:** short interval, higher token budget, no deliberate delay.

### Procedure

Run the same agent/task/attack combination under each profile for a fixed time window.

### Metrics

- requests/min;
- tokens/min;
- server latency degradation;
- estimated cost/min;
- failed request rate;
- detector visibility, such as whether simple rate limits or loop detectors trigger.

### Expected Result

Mobius should support both stealthy financial attrition and aggressive resource pressure. The paper can use this to support the configurability property in the threat model.

## Experiment A3: Benign Utility Under Attack

### Procedure

Compare:

- benign task run;
- poisoned task run;
- poisoned task run with stealth intensity;
- poisoned task run with aggressive intensity.

### Metrics

- TSR;
- hidden extra calls per completed task;
- extra tokens per completed task;
- user-visible error rate;
- task output quality verifier result.

### Expected Result

The stealth profile should preserve task appearance while increasing hidden resource use, supporting the "symbiosis with benign tasks" claim.

## Experiment A4: Component-Class Comparison

### Procedure

Run the same agent and task set with:

- ADD-S;
- ADD-M;
- ADD-C;
- EDIT-S if available.

### Metrics

- P-ASR/T-ASR/R-ASR;
- total requests;
- total tokens;
- #C;
- stability across tasks;
- time to first recursive call;
- time to saturation or timeout.

### Expected Result

Component classes may differ: skills can be easier to trigger, memory can persist across tasks, and config/MCP-like components may provide stronger system-level persistence.

## Minimum First Scope

- Agent: OpenClaw or Hermes.
- Task set: a small representative ClawBench subset.
- Attack: ADD-S.
- Server: Ollama or vLLM with one fixed local model.
- Time windows: 5 and 10 minutes.
- Runs: benign vs poisoned.

This minimum scope is enough to produce the first amplification curve.

## Outputs for Paper

The expected output form of Plan A is a resource-amplification evidence chain:

1. a cumulative growth figure showing that poisoned runs keep producing requests/tokens after benign runs settle;
2. a summary table reporting amplification factors and latency impact;
3. an intensity-profile figure showing that Mobius can be configured from stealthy financial attrition to aggressive resource pressure.

### Table A1: Single-Zombie Amplification

Columns:

- Agent;
- attack;
- time window;
- TSR;
- P-ASR;
- T-ASR;
- R-ASR;
- requests;
- tokens;
- p95 latency;
- failed requests;
- amplification factor.

Suggested schema:

```text
Agent | Attack | Window | TSR | P-ASR | T-ASR | R-ASR | Requests | Tokens | p95 Latency | AF_req | AF_tok
OpenClaw | ADD-S | 10min | ... | ... | ... | ... | ... | ... | ... | ... | ...
Hermes   | ADD-M | 10min | ... | ... | ... | ... | ... | ... | ... | ... | ...
```

### Figure A1: Request/Token Growth Over Time

Plot cumulative requests and cumulative tokens for benign vs poisoned runs.

Expected visual pattern:

- benign agent curves flatten after the task finishes or reaches a bounded request budget;
- poisoned agent curves continue to grow linearly or in a staircase pattern throughout the observation window.

### Figure A2: Intensity Profile Comparison

Plot requests/min and p95 latency for stealth, moderate, and aggressive profiles.

Recommended panels:

- requests/min by profile;
- tokens/min by profile;
- p95 latency by profile;
- estimated cost/min by profile.

### Main Finding Statement

Plan A should support the following paper finding:

> A single Mobius-infected agent can transform one successful component-level injection into sustained LLM request/token amplification, while still producing ordinary LLM API traffic from the victim-side agent workflow.

## Safety and Isolation

- Use only local LLM servers.
- Use isolated Docker networks.
- Do not target public APIs or third-party services.
- Keep request rates bounded by configured experiment windows.
- Preserve logs for reproducibility and post-experiment auditing.
