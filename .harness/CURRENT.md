# CURRENT — always overwritten

The single-file resumability anchor. Read this first when resuming a cold
session; it plus `docs/implementation-plan.md`'s milestone table is enough
to know exactly where the build stands without re-reading history.

- **active_milestone**: 6 (done)
- **iteration**: 6
- **last_gate**: G4 Verify — APPROVE (fresh subagent, milestone 6 diff vs. design-guide.md Step 9 + invariants.md; ran the milestone's tests AND the full suite itself)
- **last_action**: Milestone 6 (command/file endpoints + client + executor) built and committed, no divergence from the guide — `sandbox/client.py` and `tools/executor.py` are provider-agnostic per decisions.md's "Provider pivot" amendment, so the OpenAI switch doesn't reach them. `sandbox/manager.py` gains `run_command` (docker exec, demuxed stdout/stderr), `write_file`/`read_file` (tar stream via put_archive/get_archive). `sandbox/client.py`: `SandboxClient` with hardcoded `http://localhost:8000` default. `tools/executor.py`: `ToolExecutor.execute` dispatch table, only calls `SandboxClient` methods (invariant 3). `tests/test_manager_commands_and_files.py` covers run_command stdout/exit code (zero and nonzero), write→read round trip, missing-file 404, and one test through `ToolExecutor` rather than raw HTTP. G2: `pytest tests/test_manager_commands_and_files.py -v` → 5 passed; full suite `pytest -v` → 12 passed, no regressions. G3: invariants 2, 3, 6, 7 checked, no violations. G4: fresh subagent independently re-ran both the milestone tests and the full suite — APPROVE. Committed as `1f280cc`.
- **next_action**: run G0 existence pre-flight on milestone 7 (snapshot & restore — Step 10), then L1 BUILD. No divergence expected; watch for the image-leak note in the plan (teardown must remove the `sandbox-snapshot:<tag>` image via the Docker SDK, not just the container).
- **model**: whatever is running this session (no cheap/flagship split).
- **blockers**: none currently. Docker confirmed running; `OPENAI_API_KEY` confirmed working in `.env`; `ai-sandbox:latest` image built and cached locally.
