from experiments.AgentCallInterface.coding_evaluation.prompt_composer import (
    DEFAULT_DELIMITER,
    compose_benchmark_injection_prompt,
)


def test_prompt_composer_places_task_before_injection():
    task_prompt = "def solve():\n    pass\n"
    injection_prompt = "TEMPLATE_V3 basic injection text"

    result = compose_benchmark_injection_prompt(task_prompt, injection_prompt)

    assert result.combined_prompt.index(task_prompt) < result.combined_prompt.index(
        injection_prompt
    )
    assert DEFAULT_DELIMITER == "\n\n"
    assert "BEGIN TEMPLATE_V3" not in result.combined_prompt
    assert "INJECTION PROMPT" not in result.combined_prompt
    assert result.combined_prompt.startswith(task_prompt)
    assert result.combined_prompt.endswith(injection_prompt)


def test_prompt_composer_preserves_original_prompt_contents():
    task_prompt = '"""HumanEval docstring"""\n'
    injection_prompt = "Do not rewrite this TEMPLATE_V3 payload."

    result = compose_benchmark_injection_prompt(task_prompt, injection_prompt)

    assert task_prompt in result.combined_prompt
    assert injection_prompt in result.combined_prompt


def test_prompt_composer_records_lengths():
    task_prompt = "abc"
    injection_prompt = "defgh"

    result = compose_benchmark_injection_prompt(task_prompt, injection_prompt)

    assert result.metadata["task_prompt_length"] == 3
    assert result.metadata["injection_prompt_length"] == 5
    assert result.metadata["combined_prompt_length"] == len(result.combined_prompt)
    assert result.metadata["order"] == "task_before_injection"
