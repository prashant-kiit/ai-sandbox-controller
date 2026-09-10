# CURRENT — always overwritten

The single-file resumability anchor. Read this first when resuming a cold
session; it plus `docs/implementation-plan.md`'s milestone table is enough
to know exactly where the build stands without re-reading history.

- **active_milestone**: 3 (done)
- **iteration**: 3
- **last_gate**: G4 Verify — APPROVE (fresh subagent, milestone 3 diff vs. design-guide.md Step 6 + decisions.md's "Provider pivot" amendment + invariants.md)
- **last_action**: Milestone 3 (tool schema) built and committed. G1 read design-guide.md Step 6 + decisions.md's provider-pivot amendment (OpenAI function-calling envelope). Implemented `tools/schema.py` with the same three tools (`run_command`, `write_file`, `read_file`) — identical names/descriptions/parameter schemas to the guide — wrapped in `{"type": "function", "function": {...}}` instead of Anthropic's flat `{"name", "description", "input_schema"}` shape. Introduced `tests/` (`__init__.py`, `test_schema.py::test_tools_schema_shape`) checking the OpenAI envelope. G2 demo command (`pytest tests/test_schema.py -v`) passed (1 passed). G3: invariant 6 checked, no violations. G4: fresh subagent APPROVE. Committed as `cf1ff21`.
- **next_action**: run G0 existence pre-flight on milestone 4 (sandbox manager lifecycle + Dockerfile — Step 7), then L1 BUILD. Needs Docker running (already confirmed) — no LLM API calls needed for this milestone.
- **model**: whatever is running this session (no cheap/flagship split).
- **blockers**: none currently. Docker confirmed running; `OPENAI_API_KEY` confirmed working in `.env`.
