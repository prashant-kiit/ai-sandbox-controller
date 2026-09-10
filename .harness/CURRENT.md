# CURRENT — always overwritten

The single-file resumability anchor. Read this first when resuming a cold
session; it plus `docs/implementation-plan.md`'s milestone table is enough
to know exactly where the build stands without re-reading history.

- **active_milestone**: 1 (done)
- **iteration**: 1
- **last_gate**: G4 Verify — APPROVE (fresh subagent, milestone 1 diff vs. design-guide.md Step 4 + decisions.md deviations + invariants.md)
- **last_action**: Milestone 1 (project scaffold, deps) built and committed. G1 read design-guide.md Step 4 + decisions.md's flattened-layout and dependency-version deviations. Created `agent/__init__.py`, `tools/__init__.py`, `sandbox/__init__.py` (empty) at repo root; created `.venv` via `python3 -m venv .venv`; installed fastapi/uvicorn/docker/requests/anthropic/pydantic/pytest unpinned and froze resolved versions into `requirements.txt` via `pip freeze`. G2 demo command (`pip list | grep -E "fastapi|docker|anthropic|pydantic|uvicorn|pytest"`) passed with real output. G3: invariants 6 and 8 checked, no violations. G4: fresh subagent APPROVE. Committed as `2299b7c`. Docker Desktop was also started and confirmed ready (`docker ps` returns a header) ahead of milestone 2.
- **next_action**: run G0 existence pre-flight on milestone 2 (agent core loop, no tools — Step 5), then L1 BUILD. Requires `ANTHROPIC_API_KEY` exported in the shell.
- **model**: whatever is running this session (no cheap/flagship split).
- **blockers**: `ANTHROPIC_API_KEY` not yet confirmed exported in this session's shell — needed before milestone 2's demo command (`python3 -m agent.agent`) can run. Docker is no longer a blocker (confirmed running).
