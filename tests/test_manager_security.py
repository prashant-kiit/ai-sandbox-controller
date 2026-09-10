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


def _assert_mount_denied(base_url, vm_id):
    r = requests.post(f"{base_url}/vms/{vm_id}/commands", json={"command": "mount /dev/sda1 /mnt"})
    assert r.status_code == 200
    body = r.json()
    assert body["exit_code"] != 0
    combined_output = (body["stdout"] + body["stderr"]).lower()
    assert "not permitted" in combined_output or "denied" in combined_output


def test_created_vm_denies_privileged_mount(base_url, vm):
    _assert_mount_denied(base_url, vm)


def test_restored_vm_also_denies_privileged_mount(base_url, vm, snapshot_tag):
    snap_resp = requests.post(f"{base_url}/vms/{vm}/snapshots", json={"snapshot_id": snapshot_tag})
    assert snap_resp.status_code == 200

    restore_resp = requests.post(f"{base_url}/vms/{vm}/restore", json={"snapshot_id": snapshot_tag})
    assert restore_resp.status_code == 200

    _assert_mount_denied(base_url, vm)
