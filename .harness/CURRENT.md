# CURRENT — always overwritten

The single-file resumability anchor. Read this first when resuming a cold
session; it plus `docs/implementation-plan.md`'s milestone table is enough
to know exactly where the build stands without re-reading history.

- **active_milestone**: none (not yet started)
- **iteration**: 0
- **last_gate**: —
- **last_action**: harness scaffolded (`.harness/` + `.claude/skills/sandbox-harness/`); `docs/implementation-plan.md` restructured with a machine-parseable milestone table. No build code written yet.
- **next_action**: run G0 existence pre-flight on milestone 1 (project scaffold, deps), then L1 BUILD.
- **model**: whatever is running this session (no cheap/flagship split).
- **blockers**: Docker Desktop daemon not running as of last check; `ANTHROPIC_API_KEY` not yet exported in this session's shell. Both needed before milestone 2 onward (milestone 1 itself doesn't need either).
