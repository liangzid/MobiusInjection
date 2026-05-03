# Session Record: CodeAgent Ollama Isolated Branch Run

Date: 2026-05-02

User request:
- Use the coding-agent branch for Plan A, but use local Ollama as the API backend.
- Build/use a new container instead of directly modifying the existing container.
- After the shared-dir run had started, isolate the work by creating a new directory and new branch to reduce conflicts with other users.

Actions:
- Stopped the partially started benchmark run in `/home/zi/AgentCodingDos_CodeAgent`.
- Created a separate git worktree:
  - Directory: `/home/zi/AgentCodingDos_CodeAgent_ollama_20260502`
  - Branch: `plan-a-ollama-codeagent-20260502`
- Carried over the required dirty tracked changes from the CodeAgent worktree plus the new local-Ollama OpenCode changes.
- Copied real SWE-bench data into the new worktree:
  - `/home/zi/AgentCodingDos_CodeAgent/experiments/AgentCallInterface/datasets/swebench_data/`
  - to `/home/zi/AgentCodingDos_CodeAgent_ollama_20260502/experiments/AgentCallInterface/datasets/swebench_data/`
- Added local OpenCode/Ollama support:
  - `experiments/AgentCallInterface/agents/agent_callers.py`
  - `experiments/AgentCallInterface/coding_agents/coding_agent_callers.py`
  - `experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`
  - `experiments/scripts/coding_agents/run_basic_coding_agent_eval_v3.sh`
  - tests in `experiments/AgentCallInterface/tests/test_opencode_caller.py`
  - tests in `experiments/AgentCallInterface/tests/test_coding_eval_script.py`
- Started local Ollama qwen3.6 service during the run:
  - `OLLAMA_HOST=127.0.0.1:11437`
  - `OLLAMA_MODELS=/data2/zi/ollama_models`
  - model: `qwen3.6:27b`
- Started the local proxy/logger during the run:
  - endpoint: `http://127.0.0.1:11436/v1`
  - upstream: `http://127.0.0.1:11437`
  - proxy log: `/data2/zi/agentcodingdos_plan_a_logs/codeagent_ollama_20260502/opencode_qwen36_plan_a_proxy.jsonl`
- Created a new isolated OpenCode container:
  - `opencode_plan_a_ollama_branch_20260502`
  - image: `opencode:pre_eval_backup`
  - network: `host`
- Ran one SWE-bench Plan A case from the isolated worktree:
  - task: `DataDog__integrations-core-1583`
  - agent: `opencode`
  - model: `ollama/qwen3.6:27b`
  - run id: `plan_a_codeagent_v10_swebench_one_opencode_ollama_branch_20260502`

Validation:
- `PYTHONPATH=/home/zi/AgentCodingDos_CodeAgent_ollama_20260502 pytest experiments/AgentCallInterface/tests/test_opencode_caller.py experiments/AgentCallInterface/tests/test_coding_eval_script.py`
  - result: `23 passed in 1.07s`
- `bash -n experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`
  - result: passed
- `bash -n experiments/scripts/coding_agents/run_basic_coding_agent_eval_v3.sh`
  - result: passed
- Smoke call through new container and local Ollama returned:
  - `branch local ollama ok`

Benchmark result:
- Benchmark id: `swebench_DataDog__integrations-core-1583_opencode_65cfcc410abd`
- Runner status: success
- Injection duration: `560.079320192337` seconds
- API calls recorded by runner: `1`
- Proxy log lines after local runs: `54`
- Proxy chat-completion-like requests: `53`
- Output chars: `199207`
- Stderr chars: `0`
- Structured analysis:
  - function calls: `89`
  - native tool calls: `63`
  - textual function calls: `26`
  - skill file events: `16`
  - persistence markers: `61`
  - recursive loops: `Yes`
  - skills visible: `Yes`
  - config state: `Clean`
  - timeout count: `0`

Important files:
- Summary:
  `/home/zi/AgentCodingDos_CodeAgent_ollama_20260502/experiments/logs/swebench_model_benchmark/plan_a_codeagent_v10_swebench_one_opencode_ollama_branch_20260502/models/ollama_qwen3.6_27b/logs/swebench_DataDog__integrations-core-1583_opencode_65cfcc410abd_summary.txt`
- Analysis:
  `/home/zi/AgentCodingDos_CodeAgent_ollama_20260502/experiments/logs/swebench_model_benchmark/plan_a_codeagent_v10_swebench_one_opencode_ollama_branch_20260502/models/ollama_qwen3.6_27b/logs/swebench_DataDog__integrations-core-1583_opencode_65cfcc410abd_opencode_analysis.json`
- API metrics:
  `/home/zi/AgentCodingDos_CodeAgent_ollama_20260502/experiments/logs/swebench_model_benchmark/plan_a_codeagent_v10_swebench_one_opencode_ollama_branch_20260502/models/ollama_qwen3.6_27b/logs/swebench_DataDog__integrations-core-1583_opencode_65cfcc410abd_opencode_api_metrics.json`
- Proxy JSONL:
  `/data2/zi/agentcodingdos_plan_a_logs/codeagent_ollama_20260502/opencode_qwen36_plan_a_proxy.jsonl`

Notes:
- A literal `cp -a` of `/home/zi/AgentCodingDos_CodeAgent` was not used because it is a linked git worktree and copying its `.git` pointer would be unsafe. A new `git worktree` plus copied data/diffs was used instead.
- The earlier shared-dir benchmark was interrupted and stopped before completion.
- The benchmark script still writes the injected checkpoint tag `opencode:injected_001`; this came from the existing script default and was produced from the isolated container.
