# Implementation notes — rolling status

Append-only where noted. This is the "what's actually built and live"
record — `docs/implementation-plan.md`'s milestone table tracks Status
per milestone; this file tracks the narrative behind status changes.

## Status

Milestone 3 of 10 done. Project scaffold, dependencies, agent core loop
(OpenAI-based, post-pivot), and tool schema committed.

## What is actually built & live

| Capability | Location | Status | Verified by |
|---|---|---|---|
| Package inits (`agent/`, `tools/`, `sandbox/`) | `agent/__init__.py`, `tools/__init__.py`, `sandbox/__init__.py` | done | `pip list` demo command + G4 subagent APPROVE |
| Pinned dependencies (resolved for Python 3.13.5) | `requirements.txt` | done | `pip list` demo command + G4 subagent APPROVE |
| Agent core loop (OpenAI, no tools yet) | `agent/llm_client.py`, `agent/agent.py` | done | `python3 -m agent.agent` real API call + G4 subagent APPROVE |
| Tool schema (OpenAI function-calling envelope) | `tools/schema.py` | done | `pytest tests/test_schema.py -v` + G4 subagent APPROVE |

## Deviations from plan (append-only)

| Date | Milestone | Planned approach | Actual approach | Reason | Invariant impact |
|---|---|---|---|---|---|
| 2026-09-11 | 1 | decisions.md: install unpinned then freeze resolved versions | Did exactly this — `pip install <unpinned deps>` then `pip freeze > requirements.txt` | Matches plan, no deviation from the plan itself | None — satisfies invariant 8 |
| 2026-09-11 | 2 | design-guide.md Step 5 + decisions.md's original `ANTHROPIC_MODEL`/`claude-sonnet-5` deviation | Switched LLM provider to OpenAI mid-milestone: `openai` SDK, `OPENAI_API_KEY`, `OPENAI_MODEL` env var falling back to `gpt-4o` | Anthropic account hit two unfixable account-side blockers on the real API call (workspace-scoping needed a header the guide's SDK call doesn't send; then, after swapping to a workspace-scoped key, insufficient account credit). User directed the OpenAI pivot rather than waiting on the Anthropic account. Documented as a dated amendment in decisions.md's "Provider pivot" section. | Invariant 4 rewritten for `OPENAI_MODEL`/`gpt-4o`; invariant 2 generalized (`openai`, not `anthropic`); invariant 7 updated (OpenAI API, not Anthropic). Milestones 3 (tool schema envelope) and 8 (agent-loop message shape) will need OpenAI-shaped code when reached — flagged in their `docs/implementation-plan.md` build-order entries now. |

## Known gaps & ordered next list

1. Run G0 + L1 BUILD on milestone 4 (sandbox manager lifecycle + Dockerfile — Step 7). No LLM API calls needed; Docker already confirmed running.
2. When milestone 8 (Step 11, full ReAct loop) is reached, remember the message-shape divergence already documented in decisions.md and implementation-plan.md (tool_calls, tool_call_id, JSON-string arguments needing `json.loads`).

## Session log (append-only, newest first)

- 2026-09-11 — Milestone 3 (tool schema) built, verified (G4 APPROVE), and committed as `cf1ff21`. Same three tools/descriptions/parameters as the guide, wrapped in OpenAI's function-calling envelope per the milestone-2 provider pivot. `pytest tests/test_schema.py -v` → 1 passed.
- 2026-09-11 — Milestone 2 (agent core loop) built, verified (G4 APPROVE), and committed as `b181fdd`, after a mid-milestone provider pivot from Anthropic to OpenAI (Anthropic account: workspace-scoping error, then insufficient credit — both account-side, not code bugs). `docs/decisions.md`, `.harness/invariants.md`, and `docs/implementation-plan.md` updated to record the pivot and its downstream impact on milestones 3 and 8; `docs/design-guide.md` left untouched as the locked original spec. Real end-to-end call confirmed (`[agent] Hello! I can assist you with information, advice, and problem-solving across a wide range of topics.`); `OPENAI_MODEL` env-var override confirmed both directions.
- 2026-09-11 — Milestone 1 (project scaffold, deps) built, verified (G4 APPROVE), and committed as `2299b7c`. `requirements.txt` is a real `pip freeze` against Python 3.13.5 (fastapi 0.141.1, uvicorn 0.52.4, docker 7.2.0, requests 2.34.2, anthropic 1.5.0, pydantic 2.13.5, pytest 9.1.1 — plus transitive deps), not the guide's pre-3.13 pins. Docker Desktop started and confirmed ready (`docker ps` returns a header) ahead of milestone 2.
- 2026-09-11 — Harness built: `.harness/{LOOPS.md, CURRENT.md, invariants.md, implementation-notes.md}` and `.claude/skills/sandbox-harness/SKILL.md` created; `docs/implementation-plan.md` restructured with a milestone table. No build commits yet.
