import os
from openai import OpenAI


class LLMClient:
    """Thin wrapper so the rest of the agent never touches the SDK directly."""

    def __init__(self, model: str | None = None):
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")

    def call(self, messages, tools=None, system=None):
        full_messages = ([{"role": "system", "content": system}] if system else []) + messages
        kwargs = {"model": self.model, "messages": full_messages}
        if tools:
            kwargs["tools"] = tools
        return self.client.chat.completions.create(**kwargs)
