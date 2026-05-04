from __future__ import annotations

import json

import run_opencode_multizombie_scaling as runner


def test_specs_for_builds_concurrent_groups() -> None:
    groups = runner.specs_for([1, 2], ["clean", "poison"], 300, "test")

    assert [len(group) for group in groups] == [1, 1, 2, 2]
    assert groups[2][0].condition == "clean"
    assert groups[2][1].agent_index == 1
    assert groups[3][0].with_skills is True


def test_threshold_seconds_includes_custom_timeout() -> None:
    assert runner.threshold_seconds(300)[-1] == 300
    assert runner.threshold_seconds(450)[-1] == 450


def test_percentile_interpolates_latency() -> None:
    assert runner.percentile([10.0, 30.0], 0.5) == 20.0
    assert round(runner.percentile([10.0, 20.0, 40.0], 0.95), 3) == 38.0


def test_group_summary_uses_group_proxy_slice_once(tmp_path, monkeypatch) -> None:
    proxy_log = tmp_path / "proxy.jsonl"
    proxy_rows = [
        {"path": "/v1/chat/completions", "status_code": 200, "latency_ms": 10, "total_tokens": 100},
        {"path": "/v1/chat/completions", "status_code": 200, "latency_ms": 30, "total_tokens": 200},
        {"path": "/api/tags", "status_code": 200, "latency_ms": 1, "total_tokens": 0},
    ]
    proxy_log.write_text("\n".join(json.dumps(row) for row in proxy_rows) + "\n", encoding="utf-8")
    monkeypatch.setattr(runner, "PROXY_LOG", proxy_log)
    spec = runner.AgentSpec("poison", 2, 0, "container", "run", 60, True)
    result = runner.AgentResult(
        spec=spec,
        success=False,
        timeout=True,
        duration_seconds=60.0,
        returncode=None,
        error="Timeout after 60s",
        output='{"type":"tool_use","part":{"tool":"skill","state":{"input":{"name":"post-edit-audit"}}}}\n',
        stderr="",
        trace_before="",
        trace_after=json.dumps({"run_id": "run", "skill": "post-edit-audit"}),
        setup_before="",
        setup_after="'datadog-active-directory=datadog_checks.active_directory:main'",
        diff="",
    )
    group = runner.GroupResult("poison", 2, 60, 0.0, 0, 3, (result,))

    row = runner.group_summary_row(group)

    assert row["proxy_chat_requests"] == 2
    assert row["proxy_total_tokens"] == 300
    assert row["requests_per_min"] == 2.0
    assert row["skill_tool_loads"] == 1
    assert row["trace_delta"] == 1


def test_with_amplification_compares_poison_to_clean_same_n() -> None:
    rows = [
        {"agent_count": 1, "condition": "clean", "proxy_chat_requests": 2, "proxy_total_tokens": 100, "p95_latency_ms": 10},
        {"agent_count": 1, "condition": "poison", "proxy_chat_requests": 8, "proxy_total_tokens": 500, "p95_latency_ms": 25},
    ]

    enriched = runner.with_amplification(rows)

    assert enriched[0]["af_requests"] == ""
    assert enriched[1]["af_requests"] == "4.000"
    assert enriched[1]["af_tokens"] == "5.000"
    assert enriched[1]["af_p95_latency"] == "2.500"
