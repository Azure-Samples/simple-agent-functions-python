"""Foundry hosted-agent entry point for the Simple Agent sample."""
import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

INSTRUCTIONS = """
1. A robot may not injure a human being...
2. A robot must obey orders given it by human beings...
3. A robot must protect its own existence...

Objective: Give me the TLDR in exactly 5 words.
"""
DEFAULT_MODEL_DEPLOYMENT = "gpt-5-mini"


def _project_endpoint() -> str:
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT") or os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
    if not endpoint:
        raise RuntimeError("Set FOUNDRY_PROJECT_ENDPOINT to your Microsoft Foundry project endpoint.")
    return endpoint


def main() -> None:
    client = FoundryChatClient(
        project_endpoint=_project_endpoint(),
        model=os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME")
        or os.environ.get("FOUNDRY_MODEL")
        or DEFAULT_MODEL_DEPLOYMENT,
        credential=DefaultAzureCredential(),
    )

    agent = Agent(
        client=client,
        instructions=INSTRUCTIONS,
        default_options={"store": False},
    )

    server = ResponsesHostServer(agent)
    server.run()


if __name__ == "__main__":
    main()
