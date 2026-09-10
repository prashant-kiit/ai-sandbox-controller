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
- **Integration-style, not mocked.** Tests hit a real Docker daemon — same
  behavior as the guide's manual tests, just automated. (Originally written
  as "real Anthropic API calls" before the "Provider pivot" amendment;
  updated for OpenAI. In practice the sandbox-layer test suite itself never
  calls the LLM at all — only `run.py`/`demo_snapshot.py` do — but the
  precondition below still requires the credential per this section's
  original wording.)
- **No skip logic.** Tests always require Docker running and
  `OPENAI_API_KEY` set; they fail loudly (not skip) if either is missing.
- **No CI workflow.** Running tests in GitHub Actions would need
  Docker-in-Docker and a real API key as a repo secret — more setup than this
  pass needs. Local-only for now.

## Provider pivot (amendment, 2026-09-11)

- **LLM provider switched from Anthropic (Claude) to OpenAI, effective
  milestone 2 onward.** The Anthropic account available for this build hit
  two hard blockers when milestone 2's demo command (`python3 -m
  agent.agent`) made a real call: first an API key not scoped to a
  workspace (`anthropic-workspace-id` required), then — after swapping to a
  workspace-scoped key — insufficient account credit. Both are account-side,
  not fixable from code. The user directed a switch to OpenAI rather than
  waiting on the Anthropic account.
- **This supersedes the "Model is configurable" bullet above.** `LLMClient`
  now reads `OPENAI_MODEL` (was `ANTHROPIC_MODEL`), falling back to
  `gpt-4o` (was `claude-sonnet-5`) if unset. `OPENAI_API_KEY` replaces
  `ANTHROPIC_API_KEY` as the required credential. The single-source-of-
  resolution rule is unchanged: it still lives in exactly one place,
  `agent/llm_client.py`.
- **SDK: `openai` package replaces `anthropic`** in `requirements.txt`,
  version resolved fresh the same way (see "Dependency versions" above).
- **Tool-calling format changes starting at milestone 3
  (`tools/schema.py`).** OpenAI's function-calling schema
  (`{"type": "function", "function": {"name", "description", "parameters"}}`)
  replaces Anthropic's flat `{"name", "description", "input_schema"}` shape
  from `design-guide.md` Step 6. The three tools (`run_command`,
  `write_file`, `read_file`) and their semantics are unchanged — only the
  JSON envelope differs.
- **Agent loop message format changes starting at milestone 8
  (`agent/agent.py`'s final ReAct loop).** OpenAI's chat-completions
  conventions (`role: system/user/assistant/tool`, `response.choices[0]
  .message.tool_calls`, `tool_call_id`) replace Anthropic's content-block
  conventions (`response.content` blocks of type `tool_use`/`tool_result`)
  from `design-guide.md` Step 11. `tools/executor.py`'s dispatch table
  (name + input dict → sandbox action) is provider-agnostic and does not
  change.
- **`docs/design-guide.md` is not edited.** It stays as the original
  Anthropic-based course text (locked input, per the harness's own rule).
  This amendment plus each affected milestone's "Build order" entry in
  `docs/implementation-plan.md` are what capture the divergence from here
  on — the guide is read as "this is the shape, adapted for OpenAI's API,"
  not followed for literal SDK calls once milestone 2 is reached.

## Default model amendment (2026-09-11)

- **`OPENAI_MODEL`'s fallback changed from `gpt-4o` to `gpt-5`,
  discovered and fixed during milestone 10's verification.** Running
  `demo_snapshot.py` (unmodified, exactly per guide) against the default
  `gpt-4o` fallback failed to reliably complete the "introduce a bug"
  step in 3 consecutive real runs — the model described the intended
  change in prose instead of calling `write_file`, apparently because the
  task text doesn't name the file and `gpt-4o` is less willing than
  Claude (the guide's original model) to infer or explore for it. The
  same unmodified script with `OPENAI_MODEL=gpt-5` succeeded on the first
  try, including using `run_command` to inspect the sandbox first. The
  underlying snapshot/restore mechanism was never in question — milestone
  7's pytest suite already proves that round trip deterministically via
  direct tool calls, bypassing the LLM entirely.
- **This supersedes the "Provider pivot" amendment's `gpt-4o` fallback
  above.** `agent/llm_client.py` now reads `OPENAI_MODEL`, falling back
  to `gpt-5` if unset. `OPENAI_API_KEY` requirement and the
  single-source-of-resolution rule are unchanged.
- No code outside `agent/llm_client.py` changes because of this — it's a
  one-line default-value edit, not a shape change like the provider
  pivot's tool-schema/message-format divergences.

## Process

- **One git commit per design-guide step** (or small logical group of related
  steps), each committed once it lands and passes its test — so history
  mirrors the course's own progression.
- **Docker Desktop is started as part of setup** (it was installed but not
  running at the time of this build).
- **`ANTHROPIC_API_KEY` is provided via the session shell** (not pasted into
  chat), so the agent loop (Steps 5, 11, 15) can be run and verified
  end-to-end as part of the build, not deferred to later manual testing.
