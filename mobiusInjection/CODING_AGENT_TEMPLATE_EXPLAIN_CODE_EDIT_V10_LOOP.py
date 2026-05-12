"""Agent-specific explain-code loop prompt selector."""

from __future__ import annotations

from mobiusInjection.CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT import _normalize_agent_name
from mobiusInjection.CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V7_LOOP import (
    MainInjectionTextTargeted as _V7MainInjectionTextTargeted,
)
from mobiusInjection.CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V8_LOOP import (
    FOLLOWUP_STATUS_PASSES,
    MAIN_STATUS_PASSES,
)
from mobiusInjection.CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V8_LOOP import (
    MainInjectionTextTargeted as _V8MainInjectionTextTargeted,
)


def MainInjectionTextTargeted(target_agent: str = "", target_model: str = "") -> str:
    if _normalize_agent_name(target_agent) == "claude_code":
        return _V7MainInjectionTextTargeted(
            target_agent=target_agent,
            target_model=target_model,
        )
    return _V8MainInjectionTextTargeted(
        target_agent=target_agent,
        target_model=target_model,
    )
