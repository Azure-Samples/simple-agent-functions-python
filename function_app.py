import os
import azure.functions as func
from copilot import CopilotClient

app = func.FunctionApp()
client = CopilotClient()

instructions = """
    1. A robot may not injure a human being...
    2. A robot must obey orders given it by human beings...
    3. A robot must protect its own existence...
    
    Objective: Give me the TLDR in exactly 5 words.
    """


def _session_config():
    """Build session config, optionally using Azure Foundry as provider."""
    config = {"system_message": {"content": instructions}}
    base_url = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    model = os.environ.get("AZURE_OPENAI_MODEL", "gpt-5-mini")
    if base_url and api_key:
        config["model"] = model
        config["provider"] = {
            "type": "azure",
            "base_url": base_url,
            "api_key": api_key,
        }
    return config


@app.route(route="ask", methods=["POST"])
async def ask(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP trigger that sends a message to the Copilot SDK agent."""
    prompt = req.get_body().decode("utf-8") or "What are the laws?"

    session = await client.create_session(_session_config())

    reply = await session.send_and_wait({"prompt": prompt})
    response_text = reply.data.content if reply else "No response"

    await session.destroy()

    return func.HttpResponse(response_text, mimetype="text/plain")
