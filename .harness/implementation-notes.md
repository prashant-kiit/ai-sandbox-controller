# Implementation notes — rolling status

Append-only where noted. This is the "what's actually built and live"
record — `docs/implementation-plan.md`'s milestone table tracks Status
per milestone; this file tracks the narrative behind status changes.

## Status

Milestone 6 of 10 done. Project scaffold, dependencies, agent core loop
(OpenAI-based, post-pivot), tool schema, sandbox manager lifecycle, port
publishing, and command/file endpoints + client + executor committed.

## What is actually built & live

| Capability | Location | Status | Verified by |
|---|---|---|---|
| Package inits (`agent/`, `tools/`, `sandbox/`) | `agent/__init__.py`, `tools/__init__.py`, `sandbox/__init__.py` | done | `pip list` demo command + G4 subagent APPROVE |
| Pinned dependencies (resolved for Python 3.13.5) | `requirements.txt` | done | `pip list` demo command + G4 subagent APPROVE |
| Agent core loop (OpenAI, no tools yet) | `agent/llm_client.py`, `agent/agent.py` | done | `python3 -m agent.agent` real API call + G4 subagent APPROVE |
| Tool schema (OpenAI function-calling envelope) | `tools/schema.py` | done | `pytest tests/test_schema.py -v` + G4 subagent APPROVE |
| Sandbox manager lifecycle (create/list/delete/health) + base Docker image | `sandbox/Dockerfile`, `sandbox/manager.py` | done | `pytest tests/test_manager_lifecycle.py -v` (4 passed) + G4 subagent APPROVE |
| Self-sufficient pytest fixtures (Docker/API-key preconditions, image build, manager subprocess, per-test vm) | `tests/conftest.py` | done | Same test run + G4 subagent re-ran suite independently |
| Port publishing (`publish_port` -> `host_port` on `create_vm`) | `sandbox/manager.py` | done | `pytest tests/test_manager_lifecycle.py -v` (6 passed) + manual curl/http.server end-to-end check + G4 subagent APPROVE |
| Command/file endpoints (`run_command`, `write_file`, `read_file`) + `SandboxClient` + `ToolExecutor` | `sandbox/manager.py`, `sandbox/client.py`, `tools/executor.py` | done | `pytest tests/test_manager_commands_and_files.py -v` (5 passed) + full suite 12 passed + G4 subagent APPROVE |

## Deviations from plan (append-only)

| Date | Milestone | Planned approach | Actual approach | Reason | Invariant impact |
|---|---|---|---|---|---|
| 2026-09-11 | 1 | decisions.md: install unpinned then freeze resolved versions | Did exactly this — `pip install <unpinned deps>` then `pip freeze > requirements.txt` | Matches plan, no deviation from the plan itself | None — satisfies invariant 8 |
| 2026-09-11 | 2 | design-guide.md Step 5 + decisions.md's original `ANTHROPIC_MODEL`/`claude-sonnet-5` deviation | Switched LLM provider to OpenAI mid-milestone: `openai` SDK, `OPENAI_API_KEY`, `OPENAI_MODEL` env var falling back to `gpt-4o` | Anthropic account hit two unfixable account-side blockers on the real API call (workspace-scoping needed a header the guide's SDK call doesn't send; then, after swapping to a workspace-scoped key, insufficient account credit). User directed the OpenAI pivot rather than waiting on the Anthropic account. Documented as a dated amendment in decisions.md's "Provider pivot" section. | Invariant 4 rewritten for `OPENAI_MODEL`/`gpt-4o`; invariant 2 generalized (`openai`, not `anthropic`); invariant 7 updated (OpenAI API, not Anthropic). Milestones 3 (tool schema envelope) and 8 (agent-loop message shape) will need OpenAI-shaped code when reached — flagged in their `docs/implementation-plan.md` build-order entries now. |

## Known gaps & ordered next list

1. Run G0 + L1 BUILD on milestone 7 (snapshot & restore — Step 10). No divergence expected. Remember the plan's explicit note: test teardown must remove the `sandbox-snapshot:<tag>` image via the Docker SDK, not just the container — the guide's own manual test leaks this image.
2. When milestone 8 (Step 11, full ReAct loop) is reached, remember the message-shape divergence already documented in decisions.md and implementation-plan.md (tool_calls, tool_call_id, JSON-string arguments needing `json.loads`).
3. `tests/conftest.py`'s `vm` fixture is intentionally raw-HTTP-based (not `SandboxClient`) since its freeze boundary is milestone 4 only — this is fine; milestone 6's own tests instantiate `SandboxClient` directly where needed instead of changing the shared fixture.

## Session log (append-only, newest first)

- 2026-09-11 — Milestone 6 (command/file endpoints + client + executor) built, verified (G4 APPROVE — the verify subagent independently re-ran both the milestone's tests and the full suite), and committed as `1f280cc`. No divergence from the guide — `sandbox/client.py` and `tools/executor.py` are provider-agnostic, unaffected by the OpenAI pivot. `run_command`/`write_file`/`read_file` added to the manager; `SandboxClient` and `ToolExecutor` introduced exactly per guide. `pytest tests/test_manager_commands_and_files.py -v` → 5 passed; full suite → 12 passed, no regressions.
- 2026-09-11 — Milestone 5 (storage/networking + port publishing) built, verified (G4 APPROVE — the verify subagent independently re-ran both pytest and the guide's own manual curl/http.server check), and committed as `4af37df`. No divergence from the guide. `create_vm` gains `publish_port`/`host_port`; two new pytest cases added to `tests/test_manager_lifecycle.py` (6 passed total). Manual end-to-end check confirmed real host→NAT→bridge→sandbox port routing (curled a real HTML directory listing back from a container-internal `http.server`).
- 2026-09-11 — Milestone 4 (sandbox manager lifecycle + Dockerfile) built, verified (G4 APPROVE — the verify subagent re-ran the test suite itself), and committed as `e6c0ac0`. No divergence from the guide (sandbox layer never touches an LLM SDK). `tests/conftest.py` introduced as the one-shot, self-sufficient fixture file for the rest of the suite (fail-loud Docker/API-key preconditions, auto image build, manager subprocess with health polling, per-test `vm` fixture). `pytest tests/test_manager_lifecycle.py -v` → 4 passed (first run built `ai-sandbox:latest` in ~2m15s; reruns ~1.5s). No leftover containers after any run.
- 2026-09-11 — Milestone 3 (tool schema) built, verified (G4 APPROVE), and committed as `cf1ff21`. Same three tools/descriptions/parameters as the guide, wrapped in OpenAI's function-calling envelope per the milestone-2 provider pivot. `pytest tests/test_schema.py -v` → 1 passed.
- 2026-09-11 — Milestone 2 (agent core loop) built, verified (G4 APPROVE), and committed as `b181fdd`, after a mid-milestone provider pivot from Anthropic to OpenAI (Anthropic account: workspace-scoping error, then insufficient credit — both account-side, not code bugs). `docs/decisions.md`, `.harness/invariants.md`, and `docs/implementation-plan.md` updated to record the pivot and its downstream impact on milestones 3 and 8; `docs/design-guide.md` left untouched as the locked original spec. Real end-to-end call confirmed (`[agent] Hello! I can assist you with information, advice, and problem-solving across a wide range of topics.`); `OPENAI_MODEL` env-var override confirmed both directions.
- 2026-09-11 — Milestone 1 (project scaffold, deps) built, verified (G4 APPROVE), and committed as `2299b7c`. `requirements.txt` is a real `pip freeze` against Python 3.13.5 (fastapi 0.141.1, uvicorn 0.52.4, docker 7.2.0, requests 2.34.2, anthropic 1.5.0, pydantic 2.13.5, pytest 9.1.1 — plus transitive deps), not the guide's pre-3.13 pins. Docker Desktop started and confirmed ready (`docker ps` returns a header) ahead of milestone 2.
- 2026-09-11 — Harness built: `.harness/{LOOPS.md, CURRENT.md, invariants.md, implementation-notes.md}` and `.claude/skills/sandbox-harness/SKILL.md` created; `docs/implementation-plan.md` restructured with a milestone table. No build commits yet.
