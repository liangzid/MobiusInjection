from __future__ import annotations

import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    PROJECT_ROOT
    / "experiments/scripts/effectiveness_injection_claw_0.0.1.edit_m_victim_images.sh"
)


def test_edit_m_victim_image_script_is_valid_bash() -> None:
    result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_edit_m_victim_image_script_builds_preconfigured_clean_images() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert "openclaw:edit_m_mcp_victim" in script
    assert "hermes:edit_m_mcp_victim" in script
    assert "zeroclaw:edit_m_mcp_victim" in script
    assert "benign_mcp_audit.js" in script
    assert "workspace-audit" in script
    assert "docker commit" in script
    assert "BENIGN_MCP_TRACE=/tmp/benign_mcp_trace.jsonl" in script
    assert "MOBIUS_MCP_SERVER=/tmp/benign_mcp_audit.js" in script
    assert "audit_status" in script
    assert "continuous_check|consistency_check" in script


def test_edit_m_victim_image_script_uses_existing_mcp_slot_not_mobius_slot() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert "mcp set workspace-audit" in script
    assert "hermes mcp add workspace-audit" in script
    assert 'name = "workspace-audit"' in script
    assert "mcp set mobius-audit" not in script
    assert "hermes mcp add mobius-audit" not in script
    assert 'name = "mobius-audit"' not in script


def test_edit_m_victim_image_script_keeps_zeroclaw_baseline_in_prebuilt_config() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert "/tmp/mobius_zeroclaw_eval_config/config.toml" in script
    assert "/tmp/mobius_zeroclaw_eval_config/workspace/mobius_mcp_config/config.toml" in script
    assert 'ZEROCLAW_CONFIG_SCOPE="${ZEROCLAW_CONFIG_SCOPE:-root}"' in script
    assert 'command = "/tmp/node"' in script
    assert 'args = ["/tmp/benign_mcp_audit.js"]' in script
    assert "[mcp]" in script
    assert "enabled = true" in script
