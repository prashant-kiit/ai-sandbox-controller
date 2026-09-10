import os
import subprocess
import sys
import time
from pathlib import Path

import docker
import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
SANDBOX_DIR = REPO_ROOT / "sandbox"
SANDBOX_IMAGE = "ai-sandbox:latest"
MANAGER_PORT = 8000
BASE_URL = f"http://localhost:{MANAGER_PORT}"


@pytest.fixture(scope="session", autouse=True)
def _preconditions():
    try:
        docker.from_env().ping()
    except Exception as exc:
        raise RuntimeError(f"Docker daemon is not reachable: {exc}") from exc
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY must be set in the environment for the test suite to run")


@pytest.fixture(scope="session")
def _sandbox_image(_preconditions):
    docker_client = docker.from_env()
    try:
        docker_client.images.get(SANDBOX_IMAGE)
    except docker.errors.ImageNotFound:
        docker_client.images.build(path=str(SANDBOX_DIR), dockerfile="Dockerfile", tag=SANDBOX_IMAGE)
    return SANDBOX_IMAGE


@pytest.fixture(scope="session")
def base_url(_sandbox_image):
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "sandbox.manager:app", "--port", str(MANAGER_PORT)],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    deadline = time.time() + 30
    last_error = None
    try:
        while time.time() < deadline:
            if proc.poll() is not None:
                raise RuntimeError("sandbox manager subprocess exited before becoming healthy")
            try:
                r = requests.get(f"{BASE_URL}/health", timeout=1)
                if r.status_code == 200:
                    break
            except requests.exceptions.RequestException as exc:
                last_error = exc
            time.sleep(0.5)
        else:
            raise RuntimeError(f"sandbox manager did not become healthy in time: {last_error}")

        yield BASE_URL
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture
def vm(base_url):
    r = requests.post(f"{base_url}/vms")
    r.raise_for_status()
    vm_id = r.json()["vm_id"]
    try:
        yield vm_id
    finally:
        requests.delete(f"{base_url}/vms/{vm_id}")
