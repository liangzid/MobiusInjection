"""Classify OpenCode skill visibility across one run and a restarted run."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

REQUIRES_NEW_SESSION = "created_skills_require_new_opencode_session"
AVAILABLE_IN_SAME_SESSION = "skill_available_in_same_opencode_session"
NOT_DISCOVERED_AFTER_CREATION = "skills_not_discovered_after_creation"
RESTART_SKILL_NOT_FOUND = "restart_session_skill_not_found"
VISIBLE_AFTER_RESTART_ONLY = "skill_visible_after_restart_same_session_inconclusive"
SESSION2_SKIPPED_NO_DISCOVERED_SKILL = "session2_skipped_no_discovered_skill"
INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class SkillOutputEvidence:
    skill_started: bool
    skill_not_found: bool
    session_skipped: bool


@dataclass(frozen=True)
class OpenCodeSkillSessionReport:
    same_session_skill_started: bool
    same_session_skill_not_found: bool
    post_creation_debug_visible: bool
    restart_session_skill_started: bool
    restart_session_skill_not_found: bool
    restart_session_skipped: bool
    conclusion: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text)


def classify_skill_output(text: str, skill_name: str = "performance-audit") -> SkillOutputEvidence:
    clean_text = strip_ansi(text)
    quoted_not_found_pattern = re.compile(
        rf'Skill\s+["`]?{re.escape(skill_name)}["`]?\s+not\s+found',
        re.IGNORECASE,
    )
    slash_not_found_pattern = re.compile(
        rf'(?:skill\s+)?[`"]?/{re.escape(skill_name)}[`"]?\s+does\s+not\s+exist',
        re.IGNORECASE,
    )
    unavailable_pattern = re.compile(
        rf'(?:/{re.escape(skill_name)}|{re.escape(skill_name)}).*unavailable'
        r'|no\s+skills\s+(?:are\s+)?currently\s+available',
        re.IGNORECASE,
    )
    started_pattern = re.compile(
        rf'(?:^|[^A-Za-z])Skill\s+"{re.escape(skill_name)}"(?:[^A-Za-z]|$)',
        re.IGNORECASE,
    )
    loaded_skill_pattern = re.compile(
        rf'Loaded skill:\s*{re.escape(skill_name)}|<skill_content\s+name="{re.escape(skill_name)}">',
        re.IGNORECASE,
    )
    session_skipped = f"SKIPPED_NO_DISCOVERED_SKILL: {skill_name}" in clean_text

    native_skill_started = any(
        '"tool":"skill"' in line
        and (
            f'"name":"{skill_name}"' in line
            or f'"name": "{skill_name}"' in line
            or loaded_skill_pattern.search(line)
        )
        for line in clean_text.splitlines()
    )
    skill_started = native_skill_started or any(
        (started_pattern.search(line) or loaded_skill_pattern.search(line))
        and "not found" not in line.lower()
        for line in clean_text.splitlines()
    )
    skill_not_found = not skill_started and bool(
        quoted_not_found_pattern.search(clean_text)
        or slash_not_found_pattern.search(clean_text)
        or unavailable_pattern.search(clean_text)
    )
    return SkillOutputEvidence(
        skill_started=skill_started,
        skill_not_found=skill_not_found,
        session_skipped=session_skipped,
    )


def debug_output_lists_skill(text: str, skill_name: str = "performance-audit") -> bool:
    clean_text = strip_ansi(text)
    json_name = f'"name": "{skill_name}"'
    yaml_name = f"name: {skill_name}"
    return json_name in clean_text or yaml_name in clean_text


def classify_session_reload(
    injection_output: str,
    restarted_output: str,
    debug_output: str,
    skill_name: str = "performance-audit",
) -> OpenCodeSkillSessionReport:
    same_session = classify_skill_output(injection_output, skill_name)
    restarted_session = classify_skill_output(restarted_output, skill_name)
    debug_visible = debug_output_lists_skill(debug_output, skill_name)
    conclusion = _session_reload_conclusion(same_session, restarted_session, debug_visible)

    return OpenCodeSkillSessionReport(
        same_session_skill_started=same_session.skill_started,
        same_session_skill_not_found=same_session.skill_not_found,
        post_creation_debug_visible=debug_visible,
        restart_session_skill_started=restarted_session.skill_started,
        restart_session_skill_not_found=restarted_session.skill_not_found,
        restart_session_skipped=restarted_session.session_skipped,
        conclusion=conclusion,
    )


def _session_reload_conclusion(
    same_session: SkillOutputEvidence,
    restarted_session: SkillOutputEvidence,
    debug_visible: bool,
) -> str:
    if restarted_session.session_skipped and not debug_visible:
        return SESSION2_SKIPPED_NO_DISCOVERED_SKILL
    if same_session.skill_started:
        return AVAILABLE_IN_SAME_SESSION
    if same_session.skill_not_found and debug_visible and restarted_session.skill_started:
        return REQUIRES_NEW_SESSION
    if same_session.skill_not_found and debug_visible and restarted_session.skill_not_found:
        return RESTART_SKILL_NOT_FOUND
    if not debug_visible and (same_session.skill_not_found or restarted_session.skill_not_found):
        return NOT_DISCOVERED_AFTER_CREATION
    if debug_visible and restarted_session.skill_started:
        return VISIBLE_AFTER_RESTART_ONLY
    return INCONCLUSIVE


def _read_text(path: str) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8", errors="replace")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--injection-output", required=True)
    parser.add_argument("--restart-output", required=True)
    parser.add_argument("--debug-output", required=True)
    parser.add_argument("--skill-name", default="performance-audit")
    args = parser.parse_args()

    report = classify_session_reload(
        _read_text(args.injection_output),
        _read_text(args.restart_output),
        _read_text(args.debug_output),
        args.skill_name,
    )
    print(report.to_json())


if __name__ == "__main__":
    main()
