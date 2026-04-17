# AgentCallInterface Code Review - Issues Found

**Date:** 2026-04-17
**Reviewer:** AI Assistant
**Directory:** `~/AgentCodingDos/experiments/AgentCallInterface/`

---

## Issue 1: Import Path Errors (CRITICAL)

**Files Affected:**
- `experiments/AgentCallInterface/transformers/agent_transformers.py:15-16`
- `experiments/AgentCallInterface/tests/test_dataset_loaders.py:8,12`
- `experiments/AgentCallInterface/tests/test_transformers.py:10,17-18`

**Problem:** Imports use `from experiments.datasets...` but should be `from experiments.AgentCallInterface.datasets...`

**Current (Broken):**
```python
from experiments.datasets.clawbench_loader import ClawBenchTask
from experiments.datasets.coding_benchmark_loader import CodingTask
```

**Expected (Correct):**
```python
from experiments.AgentCallInterface.datasets.clawbench_loader import ClawBenchTask
from experiments.AgentCallInterface.datasets.coding_benchmark_loader import CodingTask
```

**Status:** ✅ FIXED - 2026-04-17

---

## Issue 2: HumanEvalLoader.load_tasks() Not Implemented

**File:** `experiments/AgentCallInterface/datasets/coding_benchmark_loader.py:128`

**Problem:** The `HumanEvalLoader` class lacks a `load_tasks()` method, but `CodingBenchmarkLoader` attempts to call it at line 137-138.

**Status:** ✅ FIXED - 2026-04-17 (Implemented load_tasks with _download_dataset and _parse_humaneval)

---

## Issue 3: HumanEvalLoader Has Wrong Dataset URL

**File:** `experiments/AgentCallInterface/datasets/coding_benchmark_loader.py:119`

**Problem:** The URL points to GSM8K (math dataset) instead of HumanEval.

**Status:** ✅ FIXED - 2026-04-17 (Changed to correct HumanEval URL)

---

## Issue 4: Agent CLI Usage Does Not Align with Official APIs

### 4.0 Claw-Style Agents (OpenClaw, ZeroClaw, Nanobot, Hermes) - ✅ ALL FIXED

**Files:** `experiments/AgentCallInterface/agents/agent_callers.py`

**Summary:** All claw-style agents had incorrect calling formats. Verified and fixed on 2026-04-17.

| Agent | Container Binary Path | Correct Non-Interactive Command |
|-------|----------------------|--------------------------------|
| OpenClaw | `openclaw` (in PATH) | `openclaw chat -m "prompt"` |
| ZeroClaw | `/home/linuxbrew/.linuxbrew/Cellar/zeroclaw/0.6.9/bin/zeroclaw` | `zeroclaw agent -m "prompt"` |
| Nanobot | `nanobot` (in PATH after uv install) | `nanobot agent -m "prompt"` |
| Hermes | `source ~/.local/bin/env && hermes` | `hermes chat -q "prompt"` |

**Key Findings:**
- OpenClaw: Uses `openclaw chat -m "prompt"` (NOT `execute`)
- ZeroClaw: Uses `zeroclaw agent -m "prompt"` (NOT `run`)
- Nanobot: Uses `nanobot agent -m "prompt"` (NOT `execute --task`)
- Hermes: Uses `hermes chat -q "prompt"` (NOT `run --skill`)

**Status:** ✅ ALL FIXED - 2026-04-17

---

### 4.1 Claude Code - ✅ CORRECT

**File:** `experiments/AgentCallInterface/agents/agent_callers.py:198-245`

**Verification:** `claude -p "prompt"` is the official non-interactive/prompt mode for Claude Code.

**Status:** ✅ CORRECT

---

### 4.2 OpenAI Codex CLI - ✅ FIXED

**File:** `experiments/AgentCallInterface/agents/agent_callers.py:361-395`

**Problem:** Uses `codex --task` which does NOT exist. The correct non-interactive mode is `codex exec PROMPT`.

**Official Usage (from GitHub README):**
```bash
# Interactive mode
codex

# Non-interactive mode
codex exec "your prompt here"

# Full auto mode
codex exec --full-auto "your prompt here"
```

**Previous (INCORRECT):**
```python
cmd = [
    "npx",
    "@openai/codex@0.57.0",
    "--task",
    task_input.get("task_id", ""),
]
```

**Current (CORRECT):**
```python
prompt = task_input.get("problem_statement", task_input.get("task_id", ""))
cmd = [
    "docker",
    "run",
    "--rm",
    "-e",
    f"CODEX_PROMPT={prompt}",
    "codex:latest",
    "exec",
    "--full-auto",
    prompt,
]
```

**Status:** ✅ FIXED - 2026-04-17

---

### 4.3 Cursor - ❌ NO AUTONOMOUS CLI MODE

**File:** `experiments/AgentCallInterface/agents/agent_callers.py:248-283`

**Problem:** Cursor is an IDE/editor (VS Code fork) with GUI-based AI features (Ctrl+K, Ctrl+L). It does NOT have an autonomous CLI mode for task execution.

**Verification:** All Cursor documentation shows GUI interaction patterns only. No `--task` flag or headless mode exists.

**Current (INCORRECT):**
```python
cmd = [
    "cursor",
    "--task",
    task_input.get("task_id", ""),
    "--repo",
    task_input.get("repo", ""),
]
```

**Status:** ❌ CANNOT FIX - Cursor does not support autonomous CLI execution

---

### 4.4 OpenCode (SST) - ✅ FIXED

**File:** `experiments/AgentCallInterface/agents/agent_callers.py:286-321`

**Note:** This is SST's OpenCode (https://github.com/sst/opencode), NOT OpenAI Codex.

**Official Usage:**
```bash
opencode run "prompt"  # Non-interactive mode
opencode              # Interactive TUI mode
```

**Previous (INCORRECT):**
```python
cmd = [
    "opencode",
    "--task",
    task_input.get("task_id", ""),
    "--repo",
    task_input.get("repo", ""),
]
```

**Current (CORRECT):**
```python
prompt = task_input.get("problem_statement", task_input.get("task_id", ""))
cmd = [
    "opencode",
    "run",
    prompt,
]
```

**Status:** ✅ FIXED - 2026-04-17

---

### 4.5 KiloCode - ✅ FIXED

**File:** `experiments/AgentCallInterface/agents/agent_callers.py:324-358`

**Verification:** The package `@kilocode/cli` exists on npm. The binary is `kilo` (not `kilocode`).

**Official Usage:**
```bash
kilo run "prompt"        # Non-interactive mode
kilo exec "prompt"       # Non-interactive mode (alias)
kilo                     # Interactive TUI mode
```

**Previous (INCORRECT):**
```python
cmd = [
    "npx",
    "@kilocode/cli",
    "--task",
    task_input.get("task_id", ""),
]
```

**Current (CORRECT):**
```python
prompt = task_input.get("problem_statement", task_input.get("task_id", ""))
cmd = [
    "docker",
    "run",
    "--rm",
    "-e",
    f"KILO_PROMPT={prompt}",
    "kilo_code:latest",
    "run",
    prompt,
]
```

**Status:** ✅ FIXED - 2026-04-17

---

### 4.6 Droid (Factory.ai) - ✅ FIXED

**File:** `experiments/AgentCallInterface/agents/agent_callers.py:398-441`

**Verification:** Factory.ai Droid uses `droid exec "prompt"` for non-interactive mode.

**Official Usage:**
```bash
droid exec "prompt"     # Non-interactive mode
droid                   # Interactive REPL mode
```

**Previous (INCORRECT):**
```python
cmd = [
    "curl",
    "-fsSL",
    "https://app.factory.ai/cli",
    "|",
    "sh",
    "-s",
    "--",
    "task",
    task_input.get("task_id", ""),
]
```

**Current (CORRECT):**
```python
prompt = task_input.get("problem_statement", task_input.get("task_id", ""))
cmd = [
    "docker",
    "run",
    "--rm",
    "-e",
    f"DROID_PROMPT={prompt}",
    "droid:latest",
    "exec",
    prompt,
]
```

**Status:** ✅ FIXED - 2026-04-17

---

### 4.7 Zed - ❌ NO AUTONOMOUS CLI MODE

**File:** `experiments/AgentCallInterface/agents/agent_callers.py:444-477`

**Problem:** Zed is a code editor with AI features integrated into its GUI. It does NOT have a `--task` argument or autonomous CLI mode.

**Verification:** Zed AI is accessed through the editor's AI panel, not via CLI.

**Status:** ❌ CANNOT FIX - Zed does not support autonomous CLI execution

---

## Issue 5: ClawBenchLoader Works (Positive Finding)

**File:** `experiments/AgentCallInterface/datasets/clawbench_loader.py`

**Status:** ✅ USABLE

The ClawBench loader is properly implemented:
- Clones from `https://github.com/claw-bench/claw-bench.git`
- Parses JSON tasks correctly
- `get_quick_test_tasks()` provides 20 test cases
- `to_agent_input()` generates proper input format

---

## Testing Commands Used

```bash
# Test import paths
cd /home/zi/AgentCodingDos && uv run python -c "
import sys
sys.path.insert(0, '.')
from experiments.AgentCallInterface.datasets.clawbench_loader import ClawBenchLoader
loader = ClawBenchLoader()
print('ClawBenchLoader initialized successfully')
"

# Test HumanEvalLoader.load_tasks
uv run python -c "
from experiments.AgentCallInterface.datasets.coding_benchmark_loader import HumanEvalLoader
loader = HumanEvalLoader()
print(f'Has load_tasks: {hasattr(loader, \"load_tasks\")}')
"
```

---

---

## Issue 6: Missing MCP Modules

**Files Affected:**
- `experiments/AgentCallInterface/tests/test_mcp_recursive.py`
- `experiments/AgentCallInterface/tests/simulate_agent.py`

**Problem:** These test files import from `experiments.mcp.mcp_recursive` and `experiments.mcp.mcp_minimal`, but the `mcp` module does not exist in the codebase.

**Status:** ✅ RESOLVED - 2026-04-17
- Moved to `PastSourceCodeWhichIsOnlyForReference/AgentCallInterface_broken_tests/`
- User confirmed these outdated security tests are no longer needed

---

## Issue 7: SWE-bench Dataset URL Not Accessible

**File:** `experiments/AgentCallInterface/datasets/coding_benchmark_loader.py:51`

**Problem:** The HuggingFace URL for "swebench_verified_mini" does not exist.

**Status:** ✅ FIXED - 2026-04-17
- Found correct dataset: `SWE-bench/SWE-bench_Lite` on HuggingFace
- Downloaded 300 instances to `experiments/AgentCallInterface/datasets/swebench_data/swe-bench_lite.json`
- Dataset URL: `datasets.load_dataset('SWE-bench/SWE-bench_Lite', split='test')`

---

## Issue 8: ClawBench Tasks Use TOML Not JSON

**File:** `experiments/AgentCallInterface/datasets/clawbench_loader.py:85`

**Problem:** The loader looks for `.json` files but ClawBench tasks are stored as `.toml` files.

**Status:** ✅ FIXED - 2026-04-17
- Updated to use `tomllib`/`tomli` for TOML parsing
- Changed to `rglob("task.toml")` to find all task files
- Loaded 319 ClawBench tasks successfully

---

## Recommendations

1. ✅ ~~Fix import paths~~ - FIXED
2. ✅ ~~Implement `load_tasks()`~~ - FIXED
3. ✅ ~~Fix HumanEvalLoader URL~~ - FIXED
4. ✅ ~~Fix ClawBench TOML parsing~~ - FIXED
5. ✅ ~~SWE-bench URL~~ - FIXED (downloaded Lite dataset)
6. ✅ ~~MCP modules~~ - RESOLVED (moved to reference folder)
7. ✅ ~~Update CodexCaller~~ - FIXED (changed from `codex --task` to `codex exec`)
8. ✅ ~~Verify OpenCode (SST)~~ - FIXED (changed to `opencode run "prompt"`)
9. ✅ ~~Verify KiloCode~~ - FIXED (changed to `kilo run "prompt"`)
10. ✅ ~~Verify Droid~~ - FIXED (changed to `droid exec "prompt"`)
11. ✅ ~~Fix Claw-Style Agents~~ - FIXED (OpenClaw, ZeroClaw, Nanobot, Hermes all corrected)
12. **Cursor** - Cannot fix (no autonomous CLI mode - GUI-based IDE)
13. **Zed** - Cannot fix (no autonomous CLI mode - GUI-based editor)
14. **API Key Configuration** - Agents need proper API key configuration to execute tasks
15. **Add integration tests** - Test each agent with actual task execution after API key setup
