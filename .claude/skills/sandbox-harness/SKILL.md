---
name: sandbox-harness
description: Drive the AI Sandbox Orchestrator build through its gated BUILD/DEBUG/VERIFY loop, milestone by milestone, off docs/implementation-plan.md's milestone table. Use when the user says "build the sandbox orchestrator", "run the harness", "continue the build", or "resume milestone build".
---

Drive `docs/implementation-plan.md` to completion, one milestone at a time,
using the loop mechanics in `.harness/LOOPS.md`. Inspired by genesis-kit's
BUILD/VERIFY loop, scoped down because the spec is already locked (no
RESEARCH loop needed, no HEALTH loop, no quiz-me gate — see
`.harness/LOOPS.md`'s header for why).

## Read order (every time this skill runs, cold session or not)

1. `docs/decisions.md` — the locked build decisions.
2. `docs/design-guide.md` — the spec (read the specific step(s) for the
   current milestone in full before writing code, not just skimmed).
3. `docs/implementation-plan.md` — the milestone table; find the first row
   with `Status=pending`.
4. `.harness/CURRENT.md` — where the loop left off.
5. `.harness/invariants.md` — what a milestone must not violate.
6. `.harness/implementation-notes.md` — narrative context on any prior
   deviations from plan.

## What to do

Run `.harness/LOOPS.md`'s **L1 BUILD** loop on the next pending milestone:
G0 existence pre-flight, implement per the plan's "Build order" section,
G2 (run the milestone's demo command for real, paste the output), G3
(check against invariants), G4 (spawn a fresh verify subagent — see
`.harness/LOOPS.md`'s L4 section for exactly what it should and shouldn't
see). On APPROVE: commit, update the milestone table's Status column,
update `.harness/CURRENT.md` and `.harness/implementation-notes.md`,
report to the user, stop and wait rather than auto-continuing to the next
milestone (session-driven, per `docs/decisions.md`).

On a gate failure, run `.harness/LOOPS.md`'s **L2 DEBUG** loop — at least
2 distinct hypotheses before the first fix attempt, never two blind
retries in a row, surface to the user after 3 failed attempts on the same
milestone rather than continuing to guess.

## Stop conditions

- A milestone's demo command fails 3 times running L2 DEBUG — stop, show
  the user the actual error and what was tried.
- L4 VERIFY returns UNCERTAIN — stop, show the user the subagent's
  specific question rather than guessing an answer.
- Docker daemon or `ANTHROPIC_API_KEY` unavailable and the milestone needs
  either — stop, tell the user what's missing (don't silently skip the
  milestone's test).

## What good looks like

Every `done` row in the milestone table has: a real commit, a real demo-
command output that was pasted (not summarized), and a real subagent
APPROVE verdict — all three, not two out of three.

## Common pitfalls (mirrors genesis-kit's own list)

- Skipping G0 and rebuilding a milestone that's already committed.
- Marking a milestone done because "the code looks right" without
  actually running its demo command.
- Being both the builder and the verifier — G4 must be a fresh subagent
  call, not a mental re-check.
- Editing `docs/design-guide.md` or `docs/decisions.md` to make a
  milestone easier — they're locked; if the plan itself needs to change,
  that's a `docs/implementation-plan.md` edit surfaced to the user, not a
  silent spec change.
