# ai-sandbox-controller

A minimal AI agent that plans with an LLM and executes every action inside
an isolated Docker sandbox instead of on the host machine. Based on the
course in `docs/design-guide.md`; see `docs/decisions.md` for where and
why this build diverges from it.

## Run

1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `docker build -t ai-sandbox:latest -f sandbox/Dockerfile sandbox/`
4. `export OPENAI_API_KEY="sk-..."`
5. `uvicorn sandbox.manager:app --port 8000` (leave running in its own terminal)
6. `python3 run.py` (in a second terminal)

`OPENAI_MODEL` is an optional env var alongside `OPENAI_API_KEY` — set it
to override the default model (`gpt-5`); leave it unset to use the
default. This build uses OpenAI rather than the design guide's Anthropic
client — see decisions.md's "Provider pivot" section for why, and its
"Default model amendment" for why the fallback is `gpt-5` rather than
`gpt-4o` (the latter proved unreliable at driving `demo_snapshot.py`'s
natural-language task end to end).

## Layout

- `sandbox/` — REST manager + Docker-based sandbox runtime + Python client
- `tools/` — tool schema (what the LLM can ask for) + executor (what actually runs)
- `agent/` — the LLM wrapper and the agent's reasoning loop
- `tests/` — integration-style pytest suite against a real Docker daemon and real OpenAI API
- `run.py` — runs the agent on a single real task end-to-end
- `demo_snapshot.py` — runs the agent through a snapshot/backtracking scenario

## Tests

```bash
pytest -v
```

Requires a running Docker daemon and `OPENAI_API_KEY` set in the
environment. The suite fails loudly (raises, does not skip) if either is
missing — see decisions.md's "no skip logic" rule. It is otherwise
self-sufficient: it builds `ai-sandbox:latest` if missing and starts its
own `sandbox.manager` instance, so a clean checkout only needs the two
preconditions above.

## Extensions not implemented here

`docs/design-guide.md` Step 17 (browser/computer-use sandbox via VNC, and
exposing the sandbox over MCP) is documented in the guide but not
implemented in this build — see decisions.md's scope note.
