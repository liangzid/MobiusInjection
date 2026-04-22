"""Compose benchmark tasks with Mobius injection prompts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DEFAULT_DELIMITER = "\n\n----- BEGIN TEMPLATE_V3 BASIC INJECTION PROMPT -----\n\n"
SUPPORTED_ORDER = "task_before_injection"


@dataclass(frozen=True)
class PromptComposition:
    combined_prompt: str
    metadata: dict[str, Any]


def compose_benchmark_injection_prompt(
    task_prompt: str,
    injection_prompt: str,
    order: str = SUPPORTED_ORDER,
    delimiter: str = DEFAULT_DELIMITER,
) -> PromptComposition:
    if order != SUPPORTED_ORDER:
        raise ValueError(f"Unsupported prompt order: {order}")
    combined_prompt = f"{task_prompt}{delimiter}{injection_prompt}"
    metadata = {
        "order": order,
        "delimiter": delimiter,
        "task_prompt_length": len(task_prompt),
        "injection_prompt_length": len(injection_prompt),
        "combined_prompt_length": len(combined_prompt),
    }
    return PromptComposition(combined_prompt=combined_prompt, metadata=metadata)
