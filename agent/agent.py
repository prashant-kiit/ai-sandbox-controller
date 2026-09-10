from agent.llm_client import LLMClient


class Agent:
    def __init__(self, model: str | None = None):
        self.llm = LLMClient(model=model)

    def run(self, task: str) -> str:
        messages = [{"role": "user", "content": task}]
        response = self.llm.call(messages)
        text = response.choices[0].message.content
        print(f"[agent] {text}")
        return text


if __name__ == "__main__":
    Agent().run("Say hello and tell me what you can help with in one sentence.")
