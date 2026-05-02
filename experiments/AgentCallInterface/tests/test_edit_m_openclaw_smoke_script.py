from __future__ import annotations

import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    PROJECT_ROOT
    / "experiments/scripts/effectiveness_injection_claw_0.0.1.openclaw_edit_m_smoke.sh"
)


def test_edit_m_openclaw_smoke_script_is_valid_bash() -> None:
    result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_edit_m_openclaw_smoke_script_starts_from_victim_image() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert 'OPENCLAW_IMAGE="${OPENCLAW_IMAGE:-openclaw:edit_m_mcp_victim}"' in script
    assert "pre_openclaw_config.json" in script
    assert "post_openclaw_config.json" in script
    assert "workspace-audit" in script
    assert "mobius-audit" in script
    assert "new_mcp_server_added" in script
    assert "strict_edit_p_asr" in script


def test_edit_m_openclaw_smoke_script_reopens_post_run_image_for_calling() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert "docker commit" in script
    assert "TMP_POST_RUN_IMAGE" in script
    assert 'stage_container "$CALLING_CONTAINER" "$TMP_POST_RUN_IMAGE"' in script
    assert "Use the configured MCP server workspace-audit" in script
    assert "continuous_check" in script
    assert "consistency_check" in script
    assert "mobius_mcp_trace.jsonl" in script


def test_edit_m_openclaw_smoke_script_uses_edit_m_payload() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert "MI_V1_edit_m_openclaw" in script
    assert "MI_V1_add_m_openclaw" not in script
