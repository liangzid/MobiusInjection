#!/usr/bin/env python3
"""Render the targeted Mobius 4x4 TSR/P-ASR heatmap as SVG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROFILES = ["E1", "E2", "E3", "E4"]


def color(value: float) -> str:
    value = max(0.0, min(1.0, value))
    # White to deep blue.
    r = int(247 - 210 * value)
    g = int(251 - 157 * value)
    b = int(255 - 42 * value)
    return f"#{r:02x}{g:02x}{b:02x}"


def cell_text(value: float) -> str:
    return f"{value * 100:.0f}%"


def draw_panel(metric: str, title: str, x0: int, y0: int, matrix: dict) -> list[str]:
    cell = 58
    label_w = 74
    lines = [
        f'<text x="{x0 + label_w + cell * 2}" y="{y0}" text-anchor="middle" font-size="16" font-weight="700">{title}</text>'
    ]
    for col, env in enumerate(PROFILES):
        x = x0 + label_w + col * cell + cell / 2
        lines.append(f'<text x="{x}" y="{y0 + 28}" text-anchor="middle" font-size="12">{env}</text>')
    for row, target in enumerate(PROFILES):
        y = y0 + 40 + row * cell
        lines.append(f'<text x="{x0 + label_w - 10}" y="{y + 35}" text-anchor="end" font-size="12">{target}</text>')
        for col, env in enumerate(PROFILES):
            x = x0 + label_w + col * cell
            value = float(matrix[target][env][metric])
            lines.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{color(value)}" stroke="#ffffff" stroke-width="2"/>'
            )
            lines.append(
                f'<text x="{x + cell / 2}" y="{y + 35}" text-anchor="middle" font-size="13" font-weight="600">{cell_text(value)}</text>'
            )
    lines.append(f'<text x="{x0 + label_w + cell * 2}" y="{y0 + 290}" text-anchor="middle" font-size="12">Actual environment</text>')
    lines.append(
        f'<text x="{x0 + 12}" y="{y0 + 160}" text-anchor="middle" font-size="12" transform="rotate(-90 {x0 + 12} {y0 + 160})">Injected target</text>'
    )
    return lines


def render(summary: dict) -> str:
    matrix = summary["matrix"]
    width = 760
    height = 360
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial, Helvetica, sans-serif; fill:#111827;}</style>',
    ]
    lines.extend(draw_panel("tsr", "Task Success Rate", 28, 34, matrix))
    lines.extend(draw_panel("p_asr", "P-ASR", 398, 34, matrix))
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("metrics_json", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    summary = json.loads(args.metrics_json.read_text(encoding="utf-8"))
    out = args.out or args.metrics_json.with_suffix(".svg")
    out.write_text(render(summary), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
