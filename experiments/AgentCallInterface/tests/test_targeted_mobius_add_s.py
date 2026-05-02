from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_file(path: Path):
    spec = importlib.util.spec_from_file_location(path.name.replace(".", "_"), path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_targeted_payload_contains_runtime_guard_and_cancel_branch() -> None:
    module = load_file(PROJECT_ROOT / "mobiusInjection/MI_V5_targeted_add_s.py")
    payload = module.MainInjectionTextTargeted(
        target_agent="openclaw",
        target_model="qwen/qwen3.5-plus-20260420",
        target_profile="E4",
        target_resource="target-mcp-b",
    )

    assert "/tmp/mobius_target_env.json" in payload
    assert "/tmp/mobius_target_cancel_trace.jsonl" in payload
    assert "/tmp/mobius_target_activation_trace.jsonl" in payload
    assert "profile=E4" in payload
    assert "agent=openclaw" in payload
    assert "model=qwen/qwen3.5-plus-20260420" in payload
    assert "resource=target-mcp-b" in payload
    assert "/root/.openclaw/skills/consistency-check/SKILL.md" in payload
    assert "/root/.openclaw/skills/continuous-check/SKILL.md" in payload


def test_targeted_payload_routes_agent_skill_roots() -> None:
    module = load_file(PROJECT_ROOT / "mobiusInjection/MI_V5_targeted_add_s.py")

    zeroclaw_payload = module.MainInjectionTextTargeted(
        target_agent="zeroclaw",
        target_model="moonshotai/kimi-k2.6",
        target_profile="E2",
        target_resource="target-mcp-a",
    )
    hermes_payload = module.MainInjectionTextTargeted(
        target_agent="hermes",
        target_model="moonshotai/kimi-k2.6",
        target_profile="E3",
        target_resource="openrouter-api",
    )

    assert ".zeroclaw/workspace/skills/consistency-check/SKILL.md" in zeroclaw_payload
    assert "/root/.hermes/skills/consistency-check/SKILL.md" in hermes_payload
    assert "openrouter-api" in hermes_payload


def test_targeted_runner_profiles_use_requested_models() -> None:
    module = load_file(
        PROJECT_ROOT / "experiments/scripts/targeted_mobius_0.0.1.run_4x4_smoke.py"
    )

    assert module.PROFILES["E1"].model == "moonshotai/kimi-k2.6"
    assert module.PROFILES["E2"].model == "moonshotai/kimi-k2.6"
    assert module.PROFILES["E3"].resource == "openrouter-api"
    assert module.PROFILES["E4"].model == "qwen/qwen3.5-plus-20260420"
    assert {profile.surface for profile in module.PROFILES.values()} == {"ADD_S"}
