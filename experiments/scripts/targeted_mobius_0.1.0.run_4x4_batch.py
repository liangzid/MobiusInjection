#!/usr/bin/env python3
"""Batch entrypoint for the targeted Mobius 4x4 matrix.

This intentionally delegates to the new smoke runner implementation while
setting paper-oriented defaults. It does not call any previous untargeted
experiment runner.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SMOKE_RUNNER = Path(__file__).with_name("targeted_mobius_0.0.1.run_4x4_smoke.py")


def main() -> int:
    argv = sys.argv[1:]
    if not any(arg == "--repeats" or arg.startswith("--repeats=") for arg in argv):
        argv = ["--repeats", "3", *argv]
    cmd = [sys.executable, str(SMOKE_RUNNER), *argv]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
