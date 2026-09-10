# CURRENT — always overwritten

The single-file resumability anchor. Read this first when resuming a cold
session; it plus `docs/implementation-plan.md`'s milestone table is enough
to know exactly where the build stands without re-reading history.

- **active_milestone**: 10 (done) — ALL 10 MILESTONES COMPLETE
- **iteration**: 10
- **last_gate**: G4 Verify — APPROVE (fresh subagent, milestone 10 diff vs. design-guide.md Steps 14-16 + both decisions.md amendments + invariants.md; ran the ENTIRE verification sequence itself end-to-end)
- **last_action**: Milestone 10 (final — consolidation: demo_snapshot.py + README) built and committed. `demo_snapshot.py` is exactly per guide, no divergence in the file's code. `README.md` rewritten for the flattened layout per the plan's divergence list (no `cd ai-agent-sandbox`, explicit venv activation, `OPENAI_MODEL`/`OPENAI_API_KEY` documented, a "Tests" section, Step 17 referenced as documented-not-implemented). While running this milestone's own verification, discovered `demo_snapshot.py` failed 3/3 real runs against the `gpt-4o` default (model described the "introduce a bug" change in prose instead of calling `write_file`); surfaced to the user, who chose to switch the default. Fixed `agent/llm_client.py`'s `OPENAI_MODEL` fallback from `gpt-4o` to `gpt-5` — same script then succeeded immediately (including proactively running `ls` to find the file). Documented as a new dated "Default model amendment" in `docs/decisions.md`, updated `.harness/invariants.md` (invariant 4) and `docs/implementation-plan.md` to match, and fixed a stale Anthropic reference left over in decisions.md's Testing section from before the provider pivot. G2: full verification sequence run for real — Docker build, `pytest -v` (15 passed), manager health check (`{"status":"ok","sandboxes":0}`), `python3 run.py` (clean trace), `python3 demo_snapshot.py` (bug introduced then correctly restored, first try with gpt-5), `/vms` → `[]`, `OPENAI_MODEL` override checks (`gpt-4o-mini` / `gpt-5`) both correct. G3: invariants 1, 2, 3, 4, 5, 6, 7 all checked, no violations. G4: fresh subagent independently ran the ENTIRE sequence itself (including its own demo_snapshot.py attempt, which also succeeded first try) — APPROVE. Committed as `e00e29c`.
- **next_action**: none — build complete. All 10 milestones done, all committed, all G4-approved. If resuming a cold session, there is no pending work on `docs/implementation-plan.md`'s milestone table.
- **model**: whatever is running this session (no cheap/flagship split).
- **blockers**: none. Build finished.
