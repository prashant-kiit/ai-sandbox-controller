# CURRENT — always overwritten

The single-file resumability anchor. Read this first when resuming a cold
session; it plus `docs/implementation-plan.md`'s milestone table is enough
to know exactly where the build stands without re-reading history.

- **active_milestone**: 7 (done)
- **iteration**: 7
- **last_gate**: G4 Verify — APPROVE (fresh subagent, milestone 7 diff vs. design-guide.md Step 10 + invariants.md; ran the milestone's test, checked for the snapshot-image leak directly, and re-ran the full suite)
- **last_action**: Milestone 7 (snapshot & restore) built and committed, no divergence from the guide. `sandbox/manager.py` gains `SnapshotRequest`, `snapshot_vm` (`container.commit` into `sandbox-snapshot:<tag>`), `restore_vm` (remove old container, run fresh one from that image under the same `vm_id`). `sandbox/client.py` gains matching `snapshot`/`restore` methods. `tests/test_manager_snapshot_restore.py` reproduces the guide's bug-then-restore scenario as a real assertion, with a dedicated `snapshot_tag` fixture that removes the `sandbox-snapshot:<tag>` Docker image via the SDK in teardown (the `vm` fixture only ever cleans up the container, so this specifically closes the leak the guide's own manual test has). G2: `pytest tests/test_manager_snapshot_restore.py -v` → 1 passed; full suite → 13 passed, no regressions; `docker images | grep sandbox-snapshot` confirmed empty after the run. G3: invariants 2, 6, 7 checked, no violations (invariant 5's `SANDBOX_RUNTIME_OPTS` isn't due until milestone 9, so `restore_vm` correctly has no resource limits yet). G4: fresh subagent independently re-ran the test, checked for the image leak directly, and re-ran the full suite — APPROVE. Committed as `7181c20`.
- **next_action**: run G0 existence pre-flight on milestone 8 (full agent loop + run.py — Step 11), then L1 BUILD. This is where the OpenAI message-shape divergence documented in decisions.md's "Provider pivot" amendment actually gets implemented (tool_calls, tool_call_id, JSON-string arguments needing `json.loads`) — no new pytest here per the plan (nondeterministic/token-costly), verified manually instead via `uvicorn` + `python3 run.py`.
- **model**: whatever is running this session (no cheap/flagship split).
- **blockers**: none currently. Docker confirmed running; `OPENAI_API_KEY` confirmed working in `.env`; `ai-sandbox:latest` image built and cached locally.
