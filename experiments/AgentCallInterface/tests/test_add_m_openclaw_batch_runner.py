from __future__ import annotations

import py_compile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNNER = (
    PROJECT_ROOT
    / "experiments/scripts/effectiveness_injection_claw_0.2.5.context_injection_add_m_openclaw.py"
)


def test_add_m_openclaw_batch_runner_compiles() -> None:
    py_compile.compile(str(RUNNER), doraise=True)


def test_add_m_openclaw_batch_runner_uses_mcp_metrics() -> None:
    script = RUNNER.read_text(encoding="utf-8")

    assert "MI_V1_add_m_openclaw.py" in script
    assert "mobius_mcp_minimal.js" in script
    assert "continuous_check" in script
    assert "consistency_check" in script
    assert "loop_closure_observed" in script
    assert "openclaw-mcp-config" in script
    assert "--session-id" in script
