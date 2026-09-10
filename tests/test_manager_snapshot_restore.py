import uuid

import docker
import pytest
import requests


@pytest.fixture
def snapshot_tag():
    tag = f"test-{uuid.uuid4().hex[:8]}"
    yield tag
    docker_client = docker.from_env()
    try:
        docker_client.images.remove(f"sandbox-snapshot:{tag}", force=True)
    except docker.errors.ImageNotFound:
        pass


def test_snapshot_and_restore_round_trip(base_url, vm, snapshot_tag):
    clean_content = "def add(a, b):\n    return a + b\n"
    buggy_content = "def add(a, b):\n    return a - b  # bug!\n"

    write_resp = requests.post(f"{base_url}/vms/{vm}/files", json={"path": "app.py", "content": clean_content})
    assert write_resp.status_code == 200

    snap_resp = requests.post(f"{base_url}/vms/{vm}/snapshots", json={"snapshot_id": snapshot_tag})
    assert snap_resp.status_code == 200
    snap_body = snap_resp.json()
    assert snap_body["vm_id"] == vm
    assert snap_body["snapshot_id"] == snapshot_tag
    assert snap_body["image_id"]

    buggy_resp = requests.post(f"{base_url}/vms/{vm}/files", json={"path": "app.py", "content": buggy_content})
    assert buggy_resp.status_code == 200

    before_restore = requests.get(f"{base_url}/vms/{vm}/files", params={"path": "app.py"})
    assert before_restore.json()["content"] == buggy_content

    restore_resp = requests.post(f"{base_url}/vms/{vm}/restore", json={"snapshot_id": snapshot_tag})
    assert restore_resp.status_code == 200
    restore_body = restore_resp.json()
    assert restore_body["vm_id"] == vm
    assert restore_body["restored_from"] == snapshot_tag

    after_restore = requests.get(f"{base_url}/vms/{vm}/files", params={"path": "app.py"})
    assert after_restore.json()["content"] == clean_content
