import requests


def test_health_ok(base_url):
    r = requests.get(f"{base_url}/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert isinstance(body["sandboxes"], int)


def test_create_list_delete_vm(base_url):
    create_resp = requests.post(f"{base_url}/vms")
    assert create_resp.status_code == 200
    vm_id = create_resp.json()["vm_id"]
    assert vm_id.startswith("sandbox-")

    list_resp = requests.get(f"{base_url}/vms")
    assert list_resp.status_code == 200
    vm_ids = [v["vm_id"] for v in list_resp.json()]
    assert vm_id in vm_ids

    delete_resp = requests.delete(f"{base_url}/vms/{vm_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json() == {"vm_id": vm_id, "deleted": True}

    list_resp_after = requests.get(f"{base_url}/vms")
    vm_ids_after = [v["vm_id"] for v in list_resp_after.json()]
    assert vm_id not in vm_ids_after


def test_delete_missing_vm_404(base_url):
    r = requests.delete(f"{base_url}/vms/sandbox-doesnotexist")
    assert r.status_code == 404


def test_vm_fixture_creates_and_cleans_up(vm, base_url):
    list_resp = requests.get(f"{base_url}/vms")
    vm_ids = [v["vm_id"] for v in list_resp.json()]
    assert vm in vm_ids


def test_create_vm_with_publish_port(base_url):
    create_resp = requests.post(f"{base_url}/vms", params={"publish_port": 8080})
    assert create_resp.status_code == 200
    body = create_resp.json()
    vm_id = body["vm_id"]
    try:
        assert body["host_port"] is not None
        int(body["host_port"])  # host_port is a real port number
    finally:
        requests.delete(f"{base_url}/vms/{vm_id}")


def test_create_vm_without_publish_port_has_no_host_port(base_url):
    create_resp = requests.post(f"{base_url}/vms")
    body = create_resp.json()
    vm_id = body["vm_id"]
    try:
        assert body["host_port"] is None
    finally:
        requests.delete(f"{base_url}/vms/{vm_id}")
