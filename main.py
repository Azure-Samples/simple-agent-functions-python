"""Foundry hosted-agent-compatible entry point for the repo digest agent."""

from dotenv import load_dotenv

load_dotenv()

from agent_framework_foundry_hosting import ResponsesHostServer
from repo_digest_agent import build_agent


def main() -> None:
    ResponsesHostServer(build_agent()).run()


if __name__ == "__main__":
    main()
