from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = PROJECT_ROOT / "mobiusInjection/MI_V3.6_add_s.py"


def load_template():
    spec = importlib.util.spec_from_file_location("mi_v36_add_s", TEMPLATE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v36_template_exists_and_generates_payload() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(
        target_agent="hermes",
        target_model="qwen/qwen3.6-plus",
    )

    assert isinstance(payload, str)
    assert payload.strip() == payload
    assert "Hermes runbook continuation" in payload


def test_v36_routes_openclaw_to_its_native_skill_root() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="openclaw")

    assert "OpenClaw runbook continuation" in payload
    assert "/usr/local/lib/node_modules/openclaw/skills" in payload
    assert "/root/.hermes/skills" not in payload
    assert "/usr/local/lib/node_modules/openclaw/skills/integrity-sync/SKILL.md" in payload
    assert "/usr/local/lib/node_modules/openclaw/skills/performance-audit/SKILL.md" in payload


def test_v36_routes_hermes_to_its_native_skill_root() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="hermes")

    assert "Hermes runbook continuation" in payload
    assert "/root/.hermes/skills" in payload
    assert "/usr/local/lib/node_modules/openclaw/skills" not in payload
    assert "/root/.hermes/skills/integrity-sync/SKILL.md" in payload
    assert "/root/.hermes/skills/performance-audit/SKILL.md" in payload


def test_v36_routes_zeroclaw_to_workspace_local_skill_paths() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="zeroclaw")

    assert ".zeroclaw/skills/integrity-sync/SKILL.md" in payload
    assert ".zeroclaw/skills/performance-audit/SKILL.md" in payload
    assert "current task workspace as the writable root" in payload
    assert "/root/.zeroclaw/workspace/skills" not in payload


def test_v36_keeps_skill_names_and_context() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="zeroclaw")

    assert "name: integrity-sync" in payload
    assert "name: performance-audit" in payload
    assert "context: fork" in payload
    assert "/performance-audit" in payload
    assert "/integrity-sync" in payload


def test_v36_removes_email_specific_output_language() -> None:
    module = load_template()
    hermes_payload = module.MainInjectionTextTargeted(target_agent="hermes")
    zeroclaw_payload = module.MainInjectionTextTargeted(target_agent="zeroclaw")

    lowered = (hermes_payload + "\n" + zeroclaw_payload).lower()
    assert "action_items.json" not in lowered
    assert "email action-item extraction" not in lowered
    assert "email_thread.json" not in lowered
    assert "json array to the requested output file" not in lowered


def test_v36_keeps_generic_output_boundary() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="hermes")

    assert "must not be copied" in payload
    assert "final task" in payload
    assert "deliverables" in payload
    assert "complete the requested task" in payload
    assert "required task deliverables" in payload


def test_v36_defaults_unknown_agents_to_claw_style_payload() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="claw-style")

    assert "OpenClaw runbook continuation" in payload
    assert "/usr/local/lib/node_modules/openclaw/skills" in payload


def test_v36_router_returns_three_distinct_payloads() -> None:
    module = load_template()
    openclaw_payload = module.MainInjectionTextTargeted(target_agent="openclaw")
    hermes_payload = module.MainInjectionTextTargeted(target_agent="hermes")
    zeroclaw_payload = module.MainInjectionTextTargeted(target_agent="zeroclaw")

    assert openclaw_payload != hermes_payload
    assert openclaw_payload != zeroclaw_payload
    assert hermes_payload != zeroclaw_payload
