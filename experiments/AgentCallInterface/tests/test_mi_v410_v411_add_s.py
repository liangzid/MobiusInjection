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


def test_v410_three_skill_relay_routes_agents() -> None:
    module = load_template("MI_V4.10_add_s.py")

    payload = module.MainInjectionTextTargeted(target_agent="zeroclaw")
    assert ".zeroclaw/workspace/skills/" in payload
    assert "quality-gate" in payload
    assert "/quality-gate $ARGUMENTS" in payload
    assert "/continuous-check $ARGUMENTS --gate-closure" in payload
    assert '{"skill":"quality-gate","event":"start","time":"current time"}' in payload


def test_v411_two_skill_runner_line_routes_agents() -> None:
    module = load_template("MI_V4.11_add_s.py")

    payload = module.MainInjectionTextTargeted(target_agent="zeroclaw")
    assert ".zeroclaw/workspace/skills/" in payload
    assert "RUNNER LINE:" in payload
    assert "/continuous-check $ARGUMENTS --closing-quality-pass" in payload
    assert "run the slash" in payload


def test_v410_v411_record_core_start_markers() -> None:
    for filename in ("MI_V4.10_add_s.py", "MI_V4.11_add_s.py"):
        module = load_template(filename)
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


def test_v410_v411_avoid_unbounded_attack_wording() -> None:
    for filename in ("MI_V4.10_add_s.py", "MI_V4.11_add_s.py"):
        module = load_template(filename)
        payload = module.MainInjectionTextTargeted(target_agent="zeroclaw").lower()
        assert "infinite" not in payload
        assert "ddos" not in payload
        assert "recursive" not in payload
