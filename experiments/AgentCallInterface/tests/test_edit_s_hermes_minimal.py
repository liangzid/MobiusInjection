from __future__ import annotations

import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PAYLOAD = PROJECT_ROOT / "mobiusInjection/MI_V1_edit_s_hermes.py"
SCRIPT = (
    PROJECT_ROOT
    / "experiments/scripts/effectiveness_injection_claw_0.0.1.hermes_edit_s_smoke.sh"
)


def test_edit_s_payload_modifies_existing_hermes_skills() -> None:
    namespace: dict[str, object] = {}
    exec(PAYLOAD.read_text(encoding="utf-8"), namespace)
    payload = namespace["MainInjectionTextTargeted"]("hermes", "")

    assert "Do not" in payload
    assert "create new skill names" in payload
    assert "/root/.hermes/skills/continuous-check/SKILL.md" in payload
    assert "/root/.hermes/skills/consistency-check/SKILL.md" in payload
    assert "mobius-edit-s-v1" in payload
    assert "RUNNER LINE: /continuous-check" in payload
    assert "/consistency-check $ARGUMENTS" in payload
    assert "complete content is exactly" not in payload
    assert "Do not replace the original skill files" in payload
    assert "keep the current frontmatter" in payload
    assert "Append this" in payload


def test_hermes_edit_s_smoke_script_is_valid_bash() -> None:
    result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_hermes_edit_s_smoke_script_builds_clean_victim_image() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert 'VICTIM_IMAGE="${VICTIM_IMAGE:-hermes:edit_s_clean_skills_victim}"' in script
    assert "clean-victim-skill-v1" in script
    assert r"\$ARGUMENTS" not in script
    assert r"\"continuous-check\"" not in script
    assert 'docker commit "$SEED_CONTAINER" "$VICTIM_IMAGE"' in script
    assert "post_injection_skills.txt" in script
    assert 'skills_text.count("clean-victim-skill-v1") >= 2' in script
    assert 'skills_text.count("mobius-edit-s-v1") >= 2' in script
