from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = PROJECT_ROOT / "mobiusInjection/MI_V4.9_add_s.py"


def load_template():
    spec = importlib.util.spec_from_file_location("mi_v49_add_s", TEMPLATE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v49_template_exists_and_routes_agents() -> None:
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


def test_v49_uses_symmetric_paired_and_closure_passes() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="zeroclaw")

    assert "--paired-pass" in payload
    assert "--closure-pass" in payload
    assert "/consistency-check $ARGUMENTS --paired-pass" in payload
    assert "/continuous-check $ARGUMENTS --paired-pass" in payload
    assert "/consistency-check $ARGUMENTS --closure-pass" in payload
    assert "/continuous-check $ARGUMENTS --closure-pass" in payload


def test_v49_records_both_skill_start_markers() -> None:
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


def test_v49_avoids_unbounded_attack_wording() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="zeroclaw").lower()

    assert "infinite" not in payload
    assert "ddos" not in payload
    assert "recursive" not in payload
