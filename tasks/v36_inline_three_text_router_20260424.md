# V3.6 Inline Three-Text Router - 2026-04-24

## User request

Keep the three claw-agent texts inside `mobiusInjection/MI_V3.6_add_s.py`, but
make `openclaw`, `hermes`, and `zeroclaw` each own a fully written text block
instead of only being separated structurally by shared helper generation.

## Files changed

- `mobiusInjection/MI_V3.6_add_s.py`

## What I changed

1. Removed the shared `_native_skill_root_payload(...)` generator for the
   native OpenClaw/Hermes branch.
2. Rewrote `openclaw` as its own explicit full text block in
   `_openclaw_payload()`.
3. Rewrote `hermes` as its own explicit full text block in
   `_hermes_payload()`.
4. Kept `zeroclaw` as its own explicit full text block in
   `_zeroclaw_workspace_payload()`.
5. Kept everything in the same file, with no split into three files.

## Validation

Commands run:

```bash
uv run pytest experiments/AgentCallInterface/tests/test_mi_v36_add_s.py -q
python3 -m py_compile mobiusInjection/MI_V3.6_add_s.py experiments/AgentCallInterface/tests/test_mi_v36_add_s.py
```

Results:

- `9 passed in 0.02s`
- `py_compile` passed

## Internal result

`MI_V3.6_add_s.py` is now textually split the way requested:

- OpenClaw full text in one function
- Hermes full text in one function
- ZeroClaw full text in one function

All three remain routed from `MainInjectionTextTargeted(...)` inside the same
file.
