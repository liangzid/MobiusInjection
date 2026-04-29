from __future__ import annotations

import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PAYLOAD = PROJECT_ROOT / "mobiusInjection/MI_V1_add_m_claw_agents.py"
SCRIPT = (
    PROJECT_ROOT
    / "experiments/scripts/effectiveness_injection_claw_0.0.1.zeroclaw_hermes_add_m_smoke.sh"
)
BATCH_SCRIPT = (
    PROJECT_ROOT
    / "experiments/scripts/effectiveness_injection_claw_0.2.5.context_injection_add_m_claw_agents.py"
)


def _payload_for(agent: str) -> str:
    namespace: dict[str, object] = {}
    exec(PAYLOAD.read_text(encoding="utf-8"), namespace)
    return namespace["MainInjectionTextTargeted"](target_agent=agent, target_model="")


def test_add_m_claw_agents_payload_targets_native_config_paths() -> None:
    zeroclaw = _payload_for("zeroclaw")
    hermes = _payload_for("hermes")

    assert 'CONFIG_DIR="/tmp/mobius_zeroclaw_eval_config/workspace/mobius_mcp_config"' in zeroclaw
    assert 'workspace/mobius_mcp_config' in zeroclaw
    assert 'CONFIG_FILE="$CONFIG_DIR/config.toml"' in zeroclaw
    assert 'cat > "$CONFIG_FILE"' in zeroclaw
    assert "[[mcp.servers]]" in zeroclaw
    assert 'name = "mobius-audit"' in zeroclaw
    assert 'command = "/tmp/node"' in zeroclaw
    assert "hermes mcp add mobius-audit" in hermes
    assert "/tmp/mobius_mcp_minimal.js" in hermes
    assert "MOBIUS_MCP_TRACE" in hermes


def test_add_m_claw_agents_smoke_script_is_valid_bash() -> None:
    result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_add_m_claw_agents_smoke_script_collects_trace_metrics() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert "mobius_mcp_call_tool.js" in script
    assert "/tmp/node /tmp/mobius_mcp_call_tool.js" in script
    assert "continuous_check" in script
    assert "consistency_check" in script
    assert "r_asr" in script
    assert "hermes mcp list" in script
    assert "/tmp/mobius_zeroclaw_eval_config/config.toml" in script
    assert "workspace/mobius_mcp_config/config.toml" in script
    assert "workspace_only = false" in script
    assert "block_high_risk_commands = false" in script


def test_add_m_claw_agents_batch_runner_compiles() -> None:
    result = subprocess.run(["python3", "-m", "py_compile", str(BATCH_SCRIPT)], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr


def test_add_m_claw_agents_batch_runner_uses_trace_metrics() -> None:
    script = BATCH_SCRIPT.read_text(encoding="utf-8")

    assert "--agent" in script
    assert "mobius_mcp_call_tool.js" in script
    assert "loop_closure_observed" in script
    assert "continuous_check" in script
    assert "consistency_check" in script
    assert "batch_metrics.txt" in script
    assert "zeroclaw_workspace_config_caveat" in script
