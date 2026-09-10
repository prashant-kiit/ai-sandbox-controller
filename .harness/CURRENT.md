# CURRENT — always overwritten

The single-file resumability anchor. Read this first when resuming a cold
session; it plus `docs/implementation-plan.md`'s milestone table is enough
to know exactly where the build stands without re-reading history.

- **active_milestone**: 9 (done)
- **iteration**: 9
- **last_gate**: G4 Verify — APPROVE (fresh subagent, milestone 9 diff vs. design-guide.md Steps 12-13 + invariants.md; explicitly confirmed `SANDBOX_RUNTIME_OPTS` on both `create_vm` and `restore_vm` call sites, ran the tests and full suite itself)
- **last_action**: Milestone 9 (security hardening + scaling notes) built and committed, no divergence from the guide. `SANDBOX_RUNTIME_OPTS` (mem_limit=512m, nano_cpus=1 vCPU, cap_drop=ALL, security_opt=no-new-privileges, pids_limit=256) added and spread into BOTH `create_vm`'s and `restore_vm`'s `client.containers.run(...)` calls — the guide's own Step 10 restore_vm snippet omits it, invariant 5 exists specifically to catch that. `tests/test_manager_security.py`: the guide's mount `/dev/sda1` capability check as a real assertion, plus a second test that snapshots+restores a VM before re-checking the same denial (the test that would actually catch a missing opts application on `restore_vm`). Step 13 (scaling notes, no code of its own) folded into the commit message. G2: `pytest tests/test_manager_security.py -v` → 2 passed; full suite → 15 passed, no regressions; confirmed no leftover containers or `sandbox-snapshot` images. G3: invariants 2, 5, 6, 7 checked, no violations — invariant 5 explicitly confirmed on both call sites. G4: fresh subagent independently verified both call sites, re-ran the tests and full suite — APPROVE. Committed as `2be4704`.
- **next_action**: run G0 existence pre-flight on milestone 10 (consolidation: demo_snapshot.py + README — Steps 14-16), then L1 BUILD. This is the final milestone — demo command is `python3 demo_snapshot.py` plus the full verification sequence from the plan's "Verification" section. README needs a from-scratch rewrite for the flattened layout, `ANTHROPIC_MODEL`→`OPENAI_MODEL`/`OPENAI_API_KEY` per the provider pivot, and a "Tests" section.
- **model**: whatever is running this session (no cheap/flagship split).
- **blockers**: none currently. Docker confirmed running; `OPENAI_API_KEY` confirmed working in `.env`; `ai-sandbox:latest` image built and cached locally.
