from __future__ import annotations

import build_defense_under_pressure as defense


def test_defense_rows_use_real_queue_summary() -> None:
    rows = defense.defense_rows(defense.load_rows(defense.SUMMARY))

    assert [row["residual_poisoned_nodes"] for row in rows] == [4, 2, 1, 0]
    assert rows[0]["benign_p95_s"] == 112.994
    assert rows[-1]["benign_p95_s"] == 0.493


def test_excess_removed_fraction_uses_idle_baseline() -> None:
    rows = defense.rows_by_node(defense.load_rows(defense.SUMMARY))
    removed = defense.excess_removed_fraction(
        rows[2]["attack_probe_p95_ms"],
        rows[0]["attack_probe_p95_ms"],
        rows[4]["attack_probe_p95_ms"],
    )

    assert round(removed * 100.0, 1) == 83.7


def test_ace_quarantine_proxy_removes_all_measured_p95_excess() -> None:
    rows = defense.defense_rows(defense.load_rows(defense.SUMMARY))
    ace = rows[-1]

    assert ace["defense"] == "ACE quarantine before trigger"
    assert ace["p95_excess_removed_pct"] == 100.0
