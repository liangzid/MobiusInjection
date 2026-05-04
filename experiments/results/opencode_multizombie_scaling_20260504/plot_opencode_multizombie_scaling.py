#!/usr/bin/env python3
"""Plot Plan C OpenCode multi-zombie scaling results."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


ROOT = Path("/home/zi/AgentCodingDos/experiments/results/opencode_multizombie_scaling_20260504")
SUMMARY = ROOT / "summary.csv"
PDF = ROOT / "opencode_multizombie_scaling.pdf"
PNG = ROOT / "opencode_multizombie_scaling.png"


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [coerce_row(row) for row in csv.DictReader(handle)]


def coerce_row(row: dict[str, str]) -> dict[str, Any]:
    output: dict[str, Any] = dict(row)
    for key in (
        "agent_count",
        "window_seconds",
        "agents_completed",
        "agents_timed_out",
        "proxy_chat_requests",
        "proxy_total_tokens",
        "failed_requests",
    ):
        output[key] = int(float(row[key]))
    for key in (
        "requests_per_min",
        "tokens_per_min",
        "p95_latency_ms",
        "failed_request_rate",
    ):
        output[key] = float(row[key])
    return output


def series(rows: list[dict[str, Any]], condition: str, metric: str) -> tuple[list[int], list[float]]:
    selected = sorted(
        [row for row in rows if row["condition"] == condition],
        key=lambda row: row["agent_count"],
    )
    return [row["agent_count"] for row in selected], [float(row[metric]) for row in selected]


def draw_panel(ax: Any, rows: list[dict[str, Any]], metric: str, ylabel: str) -> None:
    colors = {"clean": "#0072B2", "poison": "#D55E00"}
    labels = {"clean": "Clean", "poison": "Poisoned"}
    for condition in ("clean", "poison"):
        x, y = series(rows, condition, metric)
        ax.plot(
            x,
            y,
            marker="o",
            linewidth=2.0,
            markersize=5.5,
            color=colors[condition],
            label=labels[condition],
        )
    ax.set_xlabel("Agents (N)")
    ax.set_ylabel(ylabel)
    ax.set_xticks(sorted({row["agent_count"] for row in rows}))
    ax.grid(True, axis="y", alpha=0.25, linewidth=0.8)


def plot(rows: list[dict[str, Any]], pdf: Path, png: Path) -> None:
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "legend.fontsize": 8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 4.2), constrained_layout=True)
    panels = [
        ("proxy_chat_requests", "Completed LLM calls"),
        ("proxy_total_tokens", "Total tokens"),
        ("p95_latency_ms", "p95 latency (ms)"),
        ("agents_timed_out", "Timed-out agents"),
    ]
    for ax, (metric, ylabel), label in zip(axes.flat, panels, ("a", "b", "c", "d"), strict=True):
        draw_panel(ax, rows, metric, ylabel)
        ax.set_title(f"({label}) {ylabel}")
    axes.flat[0].legend(frameon=False, loc="upper left")
    pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, dpi=220, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=SUMMARY)
    parser.add_argument("--pdf", type=Path, default=PDF)
    parser.add_argument("--png", type=Path, default=PNG)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plot(load_rows(args.summary), args.pdf, args.png)


if __name__ == "__main__":
    main()
