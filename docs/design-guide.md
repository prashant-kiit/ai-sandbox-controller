# Build an AI Agent with a Sandbox — From Scratch

A hands-on course based on a talk about **Arachis**, an open-source AI sandboxing service. We will build a small but real version of the same system: an **AI Agent** that plans and calls tools, and a **Sandbox** that runs those tool calls in an isolated Linux environment.

By the end, you will have:

- An agent that talks to an LLM (Claude) and decides what to do next
- A sandbox manager that creates isolated Linux environments on demand
- Tools that let the agent run commands and read/write files *inside* the sandbox, not on your host machine
- Snapshot and restore, so the agent can checkpoint progress and backtrack if it fails
- An understanding of *why* each piece is built the way it is (namespaces, cgroups, capabilities, virtualization, microVMs)

> **Scope note:** The talk this course is based on uses **microVMs** (Firecracker / Cloud Hypervisor) as the sandbox runtime, because that is what a production system needs. Running a real microVM needs a Linux host with `/dev/kvm` access, which most laptops/CI runners don't expose easily. So this course builds the same architecture using **Docker containers** as the sandbox runtime — everything you build here runs on any machine with Docker. Each step still explains the stronger (microVM) approach and how you'd swap it in later.

---

## Step 1: Prerequisites

**What:**
Software and accounts you need before starting.

**Why:**
The agent needs an LLM to think, and the sandbox needs a container engine to isolate code execution. Without both, nothing else in this course runs.

**Implementation:**

Install these on your machine:

| Requirement | Purpose | Check |
|---|---|---|
| Python 3.10+ | Runs the agent and sandbox manager | `python3 --version` |
| Docker Desktop / Docker Engine | Runs sandboxes as containers | `docker --version` |
| An Anthropic API key | Powers the agent's reasoning | `echo $ANTHROPIC_API_KEY` |

```bash
# 1. Confirm Docker is running
docker ps

# 2. Confirm Python
python3 --version

# 3. Export your API key (get one at console.anthropic.com)
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Code Explanation:**
`docker ps` lists running containers — an empty list with no error means Docker is installed and its daemon is reachable. `ANTHROPIC_API_KEY` is read by the Anthropic SDK automatically; we never hardcode it in code.

**Test:**
Run all three commands above.

**Result:**
`docker ps` prints a table header (even if empty). `python3 --version` prints `3.10` or higher. The API key prints your key (masked if you want).

---

## Step 2: What We Are Building

**What:**
A system with two independent parts talking over HTTP:

1. **Agent** — calls an LLM in a loop, decides which tool to use, reads the result, decides the next step.
2. **Sandbox** — a REST service that creates, runs commands in, and destroys isolated Linux environments, on request.

**Why:**
The talk makes one point over and over: agent code is untrusted code. An LLM can generate correct code or buggy/malicious code — the agent has no way to know in advance. So tool execution must never run on your host or production server directly. It must run in something isolated, disposable, and recoverable. That "something" is the sandbox.

**Implementation:**

Conceptual flow:

```
User task
   │
   ▼
Agent  ───tool call (run_command / read_file / write_file)───▶  Sandbox
   ▲                                                                │
   └──────────────────── tool result (stdout / file content) ◀─────┘
```

The agent never touches the filesystem or shell of your machine. Every "hands-on" action goes through the sandbox's REST API.

**Code Explanation:**
No code yet — this step is the mental model for everything that follows.

**Test:**
N/A.

**Result:**
You should be able to answer: *"If the agent asks to run `rm -rf /`, whose disk is at risk?"* — Answer: only the sandbox container's disk, which is disposable.

---

## Step 3: Architecture

**What:**
The concrete component diagram we will build, mapped to the concepts from the talk.

**Why:**
Before writing code, we need to know what each piece maps to, so implementation choices later (Docker, overlay filesystem, port mapping) make sense as *stand-ins* for the production versions (microVM, Firecracker's block device, tap networking).

**Implementation:**

```
┌────────────────────┐        HTTP (tool calls)        ┌──────────────────────────┐
│                     │ ───────────────────────────────▶│                          │
│   Agent Process     │                                  │   Sandbox Manager        │
│  (agent/agent.py)   │◀──────────────────────────────── │  (sandbox/manager.py)    │
│                     │        HTTP (tool results)        │  FastAPI REST server     │
└─────────┬───────────┘                                   └────────────┬─────────────┘
          │                                                             │ docker SDK
          │ calls                                                       ▼
          ▼                                                ┌────────────────────────┐
┌─────────────────────┐                                    │      Docker Engine       │
│  LLM (Claude API)    │                                    │  ┌────────────────────┐ │
│  decides tool calls  │                                    │  │ Sandbox container A │ │
└─────────────────────┘                                    │  └────────────────────┘ │
                                                             │  ┌────────────────────┐ │
                                                             │  │ Sandbox container B │ │
                                                             │  └────────────────────┘ │
                                                             └────────────────────────┘
```

| Concept from the talk | Production tool | What we build instead | Why it's an OK stand-in |
|---|---|---|---|
| VMM (virtual machine monitor) | Cloud Hypervisor / Firecracker | Docker Engine | Both create, start, stop isolated execution environments with an API |
| microVM | Guest kernel + KVM | Linux container (namespaces + cgroups) | Weaker isolation, same programming model |
| Root FS with shared read-only base + per-sandbox read-write layer | Custom overlay FS on the host | Docker's `overlay2` storage driver | Docker already implements exactly this layering |
| tap device + Linux bridge + iptables | Manual bridge/iptables setup | Docker's built-in bridge network + NAT | Docker sets up the same primitives for you |
| Snapshot (memory dump + RW layer backup) | Cloud Hypervisor snapshot API | `docker commit` (filesystem only, no memory) | Same *idea* (checkpoint state), narrower scope |
| Code execution server inside the guest | Custom HTTP server in the VM | `docker exec` from the manager | Same job: run a command, return stdout/stderr |
| REST server + Python SDK | Arachis manager + SDK | `sandbox/manager.py` + `sandbox/client.py` | Same shape |

**Code Explanation:**
This table is the map you'll refer back to for the rest of the course. Every time we write a "sandbox" function, it's standing in for a specific microVM mechanism from the talk.

**Test:**
N/A.

**Result:**
You know what each file you're about to create corresponds to conceptually.

---

## Step 4: Project Setup

**What:**
The folder structure and dependencies for the whole project.

**Why:**
Keeping `agent/`, `tools/`, and `sandbox/` separate mirrors the real system: the agent and the sandbox are independent services that only talk over HTTP. You could run them on two different machines without changing a line of protocol code.

**Implementation:**

```bash
mkdir ai-agent-sandbox && cd ai-agent-sandbox
mkdir agent tools sandbox
touch agent/__init__.py tools/__init__.py sandbox/__init__.py
python3 -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
```

`requirements.txt`:

```text
fastapi==0.115.0
uvicorn==0.32.0
docker==7.1.0
requests==2.32.3
anthropic==0.39.0
pydantic==2.9.2
```

```bash
pip install -r requirements.txt
```

Target structure (grows as we go):

```text
ai-agent-sandbox/
├── agent/
│   ├── __init__.py
│   ├── llm_client.py
│   └── agent.py
├── tools/
│   ├── __init__.py
│   ├── schema.py
│   └── executor.py
├── sandbox/
│   ├── __init__.py
│   ├── Dockerfile
│   ├── manager.py
│   └── client.py
├── run.py
├── requirements.txt
└── README.md
```

**Code Explanation:**
`agent/` only knows how to talk to the LLM and to the sandbox's HTTP API — it never imports Docker directly. `sandbox/` only knows how to manage containers — it never imports the Anthropic SDK. This separation is what let the talk's speaker offer a Python SDK, a Go CLI, and an MCP server all on top of the *same* REST API.

**Test:**
```bash
pip list | grep -E "fastapi|docker|anthropic"
```

**Result:**
All three packages show up with the versions from `requirements.txt`.

---

## Step 5: Build the Agent (core loop, no tools yet)

**What:**
The smallest possible agent: send a task to Claude, print the reply.

**Why:**
Before adding tools and a sandbox, confirm the LLM connection works. This isolates problems — if this step fails, it's an API/key issue, not a Docker issue.

**Implementation:**

`agent/llm_client.py`:

```python
import os
from anthropic import Anthropic

class LLMClient:
    """Thin wrapper so the rest of the agent never touches the SDK directly."""

    def __init__(self, model: str = "claude-sonnet-5"):
        self.client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = model

    def call(self, messages, tools=None, system=None):
        return self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=messages,
            tools=tools or [],
        )
```

`agent/agent.py` (v1 — no tools):

```python
from agent.llm_client import LLMClient

class Agent:
    def __init__(self, model: str = "claude-sonnet-5"):
        self.llm = LLMClient(model=model)

    def run(self, task: str) -> str:
        messages = [{"role": "user", "content": task}]
        response = self.llm.call(messages)
        text = "".join(b.text for b in response.content if b.type == "text")
        print(f"[agent] {text}")
        return text

if __name__ == "__main__":
    Agent().run("Say hello and tell me what you can help with in one sentence.")
```

**Code Explanation:**
`LLMClient.call` always passes `tools` (empty list if none) so later steps just plug in a tool list. `response.content` is a list of blocks — right now only `text` blocks exist, so we join them.

**Test:**
```bash
python3 -m agent.agent
```

**Result:**
Claude's one-sentence reply prints to your terminal. If this fails, fix your API key before continuing — everything else builds on this.

---

## Step 6: Add Tools

**What:**
Give the LLM a menu of actions it's allowed to request: run a shell command, write a file, read a file. The LLM doesn't run anything itself — it only *asks* for an action, using Claude's tool-use format.

**Why:**
The talk's core insight is that agents become far more capable with a full Linux shell than with a handful of hand-picked functions: *"You don't need a big prompt or a lot of alignment frameworks to make a coding agent when it has a Linux sandbox at its disposal."* So instead of building 20 narrow tools (`create_file`, `install_package`, `run_tests`...), we build 3 general ones and let the model use normal shell commands (`pip install`, `pytest`, `mkdir`, etc.) through `run_command`.

**Implementation:**

`tools/schema.py`:

```python
TOOLS = [
    {
        "name": "run_command",
        "description": "Run a shell command inside the Linux sandbox and get back stdout/stderr/exit code.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "A bash command, e.g. 'python3 app.py'"}
            },
            "required": ["command"],
        },
    },
    {
        "name": "write_file",
        "description": "Write text content to a file inside the sandbox (creates or overwrites it).",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path relative to /workspace"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a text file from inside the sandbox.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path relative to /workspace"}},
            "required": ["path"],
        },
    },
]
```

**Code Explanation:**
Each entry is a JSON schema describing one action. Claude reads these descriptions and decides, on its own, when to call `run_command` vs `write_file`. We haven't implemented *what happens* when a tool is called yet — that's the sandbox's job, wired up in Step 9.

**Test:**
```python
from tools.schema import TOOLS
assert len(TOOLS) == 3
print([t["name"] for t in TOOLS])
```

**Result:**
`['run_command', 'write_file', 'read_file']` — just a static check that the schema loads.

---

## Step 7: Add Sandbox

**What:**
A REST service (`sandbox/manager.py`) that can create, list, and delete isolated Linux environments, backed by Docker containers. This is the direct equivalent of Arachis's VMM + REST server.

**Why:**
From the talk: *"Agent code is no different than you using any code from GitHub and running it on your host or production server. This code could be buggy or malicious and can get root."* The fix is to never run agent-requested code in the same kernel/process/filesystem as your real application. A container gives each sandbox its own process namespace, mount namespace, and network namespace — a first line of defense (we harden this further in Step 12).

**Implementation:**

`sandbox/Dockerfile` — the base image every sandbox is created from:

```dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    nodejs npm \
    curl wget git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Keep the container alive; the manager runs commands into it with `docker exec`.
CMD ["sleep", "infinity"]
```

```bash
docker build -t ai-sandbox:latest -f sandbox/Dockerfile sandbox/
```

`sandbox/manager.py` (v1 — lifecycle only):

```python
import uuid
import docker
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Sandbox Manager")
client = docker.from_env()

SANDBOX_IMAGE = "ai-sandbox:latest"
LABEL = "ai-sandbox"


def get_container(vm_id: str):
    try:
        return client.containers.get(vm_id)
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="sandbox not found")


@app.post("/vms")
def create_vm():
    vm_id = f"sandbox-{uuid.uuid4().hex[:8]}"
    container = client.containers.run(
        SANDBOX_IMAGE,
        name=vm_id,
        detach=True,
        tty=True,
        labels={"managed-by": LABEL},
    )
    return {"vm_id": vm_id, "status": container.status}


@app.get("/vms")
def list_vms():
    containers = client.containers.list(all=True, filters={"label": f"managed-by={LABEL}"})
    return [{"vm_id": c.name, "status": c.status} for c in containers]


@app.delete("/vms/{vm_id}")
def delete_vm(vm_id: str):
    get_container(vm_id).remove(force=True)
    return {"vm_id": vm_id, "deleted": True}


@app.get("/health")
def health():
    n = len(client.containers.list(filters={"label": f"managed-by={LABEL}"}))
    return {"status": "ok", "sandboxes": n}
```

**Code Explanation:**
`docker.from_env()` talks to your local Docker daemon over its socket — this is the same relationship the VMM in the talk has with `/dev/kvm`. `create_vm` starts a container with `sleep infinity` so it stays alive for future `exec` calls, instead of running one command and exiting. The `managed-by` label lets us find *only* sandboxes we created, ignoring unrelated containers on your machine.

**Test:**
```bash
uvicorn sandbox.manager:app --port 8000 --reload
# in another terminal:
curl -X POST http://localhost:8000/vms
curl http://localhost:8000/vms
curl http://localhost:8000/health
```

**Result:**
The POST returns something like `{"vm_id": "sandbox-3f9a2b1c", "status": "created"}`. `docker ps` in your terminal shows that container running. The GET lists it back.

---

## Step 8: Sandbox Storage & Networking

**What:**
Understand — and inspect — the filesystem layering and networking Docker gives every sandbox for free, and add optional port publishing so a sandbox can expose a running service.

**Why:**
The talk spends real time on two mechanics:

1. **Storage:** a shared, read-only root filesystem plus a per-sandbox read-write layer, so agent code can never corrupt the shared base, and only the small "diff" needs to be backed up.
2. **Networking:** each sandbox gets an isolated network namespace, connected to the host via a virtual interface (`tap` device) plumbed into a Linux bridge, with `iptables` rules doing port forwarding — so a VNC server or web app inside the sandbox is reachable from outside.

Docker already implements both, using the exact same Linux primitives (OverlayFS, bridges, iptables DNAT) the talk describes building by hand.

**Implementation:**

Inspect the storage layering:

```bash
docker info | grep "Storage Driver"
# Storage Driver: overlay2
```

`overlay2` gives every container a read-only stack of image layers (the shared root filesystem — same idea as the talk's yellow "shared base layer") plus one writable layer on top (same idea as the per-sandbox read-write layer). Files an agent creates only ever touch that top layer.

```bash
docker inspect sandbox-3f9a2b1c --format '{{.GraphDriver.Data}}'
```

This prints the actual `LowerDir` (read-only, shared) and `UpperDir` (writable, per-container) paths on your host — you can `ls` into `UpperDir` and see exactly the files the agent created.

Now add optional port publishing to `create_vm` in `sandbox/manager.py`:

```python
from typing import Optional

@app.post("/vms")
def create_vm(publish_port: Optional[int] = None):
    vm_id = f"sandbox-{uuid.uuid4().hex[:8]}"
    ports = {f"{publish_port}/tcp": None} if publish_port else None

    container = client.containers.run(
        SANDBOX_IMAGE,
        name=vm_id,
        detach=True,
        tty=True,
        ports=ports,
        labels={"managed-by": LABEL},
    )
    container.reload()
    host_port = None
    if publish_port:
        binding = container.ports.get(f"{publish_port}/tcp")
        host_port = binding[0]["HostPort"] if binding else None
    return {"vm_id": vm_id, "status": container.status, "host_port": host_port}
```

```bash
curl -X POST "http://localhost:8000/vms?publish_port=8080"
```

Inspect the networking Docker set up for you:

```bash
docker network inspect bridge | grep -A3 '"sandbox-'
iptables -t nat -L DOCKER -n     # Linux only — shows the DNAT rules Docker just wrote
```

**Code Explanation:**
`ports={"8080/tcp": None}` tells Docker "expose container port 8080 on a random free host port." Docker then: (1) connects the container to its bridge network via a virtual `veth` pair — the same job the talk's `tap` device does, (2) adds the container's bridge to `docker0` — the same job as the talk's Linux bridge, (3) writes an `iptables` DNAT rule mapping the host port to the container's IP:port — the exact mechanism the talk's speaker showed setting up by hand. `container.ports` reads back which host port got assigned.

**Test:**
Run the `curl` command with `publish_port=8080`, then inside that sandbox start a tiny server and hit it from your host:

```bash
VM_ID=$(curl -s -X POST "http://localhost:8000/vms?publish_port=8080" | python3 -c "import sys,json; print(json.load(sys.stdin)['vm_id'])")
docker exec -d $VM_ID python3 -m http.server 8080 --directory /workspace
curl http://localhost:8080/
```

**Result:**
You get an HTML directory listing back — proof that traffic went: your terminal → host port → Docker's NAT rule → bridge → sandbox's port 8080, all set up automatically.

---

## Step 9: Agent ↔ Sandbox Communication

**What:**
A Python client (`sandbox/client.py`) that wraps the REST API, and command/file endpoints in the manager so tools can actually *do* something inside a sandbox.

**Why:**
The talk gives Arachis a "dead simple API" with a Python SDK on top, specifically so agent code never deals with raw HTTP or Docker internals. We do the same: `tools/executor.py` will call `SandboxClient` methods, never `requests` directly.

**Implementation:**

Add to `sandbox/manager.py`:

```python
import io
import tarfile
from pydantic import BaseModel

class CommandRequest(BaseModel):
    command: str

class FileWriteRequest(BaseModel):
    path: str
    content: str

@app.post("/vms/{vm_id}/commands")
def run_command(vm_id: str, req: CommandRequest):
    container = get_container(vm_id)
    exit_code, output = container.exec_run(
        cmd=["/bin/bash", "-lc", req.command],
        workdir="/workspace",
        demux=True,
    )
    stdout, stderr = output
    return {
        "exit_code": exit_code,
        "stdout": stdout.decode() if stdout else "",
        "stderr": stderr.decode() if stderr else "",
    }

@app.post("/vms/{vm_id}/files")
def write_file(vm_id: str, req: FileWriteRequest):
    container = get_container(vm_id)
    data = req.content.encode()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name=req.path.lstrip("/"))
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    buf.seek(0)
    container.put_archive("/workspace", buf)
    return {"path": req.path, "bytes_written": len(data)}

@app.get("/vms/{vm_id}/files")
def read_file(vm_id: str, path: str):
    container = get_container(vm_id)
    try:
        stream, _ = container.get_archive(f"/workspace/{path.lstrip('/')}")
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="file not found")
    buf = io.BytesIO()
    for chunk in stream:
        buf.write(chunk)
    buf.seek(0)
    with tarfile.open(fileobj=buf) as tar:
        member = tar.getmembers()[0]
        content = tar.extractfile(member).read()
    return {"path": path, "content": content.decode(errors="replace")}
```

`sandbox/client.py`:

```python
import requests

class SandboxClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def create(self) -> str:
        r = requests.post(f"{self.base_url}/vms")
        r.raise_for_status()
        return r.json()["vm_id"]

    def destroy(self, vm_id: str):
        r = requests.delete(f"{self.base_url}/vms/{vm_id}")
        r.raise_for_status()
        return r.json()

    def run_command(self, vm_id: str, command: str) -> dict:
        r = requests.post(f"{self.base_url}/vms/{vm_id}/commands", json={"command": command})
        r.raise_for_status()
        return r.json()

    def write_file(self, vm_id: str, path: str, content: str) -> dict:
        r = requests.post(f"{self.base_url}/vms/{vm_id}/files", json={"path": path, "content": content})
        r.raise_for_status()
        return r.json()

    def read_file(self, vm_id: str, path: str) -> str:
        r = requests.get(f"{self.base_url}/vms/{vm_id}/files", params={"path": path})
        r.raise_for_status()
        return r.json()["content"]
```

`tools/executor.py` — connects tool calls to the sandbox:

```python
from sandbox.client import SandboxClient

class ToolExecutor:
    def __init__(self, sandbox: SandboxClient, vm_id: str):
        self.sandbox = sandbox
        self.vm_id = vm_id

    def execute(self, name: str, tool_input: dict) -> str:
        if name == "run_command":
            r = self.sandbox.run_command(self.vm_id, tool_input["command"])
            return f"exit_code={r['exit_code']}\nstdout:\n{r['stdout']}\nstderr:\n{r['stderr']}"
        if name == "write_file":
            self.sandbox.write_file(self.vm_id, tool_input["path"], tool_input["content"])
            return f"wrote {tool_input['path']}"
        if name == "read_file":
            return self.sandbox.read_file(self.vm_id, tool_input["path"])
        return f"unknown tool: {name}"
```

**Code Explanation:**
`run_command` uses `container.exec_run` — the Docker SDK's version of `docker exec` — which is the same job as the talk's custom "code execution server" running inside each guest. `write_file`/`read_file` use `put_archive`/`get_archive`, Docker's file-transfer primitive (a tar stream in/out), standing in for the talk's file-upload/download API. `ToolExecutor.execute` is a simple dispatch table: tool name in, sandbox action out, string result back to the LLM.

**Test:**
```bash
python3 - <<'EOF'
from sandbox.client import SandboxClient
from tools.executor import ToolExecutor

sandbox = SandboxClient()
vm_id = sandbox.create()
executor = ToolExecutor(sandbox, vm_id)

print(executor.execute("write_file", {"path": "hello.py", "content": "print('hi from sandbox')"}))
print(executor.execute("run_command", {"command": "python3 hello.py"}))
print(executor.execute("read_file", {"path": "hello.py"}))

sandbox.destroy(vm_id)
EOF
```

**Result:**
You see `wrote hello.py`, then `exit_code=0 ... stdout: hi from sandbox`, then the file's source code — all without the agent or your host shell ever running `python3` directly.

---

## Step 10: Snapshot & Restore (Backtracking)

**What:**
Let the agent checkpoint a sandbox's state and roll back to it later.

**Why:**
Straight from the talk: *"Agents fail when you give them a big task... you shouldn't have to start from scratch, you should be able to backtrack to the last good checkpoint, replan, and try again."* Arachis does this by pausing the VMM, dumping guest memory, and copying the read-write overlay layer. We can't dump memory in a container (there's no separate guest kernel state to freeze), but we *can* capture the filesystem state — which covers the common case: files the agent created or changed.

**Implementation:**

Add to `sandbox/manager.py`:

```python
class SnapshotRequest(BaseModel):
    snapshot_id: str

@app.post("/vms/{vm_id}/snapshots")
def snapshot_vm(vm_id: str, req: SnapshotRequest):
    container = get_container(vm_id)
    image = container.commit(repository="sandbox-snapshot", tag=req.snapshot_id)
    return {"vm_id": vm_id, "snapshot_id": req.snapshot_id, "image_id": image.id}

@app.post("/vms/{vm_id}/restore")
def restore_vm(vm_id: str, req: SnapshotRequest):
    old = get_container(vm_id)
    old.remove(force=True)
    new = client.containers.run(
        f"sandbox-snapshot:{req.snapshot_id}",
        name=vm_id,
        detach=True,
        tty=True,
        labels={"managed-by": LABEL},
    )
    return {"vm_id": vm_id, "restored_from": req.snapshot_id, "status": new.status}
```

Add to `sandbox/client.py`:

```python
    def snapshot(self, vm_id: str, snapshot_id: str) -> dict:
        r = requests.post(f"{self.base_url}/vms/{vm_id}/snapshots", json={"snapshot_id": snapshot_id})
        r.raise_for_status()
        return r.json()

    def restore(self, vm_id: str, snapshot_id: str) -> dict:
        r = requests.post(f"{self.base_url}/vms/{vm_id}/restore", json={"snapshot_id": snapshot_id})
        r.raise_for_status()
        return r.json()
```

**Code Explanation:**
`container.commit(...)` takes the container's current writable layer and freezes it as a new, reusable image — this is our stand-in for "dump the guest memory and persist the read-write overlay." `restore_vm` removes the live container and starts a fresh one **from that frozen image**, under the *same* `vm_id` name, so the rest of the system doesn't need to know a swap happened. The important limitation to remember: **running processes and in-memory state are lost** on restore — only files on disk survive. A real microVM snapshot (Cloud Hypervisor/Firecracker) captures guest memory too, so a process mid-execution really does resume exactly where it left off. That gap is the direct trade-off for using containers instead of microVMs.

**Test:**
```bash
python3 - <<'EOF'
from sandbox.client import SandboxClient
from tools.executor import ToolExecutor

sandbox = SandboxClient()
vm_id = sandbox.create()
executor = ToolExecutor(sandbox, vm_id)

executor.execute("write_file", {"path": "app.py", "content": "def add(a, b):\n    return a + b\n"})
sandbox.snapshot(vm_id, "v1-correct")

executor.execute("write_file", {"path": "app.py", "content": "def add(a, b):\n    return a - b  # bug!\n"})
print("BEFORE RESTORE:")
print(executor.execute("read_file", {"path": "app.py"}))

sandbox.restore(vm_id, "v1-correct")
print("AFTER RESTORE:")
print(executor.execute("read_file", {"path": "app.py"}))

sandbox.destroy(vm_id)
EOF
```

**Result:**
"BEFORE RESTORE" shows the buggy `a - b` version. "AFTER RESTORE" shows the original `a + b` version — the sandbox rolled back to the last good checkpoint, exactly like the talk's dark-mode demo (add a feature, then restore to the snapshot from before it was added).

---

## Step 11: Agent Execution Flow

**What:**
Wire the LLM, the tool schema, and the tool executor into one loop: the full ReAct-style agent (**Re**ason, **Act**, observe, repeat).

**Why:**
This is the piece that turns "an LLM" and "a sandbox" into an *agent*. The loop is simple on purpose — the talk's point is that most of the intelligence comes from the model already knowing Linux, not from a clever framework.

**Implementation:**

`agent/agent.py` (final version):

```python
from agent.llm_client import LLMClient
from tools.schema import TOOLS
from tools.executor import ToolExecutor
from sandbox.client import SandboxClient

SYSTEM_PROMPT = """You are an AI agent with access to a Linux sandbox via three tools:
run_command, write_file, read_file. Use them to complete the user's task step by step.
When the task is fully done, reply in plain text with no further tool calls."""


class Agent:
    def __init__(self, sandbox_url: str = "http://localhost:8000", model: str = "claude-sonnet-5"):
        self.sandbox = SandboxClient(sandbox_url)
        self.vm_id = self.sandbox.create()
        self.executor = ToolExecutor(self.sandbox, self.vm_id)
        self.llm = LLMClient(model=model)
        print(f"[agent] sandbox ready: {self.vm_id}")

    def run(self, task: str, max_turns: int = 8) -> str:
        messages = [{"role": "user", "content": task}]

        for _ in range(max_turns):
            response = self.llm.call(messages, tools=TOOLS, system=SYSTEM_PROMPT)
            messages.append({"role": "assistant", "content": response.content})

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                text = "".join(b.text for b in response.content if b.type == "text")
                print(f"[agent] final answer: {text}")
                return text

            tool_results = []
            for block in tool_uses:
                print(f"[agent] tool call: {block.name}({block.input})")
                result = self.executor.execute(block.name, block.input)
                print(f"[agent] tool result: {result[:300]}")
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result}
                )
            messages.append({"role": "user", "content": tool_results})

        return "max turns reached without a final answer"

    def cleanup(self):
        self.sandbox.destroy(self.vm_id)
        print(f"[agent] sandbox destroyed: {self.vm_id}")
```

`run.py`:

```python
from agent.agent import Agent

if __name__ == "__main__":
    agent = Agent()
    try:
        agent.run(
            "Create a file hello.py that prints 'Hello from the sandbox!', "
            "run it, and tell me exactly what it printed."
        )
    finally:
        agent.cleanup()
```

**Code Explanation:**
Each loop turn: (1) send the whole conversation so far to Claude, (2) if Claude answered with `tool_use` blocks, run each one through `ToolExecutor` and feed the results back as a `tool_result` message, (3) if Claude answered with only text, the task is done — return it. `max_turns` is a safety valve so a confused agent can't loop forever burning API calls.

**Test:**
```bash
# terminal 1
uvicorn sandbox.manager:app --port 8000

# terminal 2
python3 run.py
```

**Result:**
Terminal 2 prints a trace like:

```
[agent] sandbox ready: sandbox-a1b2c3d4
[agent] tool call: write_file({'path': 'hello.py', 'content': "print('Hello from the sandbox!')"})
[agent] tool result: wrote hello.py
[agent] tool call: run_command({'command': 'python3 hello.py'})
[agent] tool result: exit_code=0 stdout: Hello from the sandbox!
[agent] final answer: The script printed: Hello from the sandbox!
[agent] sandbox destroyed: sandbox-a1b2c3d4
```

---

## Step 12: Security / Isolation Considerations

**What:**
The Linux isolation mechanisms the talk walks through, and how to apply the strongest ones our sandbox can use.

**Why:**
Directly from the talk's threat model: *"This code could be buggy or malicious and can get root and access your data or your client's data."* Isolation is layered — no single mechanism is enough on its own. Here's the ladder, weakest to strongest, exactly as covered in the talk:

| Layer | What it does | Weakness |
|---|---|---|
| Plain process | Runs in the same kernel as everything else | A bug can touch anything the host process can touch |
| Namespaces (process, mount, network) | Container only sees its own processes/files/network | Still shares the **host kernel** — a kernel bug lets code escape |
| cgroups | Caps CPU/memory a container can use | Doesn't stop privilege escalation, only resource abuse |
| Capabilities | Removes specific root powers (e.g. can't load kernel modules) | Must be tuned; too permissive defaults are common |
| seccomp | Blocks dangerous syscalls outright | Requires a curated allow-list (the talk mentions `minijail` for this) |
| gVisor | A user-space kernel intercepts syscalls before they reach the host kernel | Better than containers, but still shares some kernel surface; also loses some perf and GPU access |
| microVM (Firecracker/Cloud Hypervisor) | Separate **guest kernel**, hardware-virtualized — the strongest boundary | Slower to reach than a container's "just exec" speed, though microVMs boot in seconds |

**Implementation:**

Harden `create_vm` and `restore_vm` in `sandbox/manager.py` with capabilities, seccomp, and resource limits:

```python
SANDBOX_RUNTIME_OPTS = dict(
    mem_limit="512m",
    nano_cpus=1_000_000_000,       # 1 vCPU worth of quota (cgroups)
    cap_drop=["ALL"],              # start from zero Linux capabilities
    security_opt=["no-new-privileges"],  # a process can't gain more privilege than it started with
    pids_limit=256,                # cap process count (fork-bomb protection)
)

@app.post("/vms")
def create_vm(publish_port: Optional[int] = None):
    vm_id = f"sandbox-{uuid.uuid4().hex[:8]}"
    ports = {f"{publish_port}/tcp": None} if publish_port else None
    container = client.containers.run(
        SANDBOX_IMAGE,
        name=vm_id,
        detach=True,
        tty=True,
        ports=ports,
        labels={"managed-by": LABEL},
        **SANDBOX_RUNTIME_OPTS,
    )
    container.reload()
    host_port = None
    if publish_port:
        binding = container.ports.get(f"{publish_port}/tcp")
        host_port = binding[0]["HostPort"] if binding else None
    return {"vm_id": vm_id, "status": container.status, "host_port": host_port}
```

Apply the same `**SANDBOX_RUNTIME_OPTS` to the `client.containers.run(...)` call inside `restore_vm` from Step 10, so restored sandboxes stay just as locked down as fresh ones.

**Code Explanation:**
`cap_drop=["ALL"]` removes every Linux capability (e.g. `CAP_SYS_ADMIN`, `CAP_NET_RAW`) — matching the talk's point that you "only give capabilities that are required, you don't give a catch-all." `no-new-privileges` blocks `setuid` tricks from regaining privilege. `mem_limit`/`nano_cpus` are cgroups doing exactly what the talk describes: "cgroups control how much memory and CPU a container can access." Docker's default seccomp profile is already applied automatically (it blocks ~44 dangerous syscalls); for a custom allow-list you'd pass `security_opt=["seccomp=./custom-profile.json"]`, the same idea as the talk's `minijail`.

**Test:**
```bash
VM_ID=$(curl -s -X POST http://localhost:8000/vms | python3 -c "import sys,json;print(json.load(sys.stdin)['vm_id'])")
docker exec $VM_ID sh -c "mount /dev/sda1 /mnt" 2>&1 | grep -i "not permitted\|denied"
```

**Result:**
The privileged `mount` call is refused — `Operation not permitted` — proving the dropped capabilities are actually enforced, not just configured.

> **If you need stronger isolation than this:** swap the sandbox runtime to gVisor by installing `runsc` and adding `runtime="runsc"` to `containers.run(...)` — no other code changes needed. For the strongest isolation (what Arachis actually uses in production), replace Docker entirely with a microVM VMM like Cloud Hypervisor or Firecracker behind the same REST interface — the `sandbox/client.py` and `tools/executor.py` code in this course would not need to change at all, because they only depend on the HTTP contract, not on Docker.

---

## Step 13: Scaling Considerations

**What:**
What changes when you go from "one sandbox on my laptop" to "many sandboxes serving many agents."

**Why:**
The talk names three concrete scaling goals for Arachis: fast boot, fast snapshots, and packing many sandboxes per host. Even without microVMs, the same knobs apply to our system.

**Implementation & discussion:**

1. **Boot time.** The talk reports Arachis boots a microVM in under 7 seconds (vs. ~40s for a traditional VM), with ongoing work to get under 1 second. Our containers boot in well under a second already (`time docker run ...`) — the trade-off is the weaker isolation from Step 12, not speed.

2. **Snapshot speed.** `container.commit()` (Step 10) is fast for small sandboxes but scans the whole writable layer. The talk mentions moving from `ext4` to `btrfs` specifically because `btrfs` supports **incremental** snapshots — only the changed blocks are copied. If you outgrow `docker commit`, look at mounting each sandbox's writable layer on a `btrfs` subvolume and using `btrfs snapshot` directly.

3. **Bin-packing many sandboxes per host.** This is exactly what `mem_limit` and `nano_cpus` (Step 12) are for — without them, one runaway sandbox can starve every other sandbox on the same host. Set both conservatively and monitor `docker stats`.

4. **Health and horizontal scaling.** The `/health` endpoint (Step 7) is what a load balancer or orchestrator polls to decide whether to route new sandbox requests to this manager instance. To scale out, run multiple copies of `sandbox/manager.py` on different hosts, each managing its own Docker daemon, behind a load balancer that checks `/health`.

```bash
# Watch resource usage across all running sandboxes live
docker stats --filter "label=managed-by=ai-sandbox"
```

5. **Memory ballooning (future work in the talk).** Cloud Hypervisor supports adding/removing RAM from a running VM as a hot-pluggable PCI device, so a host can reclaim idle memory from quiet sandboxes. Docker containers can't do this — `mem_limit` is fixed at creation time. This is one of the clearest gaps between "container as sandbox" and "microVM as sandbox," and exactly why the talk lists it as ongoing work even for a microVM-based system.

**Code Explanation:**
No new application code in this step — it's operational: the limits from Step 12 *are* the scaling levers, and `/health` is the hook an external system needs to scale the manager itself.

**Test:**
```bash
for i in 1 2 3; do curl -s -X POST http://localhost:8000/vms; echo; done
docker stats --no-stream --filter "label=managed-by=ai-sandbox"
```

**Result:**
Three sandboxes show up in `docker stats`, each capped at the memory/CPU limits from Step 12 — proof several sandboxes can share the host safely.

---

## Step 14: Complete Working Example

**What:**
The full project, all files together, as it stands after every step above.

**Why:**
So you can copy it in one pass and run it, rather than re-assembling diffs from each step.

**Final project tree:**

```text
ai-agent-sandbox/
├── agent/
│   ├── __init__.py
│   ├── llm_client.py
│   └── agent.py
├── tools/
│   ├── __init__.py
│   ├── schema.py
│   └── executor.py
├── sandbox/
│   ├── __init__.py
│   ├── Dockerfile
│   ├── manager.py
│   └── client.py
├── demo_snapshot.py
├── run.py
├── requirements.txt
└── README.md
```

**`sandbox/manager.py` (complete, final version):**

```python
import io
import tarfile
import uuid
from typing import Optional

import docker
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Sandbox Manager")
client = docker.from_env()

SANDBOX_IMAGE = "ai-sandbox:latest"
LABEL = "ai-sandbox"

SANDBOX_RUNTIME_OPTS = dict(
    mem_limit="512m",
    nano_cpus=1_000_000_000,
    cap_drop=["ALL"],
    security_opt=["no-new-privileges"],
    pids_limit=256,
)


class CommandRequest(BaseModel):
    command: str


class FileWriteRequest(BaseModel):
    path: str
    content: str


class SnapshotRequest(BaseModel):
    snapshot_id: str


def get_container(vm_id: str):
    try:
        return client.containers.get(vm_id)
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="sandbox not found")


@app.post("/vms")
def create_vm(publish_port: Optional[int] = None):
    vm_id = f"sandbox-{uuid.uuid4().hex[:8]}"
    ports = {f"{publish_port}/tcp": None} if publish_port else None
    container = client.containers.run(
        SANDBOX_IMAGE,
        name=vm_id,
        detach=True,
        tty=True,
        ports=ports,
        labels={"managed-by": LABEL},
        **SANDBOX_RUNTIME_OPTS,
    )
    container.reload()
    host_port = None
    if publish_port:
        binding = container.ports.get(f"{publish_port}/tcp")
        host_port = binding[0]["HostPort"] if binding else None
    return {"vm_id": vm_id, "status": container.status, "host_port": host_port}


@app.get("/vms")
def list_vms():
    containers = client.containers.list(all=True, filters={"label": f"managed-by={LABEL}"})
    return [{"vm_id": c.name, "status": c.status} for c in containers]


@app.delete("/vms/{vm_id}")
def delete_vm(vm_id: str):
    get_container(vm_id).remove(force=True)
    return {"vm_id": vm_id, "deleted": True}


@app.post("/vms/{vm_id}/commands")
def run_command(vm_id: str, req: CommandRequest):
    container = get_container(vm_id)
    exit_code, output = container.exec_run(
        cmd=["/bin/bash", "-lc", req.command], workdir="/workspace", demux=True
    )
    stdout, stderr = output
    return {
        "exit_code": exit_code,
        "stdout": stdout.decode() if stdout else "",
        "stderr": stderr.decode() if stderr else "",
    }


@app.post("/vms/{vm_id}/files")
def write_file(vm_id: str, req: FileWriteRequest):
    container = get_container(vm_id)
    data = req.content.encode()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name=req.path.lstrip("/"))
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    buf.seek(0)
    container.put_archive("/workspace", buf)
    return {"path": req.path, "bytes_written": len(data)}


@app.get("/vms/{vm_id}/files")
def read_file(vm_id: str, path: str):
    container = get_container(vm_id)
    try:
        stream, _ = container.get_archive(f"/workspace/{path.lstrip('/')}")
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="file not found")
    buf = io.BytesIO()
    for chunk in stream:
        buf.write(chunk)
    buf.seek(0)
    with tarfile.open(fileobj=buf) as tar:
        content = tar.extractfile(tar.getmembers()[0]).read()
    return {"path": path, "content": content.decode(errors="replace")}


@app.post("/vms/{vm_id}/snapshots")
def snapshot_vm(vm_id: str, req: SnapshotRequest):
    container = get_container(vm_id)
    image = container.commit(repository="sandbox-snapshot", tag=req.snapshot_id)
    return {"vm_id": vm_id, "snapshot_id": req.snapshot_id, "image_id": image.id}


@app.post("/vms/{vm_id}/restore")
def restore_vm(vm_id: str, req: SnapshotRequest):
    get_container(vm_id).remove(force=True)
    new = client.containers.run(
        f"sandbox-snapshot:{req.snapshot_id}",
        name=vm_id,
        detach=True,
        tty=True,
        labels={"managed-by": LABEL},
        **SANDBOX_RUNTIME_OPTS,
    )
    return {"vm_id": vm_id, "restored_from": req.snapshot_id, "status": new.status}


@app.get("/health")
def health():
    n = len(client.containers.list(filters={"label": f"managed-by={LABEL}"}))
    return {"status": "ok", "sandboxes": n}
```

All other files (`sandbox/client.py`, `tools/schema.py`, `tools/executor.py`, `agent/llm_client.py`, `agent/agent.py`, `run.py`) are exactly as written in Steps 5, 6, 9, 10, and 11 — nothing else changes.

**`demo_snapshot.py`** — a second entry point showing the backtracking workflow end-to-end through the agent (not just the client, like Step 10's test):

```python
from agent.agent import Agent

agent = Agent()
try:
    agent.run("Create app.py with a function add(a, b) that returns a + b.")
    agent.sandbox.snapshot(agent.vm_id, "v1-clean")
    print("--- snapshot 'v1-clean' saved ---")

    agent.run("Introduce a bug: change add(a, b) to return a - b instead.")
    print("--- app.py after the bug ---")
    print(agent.executor.execute("read_file", {"path": "app.py"}))

    agent.sandbox.restore(agent.vm_id, "v1-clean")
    print("--- restored to 'v1-clean' ---")
    print(agent.executor.execute("read_file", {"path": "app.py"}))
finally:
    agent.cleanup()
```

**`README.md`:**

```markdown
# AI Agent + Sandbox

A minimal AI agent that plans with Claude and executes every action inside an
isolated Docker sandbox instead of on the host machine.

## Run
1. `docker build -t ai-sandbox:latest -f sandbox/Dockerfile sandbox/`
2. `uvicorn sandbox.manager:app --port 8000`
3. `export ANTHROPIC_API_KEY=sk-ant-...`
4. `python3 run.py`

## Layout
- `sandbox/` — REST manager + Docker-based sandbox runtime + Python client
- `tools/` — tool schema (what the LLM can ask for) + executor (what actually runs)
- `agent/` — the LLM wrapper and the agent's reasoning loop
```

**Code Explanation:**
Nothing new conceptually — this step is deliberately just consolidation, matching the talk's own "let's put it all together" moment before its live demo.

**Test:**
See Step 15.

**Result:**
A directory you can `git init` and run on any machine with Docker + an Anthropic key.

---

## Step 15: How to Run and Test

**What:**
The exact commands to go from a clean checkout to a working agent run.

**Why:**
A course isn't complete until "clone and run" actually works.

**Implementation:**

```bash
# 0. One-time setup
cd ai-agent-sandbox
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker build -t ai-sandbox:latest -f sandbox/Dockerfile sandbox/
export ANTHROPIC_API_KEY="sk-ant-..."

# 1. Start the sandbox manager (leave running in its own terminal)
uvicorn sandbox.manager:app --port 8000

# 2. In a second terminal: sanity-check the manager
curl http://localhost:8000/health

# 3. Run the agent on a real task
python3 run.py

# 4. Run the snapshot/backtracking demo
python3 demo_snapshot.py

# 5. Confirm no leftover sandboxes remain
curl http://localhost:8000/vms
```

**Code Explanation:**
Step 1 must stay running the whole time — it's the service the agent's `SandboxClient` talks to. Step 5's `/vms` should return `[]` after each run, since `Agent.cleanup()` destroys its sandbox in a `finally` block.

**Test:**
Run all 5 numbered commands in order.

**Result:**

- `/health` → `{"status": "ok", "sandboxes": 0}`
- `run.py` → a full tool-call trace ending in Claude confirming the printed output
- `demo_snapshot.py` → shows the buggy version, then the restored clean version of `app.py`
- Final `/vms` check → `[]` — every sandbox was cleaned up

---

## Step 16: Final Architecture / Summary

**What:**
The complete system, one last time, with every piece labeled.

**Implementation:**

```
                         ┌───────────────────────────────────────────┐
                         │                 Agent Process              │
                         │                                             │
   task ───────────────▶│  Agent.run()  ◀──▶  LLMClient  ◀──▶ Claude  │
                         │       │                                     │
                         │       ▼                                     │
                         │  ToolExecutor.execute(tool_name, input)     │
                         └───────┬─────────────────────────────────────┘
                                 │ HTTP (SandboxClient)
                                 ▼
                    ┌─────────────────────────────────────┐
                    │        Sandbox Manager (FastAPI)      │
                    │  /vms  /vms/{id}/commands             │
                    │  /vms/{id}/files  /vms/{id}/snapshots │
                    │  /vms/{id}/restore  /health           │
                    └───────────────┬───────────────────────┘
                                    │ docker SDK
                                    ▼
                     ┌───────────────────────────────────────┐
                     │              Docker Engine              │
                     │  overlay2 storage (shared base + RW)    │
                     │  bridge network + iptables NAT          │
                     │  cgroups (mem/cpu/pids) + capabilities  │
                     │                                          │
                     │   ┌────────────┐   ┌────────────┐       │
                     │   │ Sandbox A  │   │ Sandbox B  │  ...  │
                     │   └────────────┘   └────────────┘       │
                     └───────────────────────────────────────┘
```

**Summary table — talk concept → what we shipped:**

| From the talk | We built |
|---|---|
| Why AI needs sandboxes (tool calling, RL, untrusted agent code) | The whole reason `tools/executor.py` never touches the host directly |
| REST server + VMM | `sandbox/manager.py` + Docker Engine |
| microVM (Cloud Hypervisor) | Docker container (documented trade-off in Step 12) |
| Shared read-only root FS + per-sandbox RW layer | Docker's `overlay2` driver |
| tap device + Linux bridge + iptables port forwarding | Docker bridge network + `publish_port` |
| Code execution + files API inside the guest | `run_command` / `read_file` / `write_file` endpoints |
| Snapshot (pause, dump memory, persist RW layer, resume) | `docker commit` + restore-from-image (filesystem only) |
| Capabilities, seccomp, jailing | `cap_drop`, `security_opt`, Docker's default seccomp profile |
| Python SDK | `sandbox/client.py` |
| Health check endpoint for distributed setups | `/health` |
| Agent using the sandbox with minimal prompting, backtracking on failure | `agent/agent.py` + `demo_snapshot.py` |

You now have a working, from-scratch version of every major piece in the talk, plus a clear map of exactly where a production system (using real microVMs) would go further.

---

## Step 17 (Extension): Beyond This Course

Two things the talk covers that this course intentionally kept out of the main runnable path, so it stays simple to run everywhere. Both slot into the architecture above without changing `agent/` or `tools/`.

**A. Browser / computer use.** The talk's sandbox ships Chrome pre-installed with a VNC server, so an agent can drive a real browser GUI. To add this: extend `sandbox/Dockerfile` with `chromium-browser`, `xvfb` (a virtual display), and `x11vnc`; start them in the container's entrypoint instead of `sleep infinity`; then use the `publish_port` mechanism from Step 8 to expose the VNC port. A VNC client on your host can then connect to `localhost:<host_port>` and see the sandbox's screen — same idea as the talk's demo, at smaller scale.

**B. Exposing the sandbox over MCP.** In the talk's live demo, Claude Desktop drives Arachis directly through an MCP server, instead of a hand-written agent loop. You can offer the same sandbox this course built to any MCP-compatible client by wrapping `sandbox/client.py`'s methods (`create`, `run_command`, `read_file`, `write_file`, `snapshot`, `restore`) as MCP tools using the `mcp` Python package's server SDK — the sandbox manager itself does not change at all, since MCP would just be a second, alternative front door onto the same REST API.
