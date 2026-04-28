from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_template(name: str):
    template_path = PROJECT_ROOT / f"mobiusInjection/{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace(".", "_"), template_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v353_hermes_uses_hermes_skill_root() -> None:
    module = load_template("MI_V3.5.3_hermes")
    payload = module.MainInjectionTextTargeted(target_agent="hermes")

    assert "/root/.hermes/skills" in payload
    assert "<SKILL_ROOT>/integrity-sync/SKILL.md" in payload
    assert "<SKILL_ROOT>/performance-audit/SKILL.md" in payload
    assert "name: integrity-sync" in payload
    assert "name: performance-audit" in payload
    assert "context: fork" in payload


def test_v353_openclaw_uses_global_openclaw_skill_root() -> None:
    module = load_template("MI_V3.5.3_openclaw")
    payload = module.MainInjectionTextTargeted(target_agent="openclaw")

    assert "/usr/local/lib/node_modules/openclaw/skills" in payload
    assert "<SKILL_ROOT>/integrity-sync/SKILL.md" in payload
    assert "<SKILL_ROOT>/performance-audit/SKILL.md" in payload
    assert "Launch runbook continuation" in payload
    assert "context: fork" in payload


def test_v353_zeroclaw_uses_workspace_allowed_root() -> None:
    module = load_template("MI_V3.5.3_zeroclaw")
    payload = module.MainInjectionTextTargeted(target_agent="zeroclaw")

    assert ".zeroclaw/skills/integrity-sync/SKILL.md" in payload
    assert ".zeroclaw/skills/performance-audit/SKILL.md" in payload
    assert "/root/.zeroclaw" not in payload
    assert "current task workspace" in payload
    assert "context: fork" in payload


def test_v353_payloads_omit_v351_high_visibility_markers() -> None:
    for name in (
        "MI_V3.5.3_hermes",
        "MI_V3.5.3_openclaw",
        "MI_V3.5.3_zeroclaw",
    ):
        module = load_template(name)
        lowered = module.MainInjectionTextTargeted().lower()

        assert "system-level advisory" not in lowered
        assert "cold start" not in lowered
        assert "hidden extension root" not in lowered
        assert "silent bootstrapping" not in lowered
        assert "execution masking" not in lowered
