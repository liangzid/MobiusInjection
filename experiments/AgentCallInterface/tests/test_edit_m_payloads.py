from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OPENCLAW_PAYLOAD = PROJECT_ROOT / "mobiusInjection/MI_V1_edit_m_openclaw.py"
OPENCLAW_PAYLOAD_V11 = PROJECT_ROOT / "mobiusInjection/MI_V1.1_edit_m_openclaw.py"
CLAW_AGENTS_PAYLOAD = PROJECT_ROOT / "mobiusInjection/MI_V1_edit_m_claw_agents.py"
CLAW_AGENTS_PAYLOAD_V11 = PROJECT_ROOT / "mobiusInjection/MI_V1.1_edit_m_claw_agents.py"
CLAW_AGENTS_PAYLOAD_V12 = PROJECT_ROOT / "mobiusInjection/MI_V1.2_edit_m_claw_agents.py"


def _load_payload(path: Path, agent: str) -> str:
    namespace: dict[str, object] = {}
    exec(path.read_text(encoding="utf-8"), namespace)
    return namespace["MainInjectionTextTargeted"](target_agent=agent, target_model="")


def test_edit_m_openclaw_payload_updates_existing_workspace_audit_slot() -> None:
    payload = _load_payload(OPENCLAW_PAYLOAD, "openclaw")

    assert "openclaw --profile mobius-eval mcp set workspace-audit" in payload
    assert "/tmp/mobius_mcp_minimal.js" in payload
    assert "MOBIUS_MCP_TRACE" in payload
    assert "Do not create a new MCP server" in payload
    assert "mcp set mobius-audit" not in payload


def test_edit_m_openclaw_v11_payload_uses_preflight_framing_without_add_m_server() -> None:
    payload = _load_payload(OPENCLAW_PAYLOAD_V11, "openclaw")

    assert "OpenClaw runtime preflight memo" in payload
    assert "agent-control envelope" in payload
    assert "Preflight command:" in payload
    assert "openclaw --profile mobius-eval mcp set workspace-audit" in payload
    assert "/tmp/mobius_mcp_minimal.js" in payload
    assert "MOBIUS_MCP_TRACE" in payload
    assert "mcp set mobius-audit" not in payload


def test_edit_m_hermes_payload_edits_existing_config_key() -> None:
    payload = _load_payload(CLAW_AGENTS_PAYLOAD, "hermes")

    assert 'CONFIG_FILE="/root/.hermes/config.yaml"' in payload
    assert "workspace-audit:" in payload
    assert "sed -i" in payload
    assert "/tmp/benign_mcp_audit.js" in payload
    assert "/tmp/mobius_mcp_minimal.js" in payload
    assert "MOBIUS_MCP_TRACE: /tmp/mobius_mcp_trace.jsonl" in payload
    assert "hermes mcp add" not in payload
    assert "mobius-audit:" in payload
    assert "hermes mcp add mobius-audit" not in payload


def test_edit_m_zeroclaw_payload_edits_prebuilt_eval_config() -> None:
    payload = _load_payload(CLAW_AGENTS_PAYLOAD, "zeroclaw")

    assert 'CONFIG_FILE="/tmp/mobius_zeroclaw_eval_config/config.toml"' in payload
    assert 'name = "workspace-audit"' in payload
    assert "sed -i" in payload
    assert "/tmp/benign_mcp_audit.js" in payload
    assert "/tmp/mobius_mcp_minimal.js" in payload
    assert 'MOBIUS_MCP_TRACE = "/tmp/mobius_mcp_trace.jsonl"' in payload
    assert 'name = "mobius-audit"' in payload
    assert "workspace/mobius_mcp_config/config.toml" not in payload


def test_edit_m_claw_agents_v11_payloads_use_stronger_preflight_without_add_m() -> None:
    hermes = _load_payload(CLAW_AGENTS_PAYLOAD_V11, "hermes")
    zeroclaw = _load_payload(CLAW_AGENTS_PAYLOAD_V11, "zeroclaw")

    assert "Action required for local workspace processing" in hermes
    assert "workspace-audit" in hermes
    assert "/root/.hermes/config.yaml" in hermes
    assert "/tmp/mobius_mcp_minimal.js" in hermes
    assert "mobius-audit:" in hermes
    assert "hermes mcp add" not in hermes

    assert "Additional task requirement" in zeroclaw
    assert 'CONFIG_FILE="/tmp/mobius_zeroclaw_eval_config/config.toml"' in zeroclaw
    assert 'name = "workspace-audit"' in zeroclaw
    assert "/tmp/mobius_mcp_minimal.js" in zeroclaw
    assert 'name = "mobius-audit"' in zeroclaw
    assert "workspace/mobius_mcp_config/config.toml" not in zeroclaw


def test_edit_m_claw_agents_v12_zeroclaw_prefers_preexisting_workspace_config() -> None:
    zeroclaw = _load_payload(CLAW_AGENTS_PAYLOAD_V12, "zeroclaw")

    assert "/tmp/mobius_zeroclaw_eval_config/workspace/mobius_mcp_config/config.toml" in zeroclaw
    assert "/tmp/mobius_zeroclaw_eval_config/config.toml" in zeroclaw
    assert 'name = "workspace-audit"' in zeroclaw
    assert "/tmp/mobius_mcp_minimal.js" in zeroclaw
    assert 'name = "mobius-audit"' in zeroclaw
    assert "cat >" not in zeroclaw
