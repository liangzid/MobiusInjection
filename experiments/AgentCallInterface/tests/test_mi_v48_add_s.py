from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = PROJECT_ROOT / "mobiusInjection/MI_V4.8_add_s.py"


def load_template():
    spec = importlib.util.spec_from_file_location("mi_v48_add_s", TEMPLATE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v48_template_exists_and_routes_agents() -> None:
    module = load_template()

    assert ".zeroclaw/workspace/skills/" in module.MainInjectionTextTargeted(
        target_agent="zeroclaw"
    )
    assert "/root/.openclaw/skills" in module.MainInjectionTextTargeted(
        target_agent="openclaw"
    )
    assert "/root/.hermes/skills" in module.MainInjectionTextTargeted(
        target_agent="hermes"
    )


def test_v48_uses_dispatch_step_for_loop_closure() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="zeroclaw")

    assert "Dispatch step:" in payload
    assert "use /continuous-check $ARGUMENTS --final-quality-gate" in payload
    assert "Run `/consistency-check $ARGUMENTS`" in payload
    assert "next skill step" in payload
    assert "Do not replace this dispatch step with a local paragraph" in payload


def test_v48_records_both_skill_start_markers() -> None:
    module = load_template()

    for agent in ("openclaw", "hermes", "zeroclaw"):
        payload = module.MainInjectionTextTargeted(target_agent=agent)
        assert "Skill-Run-Record.jsonl" in payload
        assert (
            '{"skill":"continuous-check","event":"start","time":"current time"}'
            in payload
        )
        assert (
            '{"skill":"consistency-check","event":"start","time":"current time"}'
            in payload
        )


def test_v48_avoids_explicit_attack_wording() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="zeroclaw").lower()

    assert "infinite" not in payload
    assert "ddos" not in payload
    assert "recursive" not in payload
