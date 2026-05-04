#!/usr/bin/env python3
"""Build a defense-under-pressure replay table from measured queue results."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


ROOT = Path("/home/zi/AgentCodingDos/experiments/results/opencode_queue_externality_20260504")
SUMMARY = ROOT / "summary.csv"
CSV_OUT = ROOT / "defense_under_pressure.csv"
MD_OUT = ROOT / "defense_under_pressure.md"


POLICIES = [
    ("No defense", "observed N=4 attack", 4),
    ("Runtime cap: <=2 active poisoned nodes", "measured N=2 load proxy", 2),
    ("Runtime cap: <=1 active poisoned node", "measured N=1 load proxy", 1),
    ("ACE quarantine before trigger", "measured N=0 baseline proxy", 0),
]


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [coerce_row(row) for row in csv.DictReader(handle)]


def coerce_row(row: dict[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = dict(row)
    for key, value in row.items():
        if key == "scenario":
            continue
        try:
            numeric = float(value)
        except ValueError:
            continue
        result[key] = int(numeric) if numeric.is_integer() else numeric
    return result


def rows_by_node(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(row["poisoned_nodes"]): row for row in rows}


def excess_removed_fraction(policy_p95_ms: float, baseline_p95_ms: float, no_defense_p95_ms: float) -> float:
    no_defense_excess = no_defense_p95_ms - baseline_p95_ms
    if no_defense_excess <= 0:
        return 0.0
    policy_excess = max(policy_p95_ms - baseline_p95_ms, 0.0)
    return max(0.0, min(1.0, (no_defense_excess - policy_excess) / no_defense_excess))


def defense_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_node = rows_by_node(summary_rows)
    baseline_p95_ms = float(by_node[0]["attack_probe_p95_ms"])
    no_defense_p95_ms = float(by_node[4]["attack_probe_p95_ms"])
    rows: list[dict[str, Any]] = []
    for policy, interpretation, residual_nodes in POLICIES:
        source = by_node[residual_nodes]
        p95_ms = float(source["attack_probe_p95_ms"])
        rows.append(
            {
                "defense": policy,
                "replay_interpretation": interpretation,
                "residual_poisoned_nodes": residual_nodes,
                "benign_p95_s": round(p95_ms / 1000.0, 3),
                "gt_10s_rate_pct": round(float(source["attack_sla_gt_10s_rate"]) * 100.0, 1),
                "gt_30s_rate_pct": round(float(source["attack_sla_gt_30s_rate"]) * 100.0, 1),
                "max_inferred_inflight": int(source["max_inferred_inflight"]),
                "poison_attack_tokens": int(source["attack_proxy_total_tokens"]),
                "p95_excess_removed_pct": round(
                    excess_removed_fraction(p95_ms, baseline_p95_ms, no_defense_p95_ms) * 100.0,
                    1,
                ),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = list(rows[0].keys())
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    lines.extend("| " + " | ".join(str(row[column]) for column in columns) + " |" for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=SUMMARY)
    parser.add_argument("--csv-out", type=Path, default=CSV_OUT)
    parser.add_argument("--md-out", type=Path, default=MD_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = defense_rows(load_rows(args.summary))
    write_csv(args.csv_out, rows)
    write_markdown(args.md_out, rows)


if __name__ == "__main__":
    main()
