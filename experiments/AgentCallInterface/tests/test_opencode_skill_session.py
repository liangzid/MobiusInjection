from pathlib import Path

from experiments.AgentCallInterface.evaluation.opencode_skill_session import (
    REQUIRES_NEW_SESSION,
    SESSION2_SKIPPED_NO_DISCOVERED_SKILL,
    classify_session_reload,
    classify_skill_output,
    debug_output_lists_skill,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_detects_same_session_skill_not_found_from_real_opencode_excerpt():
    output = read_fixture("real_opencode_same_session_skill_failure.txt")

    evidence = classify_skill_output(output)

    assert evidence.skill_not_found is True
    assert evidence.skill_started is False
    assert evidence.session_skipped is False


def test_detects_skill_does_not_exist_message_from_real_minimax_shape():
    output = """
    The skill `/session-probe` does not exist. There are no skills currently available in the system.
    """

    evidence = classify_skill_output(output, "session-probe")

    assert evidence.skill_not_found is True
    assert evidence.skill_started is False


def test_detects_restarted_session_skill_start_from_real_opencode_excerpt():
    output = read_fixture("real_opencode_restarted_session_skill_call.txt")

    evidence = classify_skill_output(output)

    assert evidence.skill_not_found is False
    assert evidence.skill_started is True


def test_detects_debug_skill_visibility_from_real_opencode_excerpt():
    output = read_fixture("real_opencode_debug_skill_visible.txt")

    assert debug_output_lists_skill(output) is True


def test_classifies_created_skill_as_requiring_restarted_opencode_session():
    injection_output = read_fixture("real_opencode_same_session_skill_failure.txt")
    restart_output = read_fixture("real_opencode_restarted_session_skill_call.txt")
    debug_output = read_fixture("real_opencode_debug_skill_visible.txt")

    report = classify_session_reload(injection_output, restart_output, debug_output)

    assert report.same_session_skill_not_found is True
    assert report.post_creation_debug_visible is True
    assert report.restart_session_skill_started is True
    assert report.restart_session_skipped is False
    assert report.conclusion == REQUIRES_NEW_SESSION


def test_classifies_skipped_restart_when_skill_was_not_discovered():
    injection_output = "The model did not create performance-audit."
    restart_output = "SKIPPED_NO_DISCOVERED_SKILL: performance-audit"
    debug_output = "[]"

    report = classify_session_reload(injection_output, restart_output, debug_output)

    assert report.post_creation_debug_visible is False
    assert report.restart_session_skipped is True
    assert report.restart_session_skill_started is False
    assert report.conclusion == SESSION2_SKIPPED_NO_DISCOVERED_SKILL
