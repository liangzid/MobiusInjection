# Plan A CodeAgent Backend Comparison

Task: `DataDog__integrations-core-1583`; agent: `opencode`; injection: `CODING_AGENT_TEMPLATE_V10_LOOP`.

| backend | model | duration_seconds | function_calls | native_tool_calls | persistence | skill_file_events | proxy_chat_requests_in_injection_window | recursive_loops | success |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenRouter | openrouter/qwen/qwen3.6-plus | 198.316 | 62 | 33 | 34 | 19 |  | Yes | True |
| Local Ollama | ollama/qwen3.6:27b | 560.079 | 89 | 63 | 61 | 16 | 34 | Yes | True |

Notes:
- OpenRouter and local Ollama are different backends/models, so this is a practical backend comparison, not a controlled same-model ablation.
- The local Ollama run gives request-level timing through the proxy logger; the OpenRouter run does not have equivalent proxy telemetry.
- Local Ollama injection-window proxy chat requests: `34`.
