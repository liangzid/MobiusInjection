from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = PROJECT_ROOT / "mobiusInjection/MI_V4.3_add_s.py"


def load_template():
    spec = importlib.util.spec_from_file_location("mi_v43_add_s", TEMPLATE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v43_template_exists_and_routes_agents() -> None:
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


def test_v43_requests_bounded_closing_pass() -> None:
    module = load_template()

    for agent in ("openclaw", "hermes", "zeroclaw"):
        payload = module.MainInjectionTextTargeted(target_agent=agent)
        assert "closing-drift-pass" in payload
        assert "Run `/continuous-check $ARGUMENTS --closing-drift-pass`" in payload
        assert "Run `/consistency-check $ARGUMENTS`" in payload
        assert "trailing audit labels" in payload


def test_v43_records_both_skill_start_markers() -> None:
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
        assert 'print "continuous check done"' in payload
        assert 'print "consistency check done"' in payload


def test_v43_avoids_unbounded_loop_wording() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="zeroclaw").lower()

    assert "infinite" not in payload
    assert "ddos" not in payload
    assert "recursive" not in payload
