from pathlib import Path


WRAPPER = (
    Path(__file__).resolve().parents[3]
    / "experiments/scripts/coding_agents/run_edit_skill_evaluation_humaneval_benchmark.sh"
)


def test_edit_skill_wrapper_forwards_swebench_dataset_type() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert 'SWEBENCH_DATASET_TYPE="${SWEBENCH_DATASET_TYPE:-verified_mini}"' in text
    assert '--dataset-type "$SWEBENCH_DATASET_TYPE"' in text
