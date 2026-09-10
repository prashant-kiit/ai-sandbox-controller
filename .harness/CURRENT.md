# CURRENT — always overwritten

The single-file resumability anchor. Read this first when resuming a cold
session; it plus `docs/implementation-plan.md`'s milestone table is enough
to know exactly where the build stands without re-reading history.

- **active_milestone**: 4 (done)
- **iteration**: 4
- **last_gate**: G4 Verify — APPROVE (fresh subagent, milestone 4 diff vs. design-guide.md Step 7 + invariants.md; ran the real test suite itself)
- **last_action**: Milestone 4 (sandbox manager lifecycle + Dockerfile) built and committed, no divergence from the guide (sandbox layer never touches an LLM SDK, so the provider pivot doesn't affect it). Implemented `sandbox/Dockerfile` (Ubuntu 22.04 + python3/node/curl/wget/git, `sleep infinity`) and `sandbox/manager.py` v1 (`create_vm`, `list_vms`, `delete_vm`, `health`, Docker SDK-backed, `managed-by` label). Introduced `tests/conftest.py` — its freeze boundary is this milestone only, so it's built self-sufficient for every future test file: fail-loud preconditions (real Docker ping + `OPENAI_API_KEY` presence, no `pytest.skip` anywhere), builds `ai-sandbox:latest` if missing, spawns `uvicorn` as a subprocess polling `/health` with a hard timeout, and a per-test `vm` fixture using raw `requests` (since `sandbox/client.py` doesn't exist until milestone 6). `tests/test_manager_lifecycle.py` covers create/list/delete/health/404. G2 demo command (`pytest tests/test_manager_lifecycle.py -v`) passed (4 passed; first run built the image in ~2m15s, verify subagent's rerun was 1.46s). G3: invariants 2, 6, 7 checked, no violations. G4: fresh subagent APPROVE (it re-ran the suite itself and confirmed no leftover containers). Committed as `e6c0ac0`.
- **next_action**: run G0 existence pre-flight on milestone 5 (storage/networking + port publishing — Step 8), then L1 BUILD. Docker already confirmed running; no new LLM API calls needed for this milestone.
- **model**: whatever is running this session (no cheap/flagship split).
- **blockers**: none currently. Docker confirmed running; `OPENAI_API_KEY` confirmed working in `.env`; `ai-sandbox:latest` image built and cached locally.
