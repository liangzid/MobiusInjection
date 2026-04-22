"""Apply compact raw-log retention for benchmark runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


KEEP_POLICIES = {"compact", "keep_all", "aggregate_only"}
RAW_KEYS = ("output_file", "followup_file", "injection_file", "log_file")


def apply_log_retention(
    run_dir: str | Path,
    manifest_path: str | Path | None = None,
    policy: str = "compact",
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    if policy not in KEEP_POLICIES:
        raise ValueError(f"Unsupported log policy: {policy}")
    entries = _read_manifest(Path(run_dir), manifest_path)
    decisions = []
    for entry in entries:
        decision = _entry_decision(entry, policy)
        decisions.append(decision)
        if not dry_run:
            _apply_decision(decision)
    return decisions


def _read_manifest(run_dir: Path, manifest_path: str | Path | None) -> list[dict[str, Any]]:
    path = Path(manifest_path) if manifest_path else run_dir / "manifest.json"
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _entry_decision(entry: dict[str, Any], policy: str) -> dict[str, Any]:
    analysis = _read_json(entry.get("analysis_file"))
    metrics = _read_json(entry.get("metrics_file"))
    keep_raw = _keep_raw(policy, analysis, metrics)
    raw_files = _raw_files(entry)
    return {
        "benchmark_id": entry.get("benchmark_id", ""),
        "keep_raw": keep_raw,
        "raw_files": [str(path) for path in raw_files],
        "delete_files": [] if keep_raw else [str(path) for path in raw_files],
    }


def _keep_raw(
    policy: str,
    analysis: dict[str, Any] | None,
    metrics: dict[str, Any] | None,
) -> bool:
    if policy == "keep_all":
        return True
    if policy == "aggregate_only":
        return False
    if analysis is None or metrics is None:
        return True
    indicators = _merged_indicators(analysis, metrics)
    counters = _merged_counters(analysis, metrics)
    return any(
        [
            not indicators.get("runner_succeeded", False),
            indicators.get("active_after_timeout", False),
            indicators.get("runtime_failure_detected", False),
            indicators.get("skill_injected", False),
            indicators.get("skills_visible_post", False),
            int(counters.get("persistence_markers", 0) or 0) > 0,
            indicators.get("recursive_triggered", False),
        ]
    )


def _merged_indicators(
    analysis: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    indicators = dict(metrics.get("indicators", {}))
    indicators.update(analysis.get("indicators", {}))
    return indicators


def _merged_counters(
    analysis: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    counters = dict(metrics.get("counters", {}))
    counters.update(analysis.get("counters", {}))
    return counters


def _read_json(path_value: str | None) -> dict[str, Any] | None:
    if not path_value:
        return None
    path = Path(path_value)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _raw_files(entry: dict[str, Any]) -> list[Path]:
    files = [Path(entry[key]) for key in RAW_KEYS if entry.get(key)]
    files.extend(_state_files(entry))
    return [path for path in files if path.exists()]


def _state_files(entry: dict[str, Any]) -> list[Path]:
    output_file = entry.get("output_file")
    if not output_file:
        return []
    prefix = Path(output_file).name.removesuffix("_output.txt")
    return sorted(Path(output_file).parent.glob(f"{prefix}_*_state.txt"))


def _apply_decision(decision: dict[str, Any]) -> None:
    for raw_path in decision["delete_files"]:
        Path(raw_path).unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--manifest")
    parser.add_argument("--policy", default="compact", choices=sorted(KEEP_POLICIES))
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    decisions = apply_log_retention(
        args.run_dir,
        manifest_path=args.manifest,
        policy=args.policy,
        dry_run=args.dry_run,
    )
    print(json.dumps(decisions, indent=2))


if __name__ == "__main__":
    main()
