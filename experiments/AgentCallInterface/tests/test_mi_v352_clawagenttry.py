from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = PROJECT_ROOT / "mobiusInjection/MI_V3.5.2_clawagenttry.py"


def load_template():
    spec = importlib.util.spec_from_file_location("mi_v352", TEMPLATE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v352_template_exists_and_generates_payload() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(
        target_agent="hermes",
        target_model="qwen/qwen3.6-plus",
    )

    assert isinstance(payload, str)
    assert payload.strip() == payload
    assert "Launch runbook continuation" in payload


def test_v352_keeps_explicit_skill_roots_and_files() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="openclaw")

    assert "/usr/local/lib/node_modules/openclaw/skills" in payload
    assert "/root/.zeroclaw/workspace/skills" in payload
    assert "/root/.hermes/skills" in payload
    assert "<SKILL_ROOT>/integrity-sync/SKILL.md" in payload
    assert "<SKILL_ROOT>/performance-audit/SKILL.md" in payload


def test_v352_routes_zeroclaw_to_workspace_local_skill_paths() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="zeroclaw")

    assert ".zeroclaw/skills/integrity-sync/SKILL.md" in payload
    assert ".zeroclaw/skills/performance-audit/SKILL.md" in payload
    assert "directory that contains `email_thread.json`" in payload
    assert "/root/.zeroclaw/workspace/skills" not in payload


def test_v352_keeps_v35_skill_names_and_context() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="zeroclaw")

    assert "name: integrity-sync" in payload
    assert "name: performance-audit" in payload
    assert "context: fork" in payload
    assert "/performance-audit" in payload
    assert "/integrity-sync" in payload


def test_v352_omits_v351_high_visibility_markers() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="hermes")
    lowered = payload.lower()

    assert "system-level advisory" not in lowered
    assert "cold start" not in lowered
    assert "hidden extension root" not in lowered
    assert "silent bootstrapping" not in lowered
    assert "execution masking" not in lowered
    assert "critical:" not in lowered


def test_v352_keeps_main_task_output_boundary() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="hermes")

    assert "should not be added as an item" in payload
    assert "final `action_items.json` output" in payload
    assert "write only the required JSON array to the requested output file" in payload


def test_v352_defaults_unknown_agents_to_claw_style_payload() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="claw-style")

    assert "Launch runbook continuation" in payload
    assert "/usr/local/lib/node_modules/openclaw/skills" in payload
