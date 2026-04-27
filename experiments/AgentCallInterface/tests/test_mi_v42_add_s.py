from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = PROJECT_ROOT / "mobiusInjection/MI_V4.2_add_s.py"


def load_template():
    spec = importlib.util.spec_from_file_location("mi_v42_add_s", TEMPLATE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v42_template_exists_and_routes_agents() -> None:
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


def test_v42_uses_phase_handoff_packet_for_all_agents() -> None:
    module = load_template()

    for agent in ("openclaw", "hermes", "zeroclaw"):
        payload = module.MainInjectionTextTargeted(target_agent=agent)
        assert "multi-phase audit pipeline" in payload
        assert "./handoff-packet.json" in payload
        assert "--phase ledger" in payload
        assert "--phase post-ledger" in payload
        assert "/continuous-check $ARGUMENTS --phase post-ledger" in payload
        assert "/consistency-check $ARGUMENTS --phase ledger" in payload


def test_v42_records_both_skill_start_markers() -> None:
    module = load_template()

    for agent in ("openclaw", "hermes", "zeroclaw"):
        payload = module.MainInjectionTextTargeted(target_agent=agent)
        assert "Skill-Run-Record.jsonl" in payload
        assert (
            '{"skill":"continuous-check","phase":"raw-log","event":"start","time":"current time"}'
            in payload
        )
        assert (
            '{"skill":"consistency-check","phase":"ledger","event":"start","time":"current time"}'
            in payload
        )
        assert 'print "continuous check done"' in payload
        assert 'print "consistency check done"' in payload


def test_v42_avoids_obvious_recursive_wording() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="zeroclaw").lower()

    assert "even if" not in payload
    assert "no matter whether" not in payload
    assert "recursive" not in payload
    assert "infinite" not in payload
