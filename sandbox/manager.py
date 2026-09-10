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


class CommandRequest(BaseModel):
    command: str


class FileWriteRequest(BaseModel):
    path: str
    content: str


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


@app.get("/health")
def health():
    n = len(client.containers.list(filters={"label": f"managed-by={LABEL}"}))
    return {"status": "ok", "sandboxes": n}
