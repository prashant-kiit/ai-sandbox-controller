# CURRENT — always overwritten

The single-file resumability anchor. Read this first when resuming a cold
session; it plus `docs/implementation-plan.md`'s milestone table is enough
to know exactly where the build stands without re-reading history.

- **active_milestone**: 2 (done)
- **iteration**: 2
- **last_gate**: G4 Verify — APPROVE (fresh subagent, milestone 2 diff vs. design-guide.md Step 5 + decisions.md's "Provider pivot" amendment + invariants.md)
- **last_action**: Milestone 2 (agent core loop, no tools) built and committed. Mid-milestone, the Anthropic account hit two unfixable account-side blockers on the real API call (workspace-scoping, then insufficient credit); user directed a pivot to OpenAI. Recorded as a dated amendment in `docs/decisions.md` ("Provider pivot"), updated `.harness/invariants.md` (invariants 2, 4, 7) and `docs/implementation-plan.md` (milestones 2/3/8 build-order text, pytest suite section, commit list, verification section, critical files) accordingly — `docs/design-guide.md` itself untouched (locked input). Implemented `agent/llm_client.py` (OpenAI SDK, `OPENAI_API_KEY`, `OPENAI_MODEL` env var with `gpt-4o` fallback, resolved in exactly one place) and `agent/agent.py` v1 (no hardcoded model default, OpenAI response shape). Swapped `anthropic`→`openai` in `requirements.txt` via real `pip freeze`. G2 demo command (`python3 -m agent.agent`) passed with a real reply; env-var override confirmed both directions. G3: invariants 4, 6, 8 checked, no violations. G4: fresh subagent APPROVE. Committed as `b181fdd`.
- **next_action**: run G0 existence pre-flight on milestone 3 (tool schema — Step 6, OpenAI function-calling envelope per the provider-pivot amendment), then L1 BUILD.
- **model**: whatever is running this session (no cheap/flagship split).
- **blockers**: none currently. Docker confirmed running; `OPENAI_API_KEY` confirmed working in `.env` (loaded via `set -a; source .env; set +a` each shell invocation, since shell state doesn't persist between tool calls).
