# Mobius Injection 

Mobius Injection contains the experiment harness, payload templates, local
service tooling, analysis utilities, tests, and artifact layout for reproducing
the Mobius Injection and agent-oriented denial-of-service experiments.

Publication link: [arXiv:2605.11442](https://arxiv.org/abs/2605.11442)
([DOI](https://doi.org/10.48550/arXiv.2605.11442))


## Safety Boundary

This is a controlled security-research repository. Run experiments only on
machines, containers, model endpoints, and services that you own or are
explicitly authorized to test.

The resource-pressure experiments are intended for local model servers, local
HTTP services, isolated Docker containers, or recorded-artifact replay. Do not
aim these workloads at public services or third-party infrastructure.

## Repository Layout

```text
.
|-- Env/                         Agent container setup and operations notes
|-- experiments/
|   |-- AgentCallInterface/      Agent callers, benchmark loaders, monitors
|   |-- scripts/                 Main experiment entry-point scripts
|   |-- results/                 Generated result artifacts, ignored locally
|   |-- logs/                    Runtime logs, ignored locally
|   `-- staging/                 Temporary task and container staging
|-- localserver/                 Local Ollama startup and JSONL proxy logger
|-- mobiusInjection/             Mobius payload and benchmark prompt templates
|-- papers/                      Local manuscript support material
|-- tasks/                       Local session records and planning notes
|-- pyproject.toml               Python project metadata
`-- uv.lock                      Locked Python dependencies
```

## Reproduction Modes

Use the lightest mode that answers your question.

1. Verify the harness and replay existing artifacts.

   This checks the code, metric extraction, and plotting or aggregation scripts
   without rerunning active agent workloads.

2. Rerun selected local experiments.

   This covers local Ollama-backed experiments, queueing controls, local
   network-feature exports, and isolated Docker runs.

3. Rerun the full experiment matrix.

   This requires the agent CLIs, provider credentials, Docker images, benchmark
   datasets, local model services, and enough time to tolerate stochastic agent
   behavior.

## Requirements

The project uses `uv` for Python environment management.

Original experiment platform:

```text
OS: Ubuntu 22.04
Container runtime: Docker 29.1.3
Local model service: Ollama 0.16.1
Python: 3.10 or newer, tested mostly with Python 3.12
GPU: H100 NVL class hardware for the largest local-model runs
```

Install dependencies:

```bash
uv sync --dev
```

Use the lockfile exactly:

```bash
uv sync --dev --frozen
```

## Credentials

Do not commit credentials. The code reads provider keys from environment
variables or local `privacy_secret_*` files.

OpenRouter:

```bash
export OPENROUTER_API_KEY="..."
```

or:

```bash
printf '%s\n' "..." > privacy_secret_openrouter_API_key.txt
```

AiGoCode:

```bash
export AIGOCODE_API_KEY="..."
export AIGOCODE_BASE_URL="https://api.aigocode.com"
```

Optional provider-specific AiGoCode keys:

```bash
export AIGOCODE_ANTHROPIC_API_KEY="..."
export AIGOCODE_OPENAI_API_KEY="..."
export AIGOCODE_GEMINI_API_KEY="..."
```

The credential reader lives at:

```text
experiments/AgentCallInterface/utils/api_keys.py
```

## Agent Containers

Container setup scripts and operating notes are in:

```text
Env/
Env/setup/
```

Start by reading:

```text
Env/agent_containers_usage.md
Env/agent_api_configuration.md
Env/docker_secrets_guide.md
```

The setup scripts are split by agent:

```text
Env/setup/01_claude_code.sh
Env/setup/02_openclaw.sh
Env/setup/03_opencode.sh
Env/setup/05_kilo_code.sh
Env/setup/07_zeroclaw.sh
Env/setup/08_hermes.sh
```

Run setup only after confirming credentials, Docker permissions, and local
resource limits.

## Local Ollama and Proxy Logging

Several experiments use a local Ollama endpoint and a proxy that records one
JSON object per request.

Start Ollama:

```bash
./start_ollama.sh
```

Default local service details:

```text
Ollama host: 127.0.0.1:11435
Proxy example host: 127.0.0.1:11436
```

Run the proxy:

```bash
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost \
  uv run python localserver/ollama_proxy_logger.py \
  --host 127.0.0.1 \
  --port 11436 \
  --upstream http://127.0.0.1:11435 \
  --log-path experiments/logs/ddos_plan_a/ollama_proxy.jsonl
```

If the shell has `http_proxy`, `https_proxy`, or `all_proxy` set, keep
`NO_PROXY` and `no_proxy` configured for localhost.

## Quick Verification

Run a focused test subset before changing experiment code:

```bash
uv run pytest \
  experiments/AgentCallInterface/tests/test_agent_callers.py \
  experiments/AgentCallInterface/tests/test_dataset_loaders.py \
  experiments/AgentCallInterface/tests/test_mobius_monitor.py \
  experiments/AgentCallInterface/tests/test_prompt_composer.py
```

Run broader harness tests:

```bash
uv run pytest experiments/AgentCallInterface/tests
```

Some tests require Docker, local model services, external agent CLIs, benchmark
data, or provider credentials. When a test fails because an external service is
unavailable, fix the environment first.

## Experiment Families

The sections below describe the main experiment families and the repo-local
commands or files needed to reproduce them.

### Claw-Style Agent Effectiveness

Purpose: evaluate Mobius injection on claw-style agents and ClawBench tasks
across ADD and EDIT grafting strategies.

Core source directories:

```text
mobiusInjection/
experiments/AgentCallInterface/
experiments/scripts/
```

Representative entry points:

```text
experiments/scripts/effectiveness_clean_claw_0.1.0.baseline_tsr.py
experiments/scripts/effectivenss_injection_claw_0.2.context_injection_add_s.sh
experiments/scripts/effectiveness_injection_claw_0.2.5.context_injection_add_m_claw_agents.py
experiments/scripts/effectiveness_injection_claw_0.2.6.context_injection_edit_m_claw_agents.py
experiments/scripts/effectiveness_injection_claw_0.2.7.context_injection_add_c_batch.sh
experiments/scripts/effectiveness_injection_claw_0.2.8.context_injection_edit_c_batch.sh
```

Representative command:

```bash
bash experiments/scripts/effectivenss_injection_claw_0.2.context_injection_add_s.sh
```

Expected generated artifact root:

```text
agentcodingdos_context_injection_runs/
```

Typical subdirectories:

```text
container_exports/
logs/
manifests/
staging/
verifier_results/
```

This artifact root is ignored by git.

### Coding-Agent Benchmark Effectiveness

Purpose: evaluate coding agents on HumanEval and SWE-bench style tasks under
clean and injected conditions.

Harness modules:

```text
experiments/AgentCallInterface/coding_agents/
experiments/AgentCallInterface/coding_datasets/
experiments/AgentCallInterface/coding_evaluation/
```

Representative entry points:

```text
experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh
experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh
experiments/scripts/1.0.1.run_minimax_coding_agents_full_eval.sh
experiments/scripts/1.0.2.run_minimax_humaneval_injection_benchmark.sh
experiments/scripts/1.0.3.run_free_models_humaneval_injection_benchmark.sh
experiments/scripts/analyze_humaneval_minimax_logs.py
experiments/scripts/analyze_paper_metrics.py
```

Representative command:

```bash
bash experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh
```

Relevant tests:

```bash
uv run pytest \
  experiments/AgentCallInterface/tests/test_coding_eval_script.py \
  experiments/AgentCallInterface/tests/test_humaneval_benchmark_script.py \
  experiments/AgentCallInterface/tests/test_opencode_formal_dryrun.py \
  experiments/AgentCallInterface/tests/test_opencode_formal_results_aggregate.py
```

### Targeted Mobius Cross-Evaluation

Purpose: evaluate whether targeted payloads activate only in matching
environment profiles.

Entry points:

```text
experiments/scripts/targeted_mobius_0.0.1.build_env_images.sh
experiments/scripts/targeted_mobius_0.0.1.run_4x4_smoke.py
experiments/scripts/targeted_mobius_0.1.0.run_4x4_batch.py
experiments/scripts/targeted_mobius_0.1.0.plot_4x4_matrix.py
experiments/scripts/targeted_mobius_0.2.0.probe_then_full.sh
```

Representative command:

```bash
bash experiments/scripts/targeted_mobius_0.2.0.probe_then_full.sh
```

Expected generated artifact root:

```text
agentcodingdos_targeted_runs/
```

The batch outputs include logs and `targeted_results.jsonl` files used by the
targeted-matrix analysis.

### Single-Node Local Resource Amplification

Purpose: compare clean and poisoned single-agent local-model runs by completed
LLM calls and token consumption.

Main result directories:

```text
experiments/results/opencode_datadog_fileedit_ollama_20260503/
experiments/results/multiagent_datadog_fileedit_ollama_20260504/
experiments/results/opencode_datadog_fileedit_ollama_model_sweep_20260504/
experiments/results/multiagent_datadog_fileedit_ollama_gpt_oss_20260505/
```

Representative run and test commands:

```bash
uv run python experiments/results/opencode_datadog_fileedit_ollama_20260503/run_datadog_fileedit_ollama.py
uv run pytest experiments/results/opencode_datadog_fileedit_ollama_20260503/test_datadog_fileedit_ollama.py
uv run pytest experiments/results/multiagent_datadog_fileedit_ollama_20260504/test_multiagent_datadog_fileedit_ollama.py
```

Model-sweep plot and regression check:

```bash
uv run python experiments/results/opencode_datadog_fileedit_ollama_model_sweep_20260504/plot_model_sweep.py
uv run pytest experiments/results/opencode_datadog_fileedit_ollama_model_sweep_20260504/test_plot_model_sweep.py
```

The proxy logs and summary CSVs must refer to the same run windows. If you rerun
raw experiments, regenerate summaries before comparing curves.

### Multi-Node Queue Externality

Purpose: measure collateral latency when multiple poisoned OpenCode containers
share one local backend with a benign probe stream.

Result directory:

```text
experiments/results/opencode_queue_externality_20260504/
```

Important files:

```text
run_opencode_queue_externality.py
plot_opencode_queue_externality.py
build_defense_under_pressure.py
summary.csv
probe_latency.csv
defense_under_pressure.csv
```

Commands:

```bash
uv run python experiments/results/opencode_queue_externality_20260504/run_opencode_queue_externality.py
uv run pytest experiments/results/opencode_queue_externality_20260504 -q
uv run --with matplotlib python experiments/results/opencode_queue_externality_20260504/plot_opencode_queue_externality.py
uv run python experiments/results/opencode_queue_externality_20260504/build_defense_under_pressure.py
```

The standard queue experiment uses poisoned-node counts `0,1,2,4`.

### Multi-Zombie Scaling

Purpose: measure local model pressure under multiple clean or poisoned nodes.

Result directory:

```text
experiments/results/opencode_multizombie_scaling_20260504/
```

Commands:

```bash
uv run python experiments/results/opencode_multizombie_scaling_20260504/run_opencode_multizombie_scaling.py
uv run pytest experiments/results/opencode_multizombie_scaling_20260504 -q
uv run --with matplotlib python experiments/results/opencode_multizombie_scaling_20260504/plot_opencode_multizombie_scaling.py
```

### Other AI Infrastructure Workload

Purpose: test whether recursive agent calls can pressure non-LLM local
infrastructure such as tool, marketplace, or retrieval services.

Result directory:

```text
experiments/results/other_ai_infra_workload_20260507/
```

Commands:

```bash
uv run python experiments/results/other_ai_infra_workload_20260507/run_other_ai_infra_workload.py
uv run pytest experiments/results/other_ai_infra_workload_20260507/test_other_ai_infra_workload.py
```

### Network-Layer Stealth and Detector Mismatch

Purpose: compare Mobius traffic with conventional local HTTP and TCP pressure
using flow features and detector outcomes.

Entry points:

```text
experiments/scripts/plan_b_ids_pcap_experiment.py
experiments/scripts/plan_b_network_stealth_export.py
```

Commands:

```bash
uv run python experiments/scripts/plan_b_ids_pcap_experiment.py
uv run python experiments/scripts/plan_b_network_stealth_export.py
uv run pytest experiments/AgentCallInterface/tests/test_plan_b_network_stealth_export.py
```

Use PCAP capture, Zeek, and Suricata only against loopback or owned local test
services.

### Monitoring and Activation Comparisons

Purpose: reproduce smaller follow-up studies for activation, trace monitoring,
manual poisoned loops, and time-window effects.

Useful entry points:

```text
experiments/results/opencode_manual_poison_loop_20260503/run_manual_poison_loop.py
experiments/results/opencode_manual_poison_loop_20260503/run_consistency_continuous_v5.py
experiments/results/opencode_monitoring_time_curve_20260503/run_monitoring_time_curve.py
experiments/results/opencode_time_window_free_run_20260503/run_time_window_free_run.py
experiments/results/opencode_time_window_free_run_20260503/build_cumulative_curve.py
experiments/results/plan_a_codeagent_clean_pristine_vs_poisoned_activation_20260503/run_activation_comparison.py
```

Run these from the repository root with `uv run python <script>`.

## Result Aggregation and Metrics

Core metric and analysis modules:

```text
experiments/AgentCallInterface/evaluation/benchmark_analysis.py
experiments/AgentCallInterface/evaluation/benchmark_manifest.py
experiments/AgentCallInterface/evaluation/mobius_monitor.py
experiments/AgentCallInterface/evaluation/paper_metrics.py
experiments/AgentCallInterface/coding_evaluation/opencode_formal_results_aggregate.py
experiments/AgentCallInterface/coding_evaluation/opencode_recursive_trace_monitor.py
```

Common metrics:

```text
TSR     Task success rate
P-ASR   Pollution attack success rate
T-ASR   Trigger attack success rate
R-ASR   Recursive attack success rate
#C      Component or LLM call count, depending on context
```

When rerunning stochastic agent experiments, compare fresh runs against the
recorded artifacts only after confirming that model IDs, agent versions,
timeouts, prompts, and container images match.

## Generated Artifacts and Git Hygiene

Large or local generated artifacts are intentionally ignored. Important ignored
paths include:

```text
agentcodingdos_context_injection_runs/
agentcodingdos_targeted_runs/
experiments/results/
experiments/logs/
experiments/AgentCallInterface/coding_datasets/swebench_data/
```

Before committing:

```bash
git status --short
```

Do not commit provider secrets, local logs, Docker exports, model outputs, or
large benchmark data copies. Commit source code, scripts, tests, small fixtures,
and small configuration files needed for reproducibility.

## Common Problems

Missing provider keys.

Set the appropriate environment variable or create the matching
`privacy_secret_*` file in the repository root.

Local Ollama calls fail through a proxy.

Set both proxy bypass variables:

```bash
export NO_PROXY=127.0.0.1,localhost
export no_proxy=127.0.0.1,localhost
```

Docker image scripts fail.

Check Docker permissions, available disk space, and the agent setup notes in
`Env/`. Confirm that any required base images exist before running batch
scripts.

Recorded-artifact tests fail after a rerun.

Some tests encode the counts and endpoints from a specific recorded artifact
snapshot. If you intentionally regenerate the underlying artifacts, update the
summary CSVs, plots, and regression expectations together.

Full reruns produce different counts.

Agent behavior depends on model versions, provider behavior, timeouts,
container state, and stochastic decoding. Treat full reruns as new
measurements, not as byte-for-byte regeneration.


## Citation

If you use this repository, please cite:

```bibtex
@misc{liang2026singlemessageparalyzeai,
  title = {Can a Single Message Paralyze the AI Infrastructure? The Rise of AbO-DDoS Attacks through Targeted Mobius Injection},
  author = {Liang, Zi and Li, Ronghua and Wang, Yanyun and Ye, Qingqing and Hu, Haibo},
  year = {2026},
  eprint = {2605.11442},
  archivePrefix = {arXiv},
  primaryClass = {cs.CR},
  doi = {10.48550/arXiv.2605.11442},
  url = {https://arxiv.org/abs/2605.11442}
}
```
