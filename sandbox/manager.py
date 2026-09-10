import uuid
from typing import Optional

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
