from agent.agent import Agent

if __name__ == "__main__":
    agent = Agent()
    try:
        agent.run(
            "Create a file hello.py that prints 'Hello from the sandbox!', "
            "run it, and tell me exactly what it printed."
        )
    finally:
        agent.cleanup()
