# Invariants

Health rules the BUILD/VERIFY loop checks on every milestone. If a change
would violate one of these, it's a REJECT at L4 VERIFY regardless of
whether tests pass — these encode architecture decisions that tests don't
catch by themselves.

Sourced from `docs/design-guide.md` (architecture rationale) and
`docs/decisions.md` (build decisions), not invented by the harness.

1. **`agent/` never imports `docker` or the Docker SDK directly.** It only
   talks to sandboxes through `sandbox/client.py`'s `SandboxClient` over
   HTTP. (design-guide.md Step 4 — this is what lets the agent and sandbox
   run on different machines without protocol changes.)
2. **`sandbox/` never imports `anthropic` or the Claude SDK.** The sandbox
   manager only knows about containers; it has no idea an LLM exists.
   (design-guide.md Step 4, same rationale.)
3. **`tools/executor.py` only calls `SandboxClient` methods, never raw
   `requests` or `docker` calls.** It's a dispatch table, not a second
   client implementation.
4. **Model resolution lives in exactly one place: `agent/llm_client.py`.**
   Reads `ANTHROPIC_MODEL` env var, falls back to `claude-sonnet-5`.
   `agent/agent.py` must not hardcode a model default of its own — it
   passes `model=None` through and lets `LLMClient` resolve it.
   (decisions.md deviation from the guide's hardcoded default.)
5. **`SANDBOX_RUNTIME_OPTS` (cap_drop, mem_limit, nano_cpus, security_opt,
   pids_limit) is applied to every place a container is created —
   `create_vm` AND `restore_vm`.** The guide's own Step 10 snippet omits it
   on `restore_vm`; Step 12 must fix both call sites, not just one.
6. **No `mkdir ai-agent-sandbox` / nested project folder.** Every path in
   this build is relative to the repo root directly (decisions.md).
7. **Tests are integration-style against real Docker + real Anthropic API,
   with no skip logic.** A test suite that silently skips when Docker or
   `ANTHROPIC_API_KEY` is unavailable violates decisions.md's explicit
   "fail loudly" requirement.
8. **`requirements.txt` pins specific resolved versions, not the guide's
   original (pre-Python-3.13) pins.** A milestone that copies the guide's
   exact version numbers verbatim without checking they resolve on this
   host's Python 3.13.5 violates decisions.md.
