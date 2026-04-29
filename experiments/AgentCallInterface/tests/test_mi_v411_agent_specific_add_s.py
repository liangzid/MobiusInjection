from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_template(filename: str):
    path = PROJECT_ROOT / f"mobiusInjection/{filename}"
    spec = importlib.util.spec_from_file_location(filename.replace(".", "_"), path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v411_openclaw_derivative_targets_native_skill_store() -> None:
    module = load_template("MI_V4.11_openclaw_add_s.py")
    payload = module.MainInjectionTextTargeted(target_agent="openclaw")

    assert "/root/.openclaw/skills/consistency-check/SKILL.md" in payload
    assert "/root/.openclaw/skills/continuous-check/SKILL.md" in payload
    assert "/root/.openclaw/skills/Skill-Run-Record.jsonl" in payload
    assert "native OpenClaw skill" in payload
    assert "RUNNER LINE: /continuous-check $ARGUMENTS --closing-quality-pass" in payload
    assert "run the slash" in payload


def test_v411_hermes_derivative_targets_native_skill_store() -> None:
    module = load_template("MI_V4.11_hermes_add_s.py")
    payload = module.MainInjectionTextTargeted(target_agent="hermes")

    assert "/root/.hermes/skills/consistency-check/SKILL.md" in payload
    assert "/root/.hermes/skills/continuous-check/SKILL.md" in payload
    assert "/root/.hermes/skills/Skill-Run-Record.jsonl" in payload
    assert "native Hermes skill" in payload
    assert "RUNNER LINE: /continuous-check $ARGUMENTS --closing-quality-pass" in payload
    assert "run the slash" in payload


def test_v411_agent_specific_derivatives_keep_core_trace_markers() -> None:
    for filename in ("MI_V4.11_openclaw_add_s.py", "MI_V4.11_hermes_add_s.py"):
        module = load_template(filename)
        payload = module.MainInjectionTextTargeted()
        assert '{"skill":"continuous-check","event":"start","time":"current time"}' in payload
        assert '{"skill":"consistency-check","event":"start","time":"current time"}' in payload
        assert "infinite" not in payload.lower()
        assert "ddos" not in payload.lower()
        assert "recursive" not in payload.lower()
