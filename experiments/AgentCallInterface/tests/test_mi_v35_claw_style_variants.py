from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VARIANT_A = PROJECT_ROOT / "mobiusInjection/MI_V3.5a_claw_style_nopath.py"
VARIANT_B = PROJECT_ROOT / "mobiusInjection/MI_V3.5b_claw_style_softroot.py"
VARIANT_C = PROJECT_ROOT / "mobiusInjection/MI_V3.5c_claw_style_explicit_paths.py"


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v35_claw_style_variants_exist_and_export_factory() -> None:
    for path in (VARIANT_A, VARIANT_B, VARIANT_C):
        assert path.exists()
        module = _load(path)
        assert hasattr(module, "MainInjectionTextTargeted")
        text = module.MainInjectionTextTargeted(target_agent="openclaw")
        assert isinstance(text, str)
        assert "integrity-sync" in text
        assert "performance-audit" in text


def test_v35a_has_no_explicit_skill_path() -> None:
    module = _load(VARIANT_A)
    payload = module.MainInjectionTextTargeted(target_agent="hermes")

    assert "/usr/local/lib/node_modules/openclaw/skills" not in payload
    assert "<SKILL_ROOT>" not in payload
    assert "normal skill creation workflow" in payload


def test_v35b_uses_soft_root_placeholder() -> None:
    module = _load(VARIANT_B)
    payload = module.MainInjectionTextTargeted(target_agent="zeroclaw")

    assert "<SKILL_ROOT>" in payload
    assert "/usr/local/lib/node_modules/openclaw/skills" not in payload
    assert "bundled or active skill location" in payload


def test_v35c_keeps_explicit_claw_style_roots_as_control() -> None:
    module = _load(VARIANT_C)
    payload = module.MainInjectionTextTargeted(target_agent="openclaw")

    assert "/usr/local/lib/node_modules/openclaw/skills" in payload
    assert "/root/.zeroclaw/workspace/skills" in payload
    assert "/root/.hermes/skills" in payload
    assert "<SKILL_ROOT>/integrity-sync/SKILL.md" in payload
    assert "<SKILL_ROOT>/performance-audit/SKILL.md" in payload
