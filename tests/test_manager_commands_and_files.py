import requests

from sandbox.client import SandboxClient
from tools.executor import ToolExecutor


def test_run_command_stdout_and_exit_code(base_url, vm):
    r = requests.post(f"{base_url}/vms/{vm}/commands", json={"command": "echo hello"})
    assert r.status_code == 200
    body = r.json()
    assert body["exit_code"] == 0
    assert body["stdout"].strip() == "hello"
    assert body["stderr"] == ""


def test_run_command_nonzero_exit_code(base_url, vm):
    r = requests.post(f"{base_url}/vms/{vm}/commands", json={"command": "exit 7"})
    assert r.status_code == 200
    assert r.json()["exit_code"] == 7


def test_write_read_round_trip(base_url, vm):
    content = "print('hi from sandbox')"
    write_resp = requests.post(f"{base_url}/vms/{vm}/files", json={"path": "hello.py", "content": content})
    assert write_resp.status_code == 200
    assert write_resp.json() == {"path": "hello.py", "bytes_written": len(content)}

    read_resp = requests.get(f"{base_url}/vms/{vm}/files", params={"path": "hello.py"})
    assert read_resp.status_code == 200
    assert read_resp.json()["content"] == content


def test_read_missing_file_404(base_url, vm):
    r = requests.get(f"{base_url}/vms/{vm}/files", params={"path": "does_not_exist.txt"})
    assert r.status_code == 404


def test_tool_executor_dispatch_write_run_read(base_url, vm):
    sandbox = SandboxClient(base_url)
    executor = ToolExecutor(sandbox, vm)

    write_result = executor.execute("write_file", {"path": "hello.py", "content": "print('hi from sandbox')"})
    assert write_result == "wrote hello.py"

    run_result = executor.execute("run_command", {"command": "python3 hello.py"})
    assert "exit_code=0" in run_result
    assert "hi from sandbox" in run_result

    read_result = executor.execute("read_file", {"path": "hello.py"})
    assert read_result == "print('hi from sandbox')"
