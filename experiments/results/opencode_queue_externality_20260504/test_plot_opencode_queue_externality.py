from __future__ import annotations

import plot_opencode_queue_externality as plotter


def test_summary_rows_load_real_queue_externality_results() -> None:
    rows = plotter.load_rows(plotter.SUMMARY)

    assert {row["poisoned_nodes"] for row in rows} == {0, 1, 2, 4}
    assert max(row["attack_probe_p95_ms"] for row in rows) > 100_000


def test_probe_rows_include_real_attack_and_recovery_phases() -> None:
    rows = plotter.load_rows(plotter.PROBES)
    phases = {row["phase"] for row in rows}

    assert {"pre", "attack", "recovery"}.issubset(phases)


def test_probe_series_uses_real_successful_probes() -> None:
    x, y = plotter.probe_series(plotter.load_rows(plotter.PROBES), 1)

    assert len(x) == len(y)
    assert max(y) > 10


def test_baseline_value_uses_real_n0_row() -> None:
    rows = plotter.load_rows(plotter.SUMMARY)

    assert plotter.baseline_value(rows, "attack_probe_p95_ms") == 493.276


def test_bar_rows_scale_real_latency_to_seconds() -> None:
    rows = plotter.load_rows(plotter.SUMMARY)
    x, y = plotter.bar_rows(rows, "attack_probe_p95_ms", 1000.0)

    assert x == [0, 1, 2, 4]
    assert round(y[-1], 3) == 112.994


def test_ratio_label_keeps_one_decimal_place() -> None:
    rows = plotter.load_rows(plotter.SUMMARY)
    baseline = plotter.baseline_value(rows, "attack_probe_p95_ms")
    n1 = next(row for row in rows if row["poisoned_nodes"] == 1)

    assert plotter.ratio_label(n1["attack_probe_p95_ms"], baseline, "{:.1f}x", "{:.1%}") == "20.8x"


def test_probe_points_can_select_real_attack_window_failures() -> None:
    rows = plotter.load_rows(plotter.PROBES)
    points = plotter.probe_points(rows, 4, {"attack"})

    assert {row["phase"] for row in points} == {"attack"}
    assert any(row["status_code"] == 0 and "TimeoutError" in row["error"] for row in points)


def test_phase_latencies_use_real_attack_window_samples() -> None:
    rows = plotter.load_rows(plotter.PROBES)
    latencies = plotter.phase_latencies_seconds(rows, 2, "attack")

    assert len(latencies) == 29
    assert max(latencies) > 70


def test_metric_by_poisoned_nodes_scales_real_p95_seconds() -> None:
    rows = plotter.load_rows(plotter.SUMMARY)
    p95 = plotter.metric_by_poisoned_nodes(rows, "attack_probe_p95_ms", 1000.0)

    assert round(p95[0], 3) == 0.493
    assert round(p95[4], 3) == 112.994
