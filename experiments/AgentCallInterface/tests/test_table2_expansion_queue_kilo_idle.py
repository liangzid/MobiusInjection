from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "experiments/scripts/run_table2_expansion_queue.sh"
)


def test_table2_queue_kilo_idle_uses_docker_top_not_pgrep() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "docker top kilo_code -eo pid,comm" in text
    assert "kilo_163_ready" in text
    assert '[[ "$size" -ge 200 ]]' in text
    idle_block = text.split("kilo_idle()")[1].split("kilo_163_ready()")[0]
    assert "pgrep -f" not in idle_block
    assert "docker exec kilo_code" not in idle_block
