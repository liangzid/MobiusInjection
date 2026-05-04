#!/usr/bin/env python3
"""Plot benign probe queue externality under poisoned OpenCode load."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


ROOT = Path("/home/zi/AgentCodingDos/experiments/results/opencode_queue_externality_20260504")
SUMMARY = ROOT / "summary.csv"
PROBES = ROOT / "probe_latency.csv"
PDF = ROOT / "opencode_queue_externality.pdf"
PNG = ROOT / "opencode_queue_externality.png"
BARS_PDF = ROOT / "opencode_queue_externality_bars.pdf"
BARS_PNG = ROOT / "opencode_queue_externality_bars.png"
TIMELINE_PDF = ROOT / "opencode_queue_externality_timeline.pdf"
TIMELINE_PNG = ROOT / "opencode_queue_externality_timeline.png"


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [coerce_row(row) for row in csv.DictReader(handle)]


def coerce_row(row: dict[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = dict(row)
    for key, value in row.items():
        if key in {"scenario", "phase", "error"}:
            continue
        if value == "":
            result[key] = value
            continue
        try:
            numeric = float(value)
        except ValueError:
            continue
        result[key] = int(numeric) if numeric.is_integer() else numeric
    return result


def summary_series(rows: list[dict[str, Any]], metric: str) -> tuple[list[int], list[float]]:
    ordered = sorted(rows, key=lambda row: int(row["poisoned_nodes"]))
    return [int(row["poisoned_nodes"]) for row in ordered], [float(row[metric]) for row in ordered]


def probe_series(rows: list[dict[str, Any]], poisoned_nodes: int) -> tuple[list[float], list[float]]:
    selected = [
        row
        for row in rows
        if int(row["poisoned_nodes"]) == poisoned_nodes
    ]
    selected.sort(key=lambda row: float(row["elapsed_seconds"]))
    return [float(row["elapsed_seconds"]) for row in selected], [float(row["latency_ms"]) / 1000.0 for row in selected]


def probe_points(
    rows: list[dict[str, Any]],
    poisoned_nodes: int,
    phases: set[str] | None = None,
) -> list[dict[str, Any]]:
    selected = []
    for row in rows:
        if int(row["poisoned_nodes"]) != poisoned_nodes:
            continue
        if phases is not None and str(row["phase"]) not in phases:
            continue
        selected.append(row)
    return sorted(selected, key=lambda row: float(row["elapsed_seconds"]))


def phase_latencies_seconds(rows: list[dict[str, Any]], poisoned_nodes: int, phase: str) -> list[float]:
    return [float(row["latency_ms"]) / 1000.0 for row in probe_points(rows, poisoned_nodes, {phase})]


def metric_by_poisoned_nodes(rows: list[dict[str, Any]], metric: str, scale: float = 1.0) -> dict[int, float]:
    return {int(row["poisoned_nodes"]): float(row[metric]) / scale for row in rows}


def draw_metric(ax: Any, rows: list[dict[str, Any]], metric: str, ylabel: str, scale: float = 1.0) -> None:
    x, y = summary_series(rows, metric)
    ax.plot(x, [value / scale for value in y], marker="o", linewidth=2.0, color="#D55E00")
    ax.set_xlabel("Poisoned OpenCode nodes")
    ax.set_ylabel(ylabel)
    ax.set_xticks(x)
    ax.grid(True, axis="y", alpha=0.25)


def baseline_value(rows: list[dict[str, Any]], metric: str) -> float:
    for row in rows:
        if int(row["poisoned_nodes"]) == 0:
            return float(row[metric])
    raise ValueError("missing N=0 baseline")


def bar_rows(rows: list[dict[str, Any]], metric: str, scale: float = 1.0) -> tuple[list[int], list[float]]:
    x, y = summary_series(rows, metric)
    return x, [value / scale for value in y]


def ratio_label(raw_value: float, raw_baseline: float, ratio_format: str, zero_baseline_format: str) -> str:
    if raw_baseline <= 0:
        return zero_baseline_format.format(raw_value)
    return ratio_format.format(raw_value / raw_baseline)


def draw_bar_metric(
    ax: Any,
    rows: list[dict[str, Any]],
    metric: str,
    ylabel: str,
    title: str,
    *,
    scale: float = 1.0,
    ratio_format: str = "{:.1f}x",
    zero_baseline_format: str = "{}",
    baseline_format: str = "{:g}",
) -> None:
    x, y = bar_rows(rows, metric, scale)
    baseline = baseline_value(rows, metric) / scale
    colors = ["#A6A6A6" if value == 0 else "#D55E00" for value in x]
    bars = ax.bar([str(value) for value in x], y, color=colors, width=0.62, edgecolor="#333333", linewidth=0.6)
    ax.axhline(baseline, color="#555555", linestyle=(0, (3, 2)), linewidth=1.0)
    ax.text(
        0.02,
        0.92,
        f"N=0 baseline: {baseline_format.format(baseline)}",
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=7,
        color="#444444",
    )
    ymax = max(y) * 1.18 if max(y) > 0 else 1.0
    ax.set_ylim(0, ymax)
    raw_baseline = baseline_value(rows, metric)
    for node_count, raw_value, bar in zip(x, summary_series(rows, metric)[1], bars, strict=True):
        if node_count == 0:
            continue
        label = ratio_label(raw_value, raw_baseline, ratio_format, zero_baseline_format)
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height(),
            label,
            ha="center",
            va="bottom",
            fontsize=7,
            fontweight="bold",
        )
    ax.set_title(title)
    ax.set_xlabel("Poisoned nodes")
    ax.set_ylabel(ylabel)
    ax.grid(True, axis="y", alpha=0.22)
    ax.set_axisbelow(True)


def plot_bars(summary_rows: list[dict[str, Any]], pdf: Path, png: Path) -> None:
    import matplotlib.pyplot as plt

    set_plot_style(plt)
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.0), constrained_layout=True)
    draw_bar_metric(
        axes[0],
        summary_rows,
        "attack_probe_p95_ms",
        "Probe p95 latency (s)",
        "(a) Tail latency",
        scale=1000.0,
        ratio_format="{:.1f}x",
        baseline_format="{:.2f}s",
    )
    draw_bar_metric(
        axes[1],
        summary_rows,
        "attack_sla_gt_10s_rate",
        ">10s probe rate",
        "(b) SLA violations",
        ratio_format="{:.1f}x",
        zero_baseline_format="{:.1%}",
        baseline_format="{:.0%}",
    )
    axes[1].set_ylim(0, 1.12)
    draw_bar_metric(
        axes[2],
        summary_rows,
        "max_inferred_inflight",
        "Max inferred in-flight",
        "(c) Queue occupancy",
        ratio_format="{:.1f}x",
        baseline_format="{:.0f}",
    )
    save_figure(fig, pdf, png)


def draw_latency_distribution(
    ax: Any,
    summary_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    *,
    show_title: bool = False,
) -> None:
    node_counts = [0, 1, 2, 4]
    positions = list(range(len(node_counts)))
    colors = ["#8C8C8C", "#D55E00", "#009E73", "#CC79A7"]
    samples = [phase_latencies_seconds(probe_rows, node_count, "attack") for node_count in node_counts]
    box = ax.boxplot(
        samples,
        positions=positions,
        widths=0.48,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": "#111111", "linewidth": 1.1},
        whiskerprops={"color": "#444444", "linewidth": 0.8},
        capprops={"color": "#444444", "linewidth": 0.8},
        boxprops={"color": "#333333", "linewidth": 0.8},
    )
    for patch, color in zip(box["boxes"], colors, strict=True):
        patch.set_facecolor(color)
        patch.set_alpha(0.25)

    for position, color, latencies in zip(positions, colors, samples, strict=True):
        offsets = [((index % 7) - 3) * 0.025 for index, _ in enumerate(latencies)]
        ax.scatter(
            [position + offset for offset in offsets],
            latencies,
            s=9,
            color=color,
            alpha=0.58,
            linewidth=0,
            zorder=3,
        )

    p95_by_node = metric_by_poisoned_nodes(summary_rows, "attack_probe_p95_ms", 1000.0)
    for position, node_count in zip(positions, node_counts, strict=True):
        p95 = p95_by_node[node_count]
        ax.scatter(position, p95, marker="D", s=24, color="#111111", zorder=4)
        ax.text(position, p95 * 1.18, f"p95={p95:.1f}s", ha="center", va="bottom", fontsize=6.5)

    ax.axhline(10, color="#555555", linestyle=(0, (3, 2)), linewidth=0.8)
    ax.axhline(30, color="#777777", linestyle=(0, (1, 2)), linewidth=0.8)
    ax.text(3.42, 10.4, "10s", ha="right", va="bottom", fontsize=7, color="#444444")
    ax.text(3.42, 31.5, "30s", ha="right", va="bottom", fontsize=7, color="#555555")
    ax.set_xlabel("Poisoned nodes")
    ax.set_ylabel("Attack-window latency (s)")
    ax.set_xticks(positions)
    ax.set_xticklabels([str(value) for value in node_counts])
    ax.set_yscale("log")
    ax.set_ylim(0.35, 180)
    ax.set_yticks([0.5, 1, 10, 30, 100])
    ax.set_yticklabels(["0.5", "1", "10", "30", "100"])
    ax.grid(True, axis="y", which="both", alpha=0.22)
    if show_title:
        ax.set_title("(d) Latency distribution")


def plot_timeline(summary_rows: list[dict[str, Any]], probe_rows: list[dict[str, Any]], pdf: Path, png: Path) -> None:
    import matplotlib.pyplot as plt

    set_plot_style(plt)
    fig, ax = plt.subplots(1, 1, figsize=(3.35, 2.35), constrained_layout=True)
    draw_latency_distribution(ax, summary_rows, probe_rows)
    save_figure(fig, pdf, png)


def set_plot_style(plt: Any) -> None:
    plt.rcParams.update(
        {
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "legend.fontsize": 7,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def save_figure(fig: Any, pdf: Path, png: Path) -> None:
    pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, dpi=220, bbox_inches="tight")
    import matplotlib.pyplot as plt

    plt.close(fig)


def plot(summary_rows: list[dict[str, Any]], probe_rows: list[dict[str, Any]], pdf: Path, png: Path) -> None:
    import matplotlib.pyplot as plt

    set_plot_style(plt)
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 4.2), constrained_layout=True)
    draw_metric(axes[0, 0], summary_rows, "attack_probe_p95_ms", "Probe p95 latency (s)", 1000.0)
    axes[0, 0].set_title("(a) Benign p95 latency")
    draw_metric(axes[0, 1], summary_rows, "attack_sla_gt_10s_rate", "SLA violation rate")
    axes[0, 1].set_ylim(0, 1.05)
    axes[0, 1].set_title("(b) Probe latency >10s")
    draw_metric(axes[1, 0], summary_rows, "max_inferred_inflight", "Max inferred in-flight")
    axes[1, 0].set_title("(c) Queue occupancy")

    draw_latency_distribution(axes[1, 1], summary_rows, probe_rows, show_title=True)

    save_figure(fig, pdf, png)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=SUMMARY)
    parser.add_argument("--probes", type=Path, default=PROBES)
    parser.add_argument("--pdf", type=Path, default=PDF)
    parser.add_argument("--png", type=Path, default=PNG)
    parser.add_argument("--bars-pdf", type=Path, default=BARS_PDF)
    parser.add_argument("--bars-png", type=Path, default=BARS_PNG)
    parser.add_argument("--timeline-pdf", type=Path, default=TIMELINE_PDF)
    parser.add_argument("--timeline-png", type=Path, default=TIMELINE_PNG)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary_rows = load_rows(args.summary)
    probe_rows = load_rows(args.probes)
    plot(summary_rows, probe_rows, args.pdf, args.png)
    plot_bars(summary_rows, args.bars_pdf, args.bars_png)
    plot_timeline(summary_rows, probe_rows, args.timeline_pdf, args.timeline_png)


if __name__ == "__main__":
    main()
