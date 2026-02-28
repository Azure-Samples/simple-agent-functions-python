import os
import azure.functions as func
from copilot import CopilotClient, PermissionHandler

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
    config = {
        "system_message": {"content": instructions},
        "on_permission_request": PermissionHandler.approve_all,
    }
    base_url = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    model = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME") or os.environ.get("AZURE_OPENAI_MODEL", "gpt-5-mini")
    if base_url:
        config["model"] = model
        provider = {"type": "azure", "base_url": base_url}
        if api_key:
            provider["api_key"] = api_key
        else:
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            provider["bearer_token"] = token.token
        config["provider"] = provider
    return config


@app.route(route="ask", methods=["POST"])
async def ask(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP trigger that sends a message to the Copilot SDK agent."""
    prompt = req.get_body().decode("utf-8") or "What are the laws?"

    session = await client.create_session(_session_config())

    reply = await session.send_and_wait({"prompt": prompt})
    response_text = (reply.data.content if reply and reply.data else None) or "No response"

    await session.destroy()

    return func.HttpResponse(response_text, mimetype="text/plain")
