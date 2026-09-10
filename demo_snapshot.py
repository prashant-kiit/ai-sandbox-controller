from agent.agent import Agent

agent = Agent()
try:
    agent.run("Create app.py with a function add(a, b) that returns a + b.")
    agent.sandbox.snapshot(agent.vm_id, "v1-clean")
    print("--- snapshot 'v1-clean' saved ---")

    agent.run("Introduce a bug: change add(a, b) to return a - b instead.")
    print("--- app.py after the bug ---")
    print(agent.executor.execute("read_file", {"path": "app.py"}))

    agent.sandbox.restore(agent.vm_id, "v1-clean")
    print("--- restored to 'v1-clean' ---")
    print(agent.executor.execute("read_file", {"path": "app.py"}))
finally:
    agent.cleanup()
