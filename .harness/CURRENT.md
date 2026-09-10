# CURRENT — always overwritten

The single-file resumability anchor. Read this first when resuming a cold
session; it plus `docs/implementation-plan.md`'s milestone table is enough
to know exactly where the build stands without re-reading history.

- **active_milestone**: 8 (done)
- **iteration**: 8
- **last_gate**: G4 Verify — APPROVE (fresh subagent, milestone 8 diff vs. design-guide.md Step 11 + decisions.md's "Provider pivot" amendment + invariants.md; ran the real end-to-end demo itself)
- **last_action**: Milestone 8 (full agent loop + run.py) built and committed. `agent/agent.py`'s final ReAct loop implements the OpenAI-shape divergence documented since milestone 2: reads `response.choices[0].message.tool_calls` instead of filtering `response.content` for `tool_use` blocks; appends tool results as `{"role": "tool", "tool_call_id": ..., "content": ...}` instead of a `tool_result` content block; `json.loads`s each `tool_call.function.arguments` before `ToolExecutor.execute`. `Agent.__init__` keeps `model: str | None = None`, no hardcoded default (invariant 4), and still never imports `docker` directly (invariant 1). `run.py` unchanged in shape from the guide. G2: real end-to-end run — `uvicorn sandbox.manager:app --port 8000` + `python3 run.py` — produced a full clean trace (sandbox ready → write_file → run_command showing `Hello from the sandbox!` → final answer → sandbox destroyed), no traceback, no leftover containers. No new pytest for this milestone per decisions.md's scope (would be nondeterministic/token-costly); full suite re-run (13 passed) confirmed no regressions anyway since this milestone doesn't touch `sandbox/`/`tests/`. G3: invariants 1, 4, 6 checked, no violations. G4: fresh subagent independently re-ran the real end-to-end demo itself — APPROVE. Committed as `438d120`.
- **next_action**: run G0 existence pre-flight on milestone 9 (security hardening + scaling notes — Steps 12-13), then L1 BUILD. `SANDBOX_RUNTIME_OPTS` must be applied to BOTH `create_vm` and `restore_vm` — the guide's own Step 10 snippet only had it on the first; don't repeat that omission (invariant 5).
- **model**: whatever is running this session (no cheap/flagship split).
- **blockers**: none currently. Docker confirmed running; `OPENAI_API_KEY` confirmed working in `.env`; `ai-sandbox:latest` image built and cached locally.
