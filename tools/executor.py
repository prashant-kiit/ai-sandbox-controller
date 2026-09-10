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
