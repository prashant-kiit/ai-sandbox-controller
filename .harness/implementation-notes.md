# Implementation notes — rolling status

Append-only where noted. This is the "what's actually built and live"
record — `docs/implementation-plan.md`'s milestone table tracks Status
per milestone; this file tracks the narrative behind status changes.

## Status

Milestone 1 of 10 done. Project scaffold and dependencies committed.

## What is actually built & live

| Capability | Location | Status | Verified by |
|---|---|---|---|
| Package inits (`agent/`, `tools/`, `sandbox/`) | `agent/__init__.py`, `tools/__init__.py`, `sandbox/__init__.py` | done | `pip list` demo command + G4 subagent APPROVE |
| Pinned dependencies (resolved for Python 3.13.5) | `requirements.txt` | done | `pip list` demo command + G4 subagent APPROVE |

## Deviations from plan (append-only)

| Date | Milestone | Planned approach | Actual approach | Reason | Invariant impact |
|---|---|---|---|---|---|
| 2026-09-11 | 1 | decisions.md: install unpinned then freeze resolved versions | Did exactly this — `pip install <unpinned deps>` then `pip freeze > requirements.txt` | Matches plan, no deviation from the plan itself | None — satisfies invariant 8 |

## Known gaps & ordered next list

1. Export `ANTHROPIC_API_KEY` in this session's shell (needed for milestone 2's demo command, `python3 -m agent.agent`).
2. Run G0 + L1 BUILD on milestone 2 (agent core loop, no tools — Step 5).

## Session log (append-only, newest first)

- 2026-09-11 — Milestone 1 (project scaffold, deps) built, verified (G4 APPROVE), and committed as `2299b7c`. `requirements.txt` is a real `pip freeze` against Python 3.13.5 (fastapi 0.141.1, uvicorn 0.52.4, docker 7.2.0, requests 2.34.2, anthropic 1.5.0, pydantic 2.13.5, pytest 9.1.1 — plus transitive deps), not the guide's pre-3.13 pins. Docker Desktop started and confirmed ready (`docker ps` returns a header) ahead of milestone 2. `ANTHROPIC_API_KEY` still not confirmed in-shell.
- 2026-09-11 — Harness built: `.harness/{LOOPS.md, CURRENT.md, invariants.md, implementation-notes.md}` and `.claude/skills/sandbox-harness/SKILL.md` created; `docs/implementation-plan.md` restructured with a milestone table. No build commits yet.
