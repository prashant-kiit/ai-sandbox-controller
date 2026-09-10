# CURRENT — always overwritten

The single-file resumability anchor. Read this first when resuming a cold
session; it plus `docs/implementation-plan.md`'s milestone table is enough
to know exactly where the build stands without re-reading history.

- **active_milestone**: 5 (done)
- **iteration**: 5
- **last_gate**: G4 Verify — APPROVE (fresh subagent, milestone 5 diff vs. design-guide.md Step 8 + invariants.md; ran pytest AND the guide's own manual curl/http.server end-to-end check itself)
- **last_action**: Milestone 5 (storage/networking + port publishing) built and committed, no divergence from the guide. `create_vm` in `sandbox/manager.py` gains `publish_port: Optional[int] = None`, returning `host_port` (Docker `ports={}` kwarg + `container.reload()` + `container.ports` lookup). Added `test_create_vm_with_publish_port` and `test_create_vm_without_publish_port_has_no_host_port` to `tests/test_manager_lifecycle.py`. G2: `pytest tests/test_manager_lifecycle.py -v` → 6 passed; plus a manual curl check (create VM with `publish_port=8080`, ran `python3 -m http.server 8080` inside via `docker exec`, curled the assigned host port from outside) → real HTML directory listing came back, confirming host→NAT→bridge→sandbox routing. G3: invariants 2, 6, 7 checked, no violations. G4: fresh subagent independently re-ran both pytest and the manual curl/http.server check — APPROVE. Committed as `4af37df`.
- **next_action**: run G0 existence pre-flight on milestone 6 (command/file endpoints + client + executor — Step 9, OpenAI-shaped where relevant), then L1 BUILD. Docker already confirmed running.
- **model**: whatever is running this session (no cheap/flagship split).
- **blockers**: none currently. Docker confirmed running; `OPENAI_API_KEY` confirmed working in `.env`; `ai-sandbox:latest` image built and cached locally.
