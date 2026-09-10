TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command inside the Linux sandbox and get back stdout/stderr/exit code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "A bash command, e.g. 'python3 app.py'"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text content to a file inside the sandbox (creates or overwrites it).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path relative to /workspace"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file from inside the sandbox.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Path relative to /workspace"}},
                "required": ["path"],
            },
        },
    },
]
