# Build Decisions — AI Sandbox & Orchestrator

Decisions made before implementation, based on `docs/design-guide.md`. This file
records *what* was decided and *why*, so later contributors don't have to
re-derive intent from the code.

## Scope & terminology

- **"Orchestrator" = the design guide's Sandbox Manager.** A single REST
  service (`sandbox/manager.py`) managing containers on one Docker host, as
  described in Steps 7–14. There is no separate multi-host/fleet-scheduling
  layer above it — that's explicitly out of scope for this build.
- **Full course, Steps 1–16, built end-to-end.** Every step in the guide is
  implemented, not a subset.
- **Step 17 stays documentation-only.** The guide itself frames the
  browser/computer-use sandbox (Chrome + VNC) and the MCP server front-end as
  "beyond this course" extensions. They are not implemented in this pass.
- **Code lives at the repo root**, not nested under an `ai-agent-sandbox/`
  subfolder. This repo (`ai-sandbox-controller`) *is* the project — `agent/`,
  `tools/`, `sandbox/`, `run.py`, `requirements.txt` etc. sit directly at the
  top level.
- **Docker containers are the sandbox runtime**, matching the guide's own
  scope note. This machine is macOS on Apple Silicon with no `/dev/kvm`, so
  real microVMs (Firecracker/Cloud Hypervisor) aren't possible here anyway —
  Docker isn't just the default, it's the only option this host supports.

## Build details

- **Model is configurable.** `LLMClient` reads the model from the
  `ANTHROPIC_MODEL` env var, falling back to `claude-sonnet-5` if unset —
  rather than the guide's hardcoded default, so it can be swapped without
  code changes.
- **Dependency versions: latest compatible, not the guide's exact pins.**
  `requirements.txt` pins in the guide (`fastapi==0.115.0`,
  `anthropic==0.39.0`, `docker==7.1.0`, `pydantic==2.9.2`, etc.) predate
  Python 3.13. This host runs Python 3.13.5, so we use the latest stable
  version of each package instead of chasing guide-era pins.
- **Python environment via stdlib `venv` + `pip`**, exactly as the guide
  shows (`python3 -m venv .venv`, `pip install -r requirements.txt`) — no
  additional tooling (uv/poetry/etc.).

## Testing

- **A pytest suite is added**, beyond the guide's manual curl/script tests,
  covering the same scenarios: VM create/list/delete/health, run_command,
  read_file/write_file, and snapshot/restore round-trips.
- **Integration-style, not mocked.** Tests hit a real Docker daemon and make
  real Anthropic API calls — same behavior as the guide's manual tests, just
  automated.
- **No skip logic.** Tests always require Docker running and
  `ANTHROPIC_API_KEY` set; they fail loudly (not skip) if either is missing.
- **No CI workflow.** Running tests in GitHub Actions would need
  Docker-in-Docker and a real API key as a repo secret — more setup than this
  pass needs. Local-only for now.

## Process

- **One git commit per design-guide step** (or small logical group of related
  steps), each committed once it lands and passes its test — so history
  mirrors the course's own progression.
- **Docker Desktop is started as part of setup** (it was installed but not
  running at the time of this build).
- **`ANTHROPIC_API_KEY` is provided via the session shell** (not pasted into
  chat), so the agent loop (Steps 5, 11, 15) can be run and verified
  end-to-end as part of the build, not deferred to later manual testing.
