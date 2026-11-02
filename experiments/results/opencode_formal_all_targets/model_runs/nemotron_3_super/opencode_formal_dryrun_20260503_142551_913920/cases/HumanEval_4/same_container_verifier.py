import importlib.util
import json
import math
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SOLUTION_PATH = Path("/opencode/solution.py")
ENTRY_POINT = 'mean_absolute_deviation'
PUBLIC_TESTS = [
  {
    "name": "public_1",
    "expression": "abs(candidate([1.0, 2.0, 3.0]) - 2.0 / 3.0) < 1e-06"
  },
  {
    "name": "public_2",
    "expression": "abs(candidate([1.0, 2.0, 3.0, 4.0]) - 1.0) < 1e-06"
  },
  {
    "name": "public_3",
    "expression": "abs(candidate([1.0, 2.0, 3.0, 4.0, 5.0]) - 6.0 / 5.0) < 1e-06"
  }
]


def load_candidate():
    if not SOLUTION_PATH.exists():
        raise FileNotFoundError(str(SOLUTION_PATH))
    spec = importlib.util.spec_from_file_location("candidate_solution", SOLUTION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to create import spec for solution.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, ENTRY_POINT):
        raise AttributeError(f"missing entry point: {ENTRY_POINT}")
    return getattr(module, ENTRY_POINT)


def main() -> int:
    result = {
        "verifier_environment": "opencode-container:/opencode",
        "solution_path": str(SOLUTION_PATH),
        "entry_point": ENTRY_POINT,
        "verifier_ran": True,
        "candidate_loaded": False,
        "tests_total": len(PUBLIC_TESTS),
        "tests_passed": 0,
        "tests_failed": 0,
        "test_results": [],
        "error": None,
    }
    try:
        candidate = load_candidate()
        result["candidate_loaded"] = True
    except Exception as exc:
        result["error"] = "".join(traceback.format_exception_only(type(exc), exc)).strip()
        result["tests_failed"] = result["tests_total"]
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    namespace = {
        "candidate": candidate,
        "math": math,
        "Any": Any,
        "Dict": Dict,
        "List": List,
        "Optional": Optional,
        "Tuple": Tuple,
    }
    for test in PUBLIC_TESTS:
        item = {
            "name": test["name"],
            "expression": test["expression"],
            "passed": False,
            "error": None,
        }
        try:
            item["passed"] = bool(eval(test["expression"], namespace, namespace))
        except Exception as exc:
            item["error"] = "".join(traceback.format_exception_only(type(exc), exc)).strip()
        if item["passed"]:
            result["tests_passed"] += 1
        else:
            result["tests_failed"] += 1
        result["test_results"].append(item)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["tests_failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
