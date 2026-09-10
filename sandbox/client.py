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

    def snapshot(self, vm_id: str, snapshot_id: str) -> dict:
        r = requests.post(f"{self.base_url}/vms/{vm_id}/snapshots", json={"snapshot_id": snapshot_id})
        r.raise_for_status()
        return r.json()

    def restore(self, vm_id: str, snapshot_id: str) -> dict:
        r = requests.post(f"{self.base_url}/vms/{vm_id}/restore", json={"snapshot_id": snapshot_id})
        r.raise_for_status()
        return r.json()
