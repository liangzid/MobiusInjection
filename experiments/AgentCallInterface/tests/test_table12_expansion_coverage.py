import importlib.util
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "experiments/scripts/report_table12_expansion_coverage.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("table12_coverage", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_keep_and_discard_paths_are_distinct() -> None:
    module = _load()
    keep_paths = {str(path) for path in module.KEEP.values()}
    discard_paths = {str(path) for path in module.DISCARD.values()}
    assert keep_paths.isdisjoint(discard_paths)
    assert "add_s_plan_a_newtasks_qwen36_20260827_run2" in str(module.KEEP["claw_add_s_new28"])
    assert "add_s_v411_openclaw_derivative_planA_kimi_20260428_201953" in str(
        module.KEEP["claw_add_s_orig11_openclaw_kimi"]
    )
    assert str(module.DISCARD["claw_add_s_new28_openclaw_401"]).endswith(
        "add_s_plan_a_newtasks_qwen36_20260827"
    )


def test_report_marks_keep_dirs() -> None:
    payload = _load().report()
    assert payload["keep"]["humaneval_add_s_first20"]["exists"] is True
    assert payload["discard"]["claw_add_s_new28_openclaw_401"]["use"] is False
    assert payload["keep"]["claw_add_s_orig11_openclaw_kimi"]["path"].endswith(
        "add_s_v411_openclaw_derivative_planA_kimi_20260428_201953"
    )
