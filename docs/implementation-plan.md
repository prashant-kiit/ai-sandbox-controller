# Implementation Plan — AI Sandbox & Orchestrator

## Context

`docs/design-guide.md` is a fully prescriptive 17-step course that already
specifies almost the entire codebase — exact file contents for the agent,
tools, and sandbox manager. `docs/decisions.md` records where this build
deliberately deviates from (or adds to) that guide: flattened repo layout,
env-var-configurable model, updated dependency versions, an added pytest
integration suite, no Step 17 extensions, and per-step commits.

This plan sequences the build so each commit lands one guide step (or a
small related group), applies the relevant decisions.md deviation at the
right point, and stays independently testable. It does not re-derive code
that design-guide.md already fully specifies — it references step numbers
for anything that matches the guide exactly, and only spells out code where
the final result must differ from the guide's literal snippet.

**Mid-build amendment (2026-09-11):** the LLM provider switched from
Anthropic to OpenAI partway through milestone 2 — see decisions.md's
"Provider pivot" section for why and exactly what changes (env vars, SDK,
tool-schema envelope, agent-loop message shape). Milestones 2, 3, and 8's
"Build order" entries below already reflect this; guide step numbers still
apply for scope/rationale, just not for literal Claude-specific code.

Environment at plan time (repo root: `/Users/prashant/Desktop/Project/ai-sandbox-controller`):
Docker daemon not running, no `.venv`, no `ANTHROPIC_API_KEY` set, no
implementation code yet — only `docs/`, `README.md`, `LICENSE`,
`skills-lock.json`, `.claude/`.

## Pre-flight (not a commit)

1. Start Docker Desktop (`open -a Docker`), confirm with `docker ps` until it
   returns a header instead of a connection error.
2. `ANTHROPIC_API_KEY` is exported by the user in their own shell — not
   hardcoded, not prompted for by code.
3. No `mkdir ai-agent-sandbox` — every path in this plan is relative to the
   repo root directly.

## Milestones

Machine-parseable summary of the 10 build-order commits below, for
`.harness/LOOPS.md`'s BUILD loop to drive off directly. **Status** is the
only field the harness mutates as it works — everything else is fixed at
plan time. Freeze boundary = the only paths a milestone may touch.

| # | Milestone | Guide step(s) | Freeze boundary | Demo command | Status |
|---|---|---|---|---|---|
| 1 | Project scaffold, deps | 4 | `agent/__init__.py`, `tools/__init__.py`, `sandbox/__init__.py`, `requirements.txt`, `.venv/` | `pip list \| grep -E "fastapi\|docker\|anthropic\|pydantic\|uvicorn\|pytest"` | done |
| 2 | Agent core loop, no tools | 5 | `agent/llm_client.py`, `agent/agent.py` | `python3 -m agent.agent` | done |
| 3 | Tool schema | 6 | `tools/schema.py`, `tests/__init__.py`, `tests/test_schema.py` | `pytest tests/test_schema.py -v` | done |
| 4 | Sandbox manager lifecycle + Dockerfile | 7 | `sandbox/Dockerfile`, `sandbox/manager.py`, `tests/conftest.py`, `tests/test_manager_lifecycle.py` | `pytest tests/test_manager_lifecycle.py -v` | done |
| 5 | Storage/networking + port publishing | 8 | `sandbox/manager.py` (`create_vm`), `tests/test_manager_lifecycle.py` | `curl -X POST "http://localhost:8000/vms?publish_port=8080"` + pytest case | done |
| 6 | Command/file endpoints + client + executor | 9 | `sandbox/manager.py`, `sandbox/client.py`, `tools/executor.py`, `tests/test_manager_commands_and_files.py` | `pytest tests/test_manager_commands_and_files.py -v` | done |
| 7 | Snapshot & restore | 10 | `sandbox/manager.py`, `sandbox/client.py`, `tests/test_manager_snapshot_restore.py` | `pytest tests/test_manager_snapshot_restore.py -v` | pending |
| 8 | Full agent loop + run.py | 11 | `agent/agent.py`, `run.py` | `python3 run.py` (manager running in a second terminal) | pending |
| 9 | Security hardening + scaling notes | 12-13 | `sandbox/manager.py` (`SANDBOX_RUNTIME_OPTS`), `tests/test_manager_security.py` | `pytest tests/test_manager_security.py -v` | pending |
| 10 | Consolidation: demo_snapshot.py + README | 14-16 | `demo_snapshot.py`, `README.md` | `python3 demo_snapshot.py` + full verification sequence below | pending |

Commit messages for each milestone are listed in "Commit list" below;
`.harness/LOOPS.md` uses the milestone number to look up both.

## Build order

Each numbered item is one commit. File contents match `docs/design-guide.md`
at the cited step **except** where a divergence is called out explicitly.

**1 — Project scaffold, deps (Step 4)**
- `agent/__init__.py`, `tools/__init__.py`, `sandbox/__init__.py` (empty).
- `requirements.txt`: **diverges from the guide's exact pins.** Install
  `fastapi`, `uvicorn`, `docker`, `requests`, `anthropic`, `pydantic`,
  `pytest` into a fresh `.venv` unpinned, then freeze the resolved versions —
  don't hand-copy the guide's old pins (`fastapi==0.115.0` etc.), which
  predate Python 3.13.5. One `requirements.txt`, no separate dev-requirements
  file — `pytest` lives alongside the runtime deps.
- `.venv` via `python3 -m venv .venv` (per decisions.md — no uv/poetry).
- Test: `pip list | grep -E "fastapi|docker|anthropic|pydantic|uvicorn|pytest"`.

**2 — Agent core loop, no tools yet (Step 5)**
- **Diverges from the guide per decisions.md's "Provider pivot" amendment:
  OpenAI, not Anthropic.** `agent/llm_client.py`'s `LLMClient` wraps the
  `openai` SDK and resolves its model from `OPENAI_MODEL` with `gpt-4o`
  fallback, not a hardcoded default parameter:
  ```python
  def __init__(self, model: str | None = None):
      self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
      self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")
  ```
  `call()` uses `self.client.chat.completions.create(...)`, not Claude's
  `messages.create(...)` — same "thin wrapper, always accepts an optional
  `tools` list" shape as the guide, different SDK underneath.
- `agent/agent.py` (v1, no tools): `Agent.__init__` must **not** hardcode a
  model default. Take `model: str | None = None` and pass straight through
  to `LLMClient(model=model)` — the env lookup lives in exactly one place
  (`llm_client.py`). Reading the reply is `response.choices[0].message
  .content` (OpenAI shape), not the guide's `response.content` block list.
- Test: `python3 -m agent.agent` — real call, requires `OPENAI_API_KEY` in
  the shell. Confirms the API connection works before anything else is built.

**3 — Tool schema (Step 6)**
- `tools/schema.py`: **diverges from the guide per the provider pivot.**
  Same three tools (`run_command`, `write_file`, `read_file`), same
  descriptions and parameters, but wrapped in OpenAI's function-calling
  envelope (`{"type": "function", "function": {"name", "description",
  "parameters"}}`) instead of Anthropic's flat `{"name", "description",
  "input_schema"}` shape.
- Introduce `tests/` here (first pytest file, zero external deps):
  `tests/test_schema.py::test_tools_schema_shape` replaces the guide's
  throwaway assert script, updated to check the OpenAI envelope shape
  (`t["function"]["name"]`, not `t["name"]`).

**4 — Sandbox manager lifecycle + Dockerfile (Step 7)**
- `sandbox/Dockerfile`: identical to guide. Confirmed: flattening the repo
  layout doesn't affect this — `docker build -f sandbox/Dockerfile sandbox/`
  is unchanged since `sandbox/` is still `sandbox/` relative to repo root.
- `sandbox/manager.py` v1 (`create_vm`, `list_vms`, `delete_vm`, `health`)
  exactly as guide.
- `tests/conftest.py` introduced here (see "Pytest suite" below) plus
  `tests/test_manager_lifecycle.py` covering create/list/delete/health/404.

**5 — Storage/networking inspection + port publishing (Step 8)**
- `create_vm` gains `publish_port: Optional[int]` → `host_port`, exactly per
  guide. Manual `docker info`/`docker inspect`/`iptables` inspection commands
  are exploratory only — not automated.
- Add a pytest case for `publish_port` behavior alongside the lifecycle
  tests, since it's cheap given commit 4's fixtures already exist.

**6 — Command/file endpoints + client + executor (Step 9)**
- `sandbox/manager.py` gains `run_command`, `write_file`, `read_file`.
- `sandbox/client.py`: `SandboxClient` — exactly per guide (base_url default
  `http://localhost:8000` stays hardcoded, matching the guide).
- `tools/executor.py`: `ToolExecutor.execute` — exactly per guide.
- `tests/test_manager_commands_and_files.py`: converts the guide's manual
  heredoc script into real assertions (run_command stdout/exit code,
  write→read round trip, missing-file 404), plus one test driving the same
  sequence through `ToolExecutor` rather than raw HTTP, so the dispatch
  table itself is covered.

**7 — Snapshot & restore (Step 10)**
- `sandbox/manager.py` gains `SnapshotRequest`, `snapshot_vm`, `restore_vm`.
  `sandbox/client.py` gains `snapshot`, `restore`. No divergence from guide.
- `tests/test_manager_snapshot_restore.py`: the guide's manual
  bug-then-restore scenario as an assertion. **Teardown must remove the
  `sandbox-snapshot:<tag>` image** via the Docker SDK, not just the
  container — the guide's own manual test leaks this image; the pytest
  fixture should not repeat that leak.

**8 — Full agent loop + run.py (Step 11)**
- `agent/agent.py` final version (ReAct loop) — same `OPENAI_MODEL`
  divergence as commit 2 applies again; make sure it survives into this
  version, not just the throwaway v1. **Diverges from the guide per the
  provider pivot:** the loop reads `response.choices[0].message.tool_calls`
  (OpenAI) instead of filtering `response.content` for `tool_use` blocks
  (Anthropic); tool results are appended as `{"role": "tool", "tool_call_id":
  ..., "content": ...}` messages instead of a `tool_result` content block;
  each `tool_call.function.arguments` is a JSON string requiring
  `json.loads` before it reaches `ToolExecutor.execute`, unlike Anthropic's
  already-parsed `block.input` dict. `run.py` unchanged from guide shape
  (just instantiates `Agent` and calls `run`/`cleanup`).
- No new pytest here: driving the full LLM loop in the automated suite would
  be nondeterministic and token-costly, and decisions.md's pytest scope is
  sandbox-layer only (lifecycle, commands/files, snapshot/restore). This
  commit is verified manually instead: `uvicorn sandbox.manager:app --port
  8000` in one terminal, `python3 run.py` in another, real end-to-end.

**9 — Security hardening + scaling notes (Steps 12–13)**
- `SANDBOX_RUNTIME_OPTS` (`mem_limit`, `nano_cpus`, `cap_drop`,
  `security_opt`, `pids_limit`) applied to **both** `create_vm` and
  `restore_vm` — easy to miss the second one. No divergence from guide.
- Step 13 has no code of its own in the guide; fold its scaling discussion
  into this commit's message rather than a separate empty-diff commit.
- `tests/test_manager_security.py`: the guide's `mount /dev/sda1` capability
  check as an assertion (nonzero exit / "not permitted" in stderr).

**10 — Consolidation: demo_snapshot.py + README (Steps 14–16)**
- `demo_snapshot.py`: exactly per guide.
- `README.md` rewritten for the flattened layout — diverges from the guide's
  Step 14 README:
  - No `cd ai-agent-sandbox` anywhere (repo root is the project).
  - Keep `docker build -f sandbox/Dockerfile sandbox/` unchanged.
  - Add `python3 -m venv .venv && source .venv/bin/activate` explicitly.
  - Document `ANTHROPIC_MODEL` as an optional env var alongside
    `ANTHROPIC_API_KEY`.
  - Add a "Tests" section: `pytest` requires Docker running and
    `ANTHROPIC_API_KEY` set, fails loudly (no skip) if either is missing.
  - Reference `docs/design-guide.md` Step 17 as "documented, not
    implemented" rather than duplicating its content.

## Pytest suite design

Integration-style throughout — real Docker daemon, real containers, no
mocking. Structure:

```
tests/
├── __init__.py
├── conftest.py
├── test_schema.py
├── test_manager_lifecycle.py
├── test_manager_commands_and_files.py
├── test_manager_snapshot_restore.py
└── test_manager_security.py
```

`tests/conftest.py`:
- Session-scoped autouse fixture asserting `docker.from_env().ping()`
  succeeds and `OPENAI_API_KEY` is set — raises immediately (not
  `pytest.skip`) per decisions.md's "no skip logic, fail loudly" rule. This
  is a blanket precondition for the whole suite, even though the manager
  itself only needs Docker (the API key requirement matches decisions.md's
  wording exactly rather than being scoped per-test). Env var updated per
  the "Provider pivot" amendment (was `ANTHROPIC_API_KEY`).
- Session-scoped fixture that builds `ai-sandbox:latest` if missing, so
  `pytest` alone is sufficient from a clean checkout (mirrors the guide's
  "clone and run" spirit).
- Session-scoped fixture that spawns `uvicorn sandbox.manager:app` as a
  subprocess, polls `/health` until ready (hard timeout that raises, not
  skips), yields the base URL, terminates it at session end — so `pytest`
  doesn't require a human to run the manager in a second terminal first.
- Per-test `vm` fixture: creates a sandbox via `SandboxClient`, yields the
  `vm_id`, destroys it in a `finally` even on test failure.
- `pyproject.toml` `[tool.pytest.ini_options]` with `testpaths = ["tests"]`,
  no markers needed (no skip logic to gate).

## Commit list

1. `Add project scaffold, package inits, and dependencies (Step 4)`
2. `Add agent core loop (OpenAI) with configurable model via OPENAI_MODEL (Step 5)`
3. `Add tool schema and schema test (Step 6)`
4. `Add sandbox manager lifecycle endpoints, Dockerfile, and lifecycle tests (Step 7)`
5. `Add sandbox port publishing and storage/network notes (Step 8)`
6. `Add sandbox command/file endpoints, client, tool executor, and tests (Step 9)`
7. `Add snapshot/restore endpoints, client methods, and round-trip tests (Step 10)`
8. `Wire agent, tools, and sandbox into the full ReAct loop; add run.py (Step 11)`
9. `Harden sandboxes with capability drops, seccomp, resource limits; scaling notes (Steps 12-13)`
10. `Add demo_snapshot.py and finalize README for flattened layout (Steps 14-16)`

Each message body notes the guide step(s) covered and, where relevant, which
decisions.md deviation was applied.

## Verification (end-to-end, adapted from guide Step 15)

```bash
# 0. Docker running
open -a Docker && docker ps

# 1. Env, from repo root
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Base image
docker build -t ai-sandbox:latest -f sandbox/Dockerfile sandbox/

# 3. Credentials (user's own shell)
export OPENAI_API_KEY="sk-..."

# 4. Automated suite (self-sufficient: builds image if missing, starts manager itself)
pytest -v

# 5. Manager, left running in its own terminal
uvicorn sandbox.manager:app --port 8000

# 6. Sanity check
curl http://localhost:8000/health   # {"status": "ok", "sandboxes": 0}

# 7. Agent, real end-to-end task
python3 run.py                      # ends with confirmation of printed output

# 8. Snapshot/backtracking demo
python3 demo_snapshot.py            # shows buggy version, then restored clean version

# 9. Cleanup check
curl http://localhost:8000/vms      # []

# 10. Prove the OPENAI_MODEL deviation is actually wired, not just documented
OPENAI_MODEL="gpt-4o-mini" python3 -c "from agent.llm_client import LLMClient; print(LLMClient().model)"
# gpt-4o-mini
unset OPENAI_MODEL
python3 -c "from agent.llm_client import LLMClient; print(LLMClient().model)"
# gpt-4o
```

Success = guide's own Step 15 result block, plus: pytest suite green with
zero skips, and step 10's two checks confirming the env-var model override
actually works.

## Critical files

- `agent/llm_client.py`, `agent/agent.py` — provider (OpenAI, not
  Anthropic) and model-resolution divergence; see decisions.md's
  "Provider pivot" amendment
- `sandbox/manager.py`, `sandbox/client.py` — core REST surface
- `tools/executor.py`, `tools/schema.py`
- `requirements.txt` — version divergence
- `tests/conftest.py` — fixture design (self-sufficient pytest run)
- `README.md` — flattened-layout rewrite
