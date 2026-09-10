# LOOPS — the build engine

Inspired by `genesis-kit/templates/.genesis/LOOPS.md`, scoped down for a
build that's already fully specified (`docs/design-guide.md` +
`docs/decisions.md` + `docs/implementation-plan.md`'s milestone table) —
no RESEARCH loop (nothing unknown to research), no HEALTH loop (10
milestones, not an ongoing system), no quiz-me gate (solo build, session-
driven, not async). Three loops: **BUILD**, **DEBUG**, **VERIFY**.

## Operating mode

- Session-driven, interactive (per `docs/decisions.md`'s existing
  preference for local, supervised work — no CI, no autonomous scheduling).
- One model throughout (whatever's running this session) — no cheap/
  flagship split. The VERIFY step's value comes from a **fresh context**,
  not a different model.
- State lives on disk in `.harness/`, not in conversation memory. A cold
  session resumes by reading `.harness/CURRENT.md`.

## G0 — Existence pre-flight (before every milestone)

Before writing any code for milestone N:
1. Read `docs/implementation-plan.md`'s milestone table row N — freeze
   boundary, demo command.
2. Grep the repo for the freeze-boundary files/symbols. If they already
   exist and look complete, don't rebuild — verify what's there against
   the milestone's requirements instead (skip straight to G2/L4 VERIFY).
3. Write a one-line verdict (`UNBUILT` / `PARTIAL` / `BUILT`) into
   `.harness/CURRENT.md` before proceeding.

This exists to survive resuming a cold session without redoing work that's
already committed.

## Gates (checked every milestone, in order)

| Gate | Checks | Evidence required |
|---|---|---|
| **G1 Spec** | Read the cited `docs/design-guide.md` step(s) + the specific `docs/decisions.md` deviations that apply to this milestone, in full, before writing code. | Named in `.harness/CURRENT.md`'s `last_action`. |
| **G2 Progress** | The milestone's demo command (from the plan table) actually passes. | Paste the real command output — not "tests pass," the actual `pytest`/`curl`/`python3` output. |
| **G3 Invariants** | No rule in `.harness/invariants.md` violated by the diff. | Check the diff against the list explicitly; name which invariants apply. |
| **G4 Verify** | A fresh subagent (no build trail) reviews the diff against spec and invariants. | APPROVE required to close the milestone. REJECT/UNCERTAIN routes to L2 DEBUG or surfaces to the user. |

Gates are computed, not narrated: a gate isn't "done" because it was
described as done, it's done because its evidence is in the checkpoint.

## L1 — BUILD (ship one milestone)

```
read .harness/CURRENT.md
pick next milestone with Status=pending from docs/implementation-plan.md
G0 existence pre-flight
G1: read design-guide.md step(s) + decisions.md deltas for this milestone
implement per the plan's "Build order" section for this milestone
G2: run the milestone's demo command; on failure -> L2 DEBUG, then retry G2
G3: check diff against .harness/invariants.md
G4: spawn verify subagent (see L4 below)
  on APPROVE:
    git commit (message from implementation-plan.md's "Commit list")
    update milestone table Status -> done in docs/implementation-plan.md
    update .harness/CURRENT.md and .harness/implementation-notes.md
    report to user, move to next milestone
  on REJECT:
    fix per the subagent's stated reason, back to G2
  on UNCERTAIN:
    surface to user with the subagent's specific question, do not commit
```

## L2 — DEBUG (a gate failed)

Lightweight, not genesis-kit's full hypothesis-tree ritual, but same
discipline: **don't blindly retry the same fix twice.**

```
on G2 failure (demo command doesn't pass):
  read the actual error output
  form at least 2 distinct hypotheses for the root cause
  test the cheaper one first
  apply a fix, rerun G2
  if still failing after 3 attempts on this milestone: stop, surface
  the full error + what was tried to the user rather than attempt #4
```

Common expected DEBUG cases for this build specifically (see
`docs/implementation-plan.md`'s divergence list):
- `requirements.txt` version resolution failing on Python 3.13.5 — bump
  the specific package, don't re-pin everything.
- Docker daemon not running / not yet warmed up — check `docker ps`
  before assuming an application bug.
- Import path issues from running `pytest`/`python3` from the wrong
  working directory (must be repo root — see invariant 6).

## L4 — VERIFY (maker ≠ checker)

After G2 passes, before committing, spawn a **fresh subagent** (no memory
of how the code was built — only the artifact) with exactly:
- The relevant `docs/design-guide.md` step(s) text for this milestone.
- The specific `docs/decisions.md` deviations that apply to it.
- The actual diff (new/changed files for this milestone only).
- `.harness/invariants.md`.

Ask it to answer: does this diff satisfy the guide step, correctly apply
the stated deviations, and respect every invariant? Verdict: **APPROVE /
REJECT / UNCERTAIN**, with the specific reason either way. It must not see
my running commentary or the build trail — only the artifact and the spec,
so it can't rubber-stamp reasoning it already agrees with.

## What the loop is not allowed to do

- Skip G0 or G1.
- Mark a milestone done without a G4 APPROVE.
- Commit code outside the milestone's freeze boundary.
- Edit `docs/design-guide.md` or `docs/decisions.md` mid-loop (they're
  locked inputs, not loop state).
- Invent a gate result — every gate's evidence must be real command output
  or a real subagent verdict, pasted, not summarized as "passed."
- Move to milestone N+1 while N is not `done` in the plan table.
