import json

from agent.llm_client import LLMClient
from sandbox.client import SandboxClient
from tools.executor import ToolExecutor
from tools.schema import TOOLS

SYSTEM_PROMPT = """You are an AI agent with access to a Linux sandbox via three tools:
run_command, write_file, read_file. Use them to complete the user's task step by step.
When the task is fully done, reply in plain text with no further tool calls."""


class Agent:
    def __init__(self, sandbox_url: str = "http://localhost:8000", model: str | None = None):
        self.sandbox = SandboxClient(sandbox_url)
        self.vm_id = self.sandbox.create()
        self.executor = ToolExecutor(self.sandbox, self.vm_id)
        self.llm = LLMClient(model=model)
        print(f"[agent] sandbox ready: {self.vm_id}")

    def run(self, task: str, max_turns: int = 8) -> str:
        messages = [{"role": "user", "content": task}]

        for _ in range(max_turns):
            response = self.llm.call(messages, tools=TOOLS, system=SYSTEM_PROMPT)
            message = response.choices[0].message
            messages.append(message.model_dump(exclude_none=True))

            tool_calls = message.tool_calls or []
            if not tool_calls:
                text = message.content
                print(f"[agent] final answer: {text}")
                return text

            for call in tool_calls:
                tool_input = json.loads(call.function.arguments)
                print(f"[agent] tool call: {call.function.name}({tool_input})")
                result = self.executor.execute(call.function.name, tool_input)
                print(f"[agent] tool result: {result[:300]}")
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

        return "max turns reached without a final answer"

    def cleanup(self):
        self.sandbox.destroy(self.vm_id)
        print(f"[agent] sandbox destroyed: {self.vm_id}")
