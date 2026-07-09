# Daily Repo Digest QuickStart (Python Copilot SDK on Azure Functions)

A simple AI agent built with the GitHub Copilot SDK, running as an Azure Function. It creates live daily GitHub repository digests for recent pull requests, issues, and workflow failures. The default repository is `microsoft-foundry/foundry-samples`.

> Looking for [C#](https://github.com/Azure-Samples/simple-agent-functions-dotnet) or [TypeScript](https://github.com/Azure-Samples/simple-agent-functions-typescript)?

## Prerequisites

- Python 3.13+ via [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local#install-the-azure-functions-core-tools)
- [Azure Developer CLI (azd)](https://aka.ms/azd-install) (only needed for deploying Microsoft Foundry resources)
- Access to an AI model via one of:
  - **GitHub Copilot subscription** - models are available automatically
  - **Bring Your Own Key (BYOK)** - use an API key from [Microsoft Foundry](https://ai.azure.com) (see [BYOK docs](https://github.com/github/copilot-sdk/blob/main/docs/auth/byok.md))

## Quickstart

> **Want to use your own models?** See [Deploy Microsoft Foundry Resources](#deploy-microsoft-foundry-resources) below to provision a Microsoft Foundry project instead of using GitHub Copilot models.

1. Clone the repository

2. Install dependencies:

   ```bash
   uv sync
   ```

3. Run the function locally:

   ```bash
   uv run func start
   ```

4. Test the digest agent (in a new terminal):

   ```bash
   # Interactive chat client
   uv run chat.py

   # Or use curl directly
   curl -X POST http://localhost:7071/api/ask \
     -d "Create a concise daily repo digest for microsoft-foundry/foundry-samples."
   ```

   To chat with a deployed instance, grab the URL and function key from your `azd` environment:

   ```bash
   export AGENT_URL=$(azd env get-value SERVICE_API_URI)
   export FUNCTION_KEY=$(az functionapp keys list \
     -n $(azd env get-value AZURE_FUNCTION_APP_NAME) \
     -g $(azd env get-value RESOURCE_GROUP) \
     --query "functionKeys.default" -o tsv)

   uv run chat.py
   ```

## Source Code

The agent logic is in [`function_app.py`](function_app.py). It creates a `CopilotClient`, fetches live public GitHub data through REST APIs, and asks the model to produce a concise daily digest. The sample keeps the Azure Functions hosting model from this repo and exposes:

- An HTTP endpoint at `/api/ask` for chat or API requests.
- A timer-triggered function named `daily_repo_digest` that runs the digest at 9 AM Pacific.
- An MCP tool named `get_repo_digest_context` at `/runtime/webhooks/mcp`.

[`chat.py`](chat.py) is a lightweight console client that POSTs messages to the function in a loop, giving you an interactive chat experience. It defaults to `http://localhost:7071` but can be pointed at a deployed instance via the `AGENT_URL` environment variable.

Ask for a digest with an optional public repo such as `microsoft-foundry/foundry-samples`. If you omit the repo, the agent uses `microsoft-foundry/foundry-samples` by default. Set `GITHUB_REPOSITORY` to change the default repository. Set `GITHUB_TOKEN` only if you want higher public GitHub API rate limits.

Local development uses [`pyproject.toml`](pyproject.toml) with `uv sync` and `uv run`. [`requirements.txt`](requirements.txt) is kept for Azure Functions packaging and should stay aligned with the dependencies in `pyproject.toml`.

## Daily Schedule

The timer trigger uses the Azure Functions NCRONTAB schedule `0 0 16,17 * * *`. Azure Functions timer schedules run in UTC for this Linux Functions sample, so the function wakes at both possible 9 AM Pacific UTC offsets and only creates a digest when the current `America/Los_Angeles` hour is 9. This keeps the sample aligned with Pacific daylight and standard time without adding a separate scheduler service.

## MCP extension tutorial

This sample also exposes the live repo data fetcher as an Azure Functions MCP extension tool, then shows how to consume that tool from the Copilot SDK. The implementation uses the Python v2 Functions programming model:

```python
@app.mcp_tool()
@app.mcp_tool_property(
    arg_name="repository",
    description="Public GitHub repository in owner/name format.",
    is_required=False,
)
def get_repo_digest_context(repository: str = DEFAULT_REPOSITORY) -> str:
    return json.dumps(_repo_digest_context(repository), indent=2)
```

The Functions MCP extension exposes the server at:

```text
http://localhost:7071/runtime/webhooks/mcp
```

For a deployed Function App, use:

```text
https://<app-name>.azurewebsites.net/runtime/webhooks/mcp
```

Remote endpoints require the `mcp_extension` system key unless you change `host.json` to use anonymous webhook authorization. Get the deployed key with:

```bash
az functionapp keys list \
  --resource-group <resource-group> \
  --name <function-app-name> \
  --query systemKeys.mcp_extension \
  --output tsv
```

To have this sample consume its own MCP tool from the Copilot SDK, set:

```bash
export COPILOT_MCP_SERVER_URL="http://localhost:7071/runtime/webhooks/mcp"

# Only needed for a deployed Function App endpoint.
export MCP_EXTENSION_KEY="<mcp_extension system key>"
```

When `COPILOT_MCP_SERVER_URL` is set, `function_app.py` passes this MCP server into `CopilotClient.create_session`:

```python
config["mcp_servers"] = {
    "repo-digest-functions": {
        "type": "http",
        "url": mcp_server_url,
        "headers": headers,
        "tools": ["get_repo_digest_context"],
    }
}
```

Then the digest prompt tells the model to call `get_repo_digest_context` for live GitHub data. If `COPILOT_MCP_SERVER_URL` is not set, the sample falls back to fetching public GitHub REST data directly before sending the prompt to the model.

For the underlying Functions MCP extension docs, see [Tutorial: Host an MCP server on Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-mcp-tutorial), [Model context protocol bindings for Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-mcp), and [MCP tool trigger for Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-mcp-tool-trigger). For the Copilot SDK side, see [Using MCP servers with the GitHub Copilot SDK](https://github.com/github/copilot-sdk/blob/main/docs/features/mcp.md).

## Deploy Microsoft Foundry Resources

If you prefer to use your own models via BYOK and don't already have a Microsoft Foundry project with a model deployed:

```bash
azd auth login
azd up
```

This provisions all resources and configures local development automatically.

### What Gets Deployed

- Microsoft Foundry project with GPT-5-mini model
- Azure Functions app (Python, Flex Consumption plan)
- Storage, monitoring, and all necessary RBAC role assignments
- Optional: Search for vector store (disabled by default)
- Optional: Cosmos DB for agent thread storage (disabled by default)

## Using Microsoft Foundry (BYOK)

By default the agent uses GitHub Copilot's models. To use your own model from Microsoft Foundry instead, set these environment variables:

```bash
export AZURE_OPENAI_ENDPOINT="https://<your-ai-services>.openai.azure.com/"
export AZURE_OPENAI_API_KEY="<your-api-key>"
export AZURE_OPENAI_MODEL="gpt-5-mini"  # optional, defaults to gpt-5-mini
```

**Getting these values:**
- If you ran `azd up`, the endpoint is already in your environment. Run `azd env get-values | grep AZURE_OPENAI_ENDPOINT`
- For the API key, go to [Azure Portal](https://portal.azure.com), your AI Services resource, **Keys and Endpoint**, then select the **Azure OpenAI** tab
- Or find both in the [Microsoft Foundry portal](https://ai.azure.com) under your project settings

See the [BYOK docs](https://github.com/github/copilot-sdk/blob/main/docs/auth/byok.md) for details.

## Next steps

- Add tools and data sources with Azure Functions custom bindings, Python helpers, or MCP integration: [Model context protocol bindings for Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-mcp) and [connect MCP server endpoints to Foundry agents](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol).
- Build durable, long-running Functions workflows: [Durable Functions overview](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview) and [Azure Functions timer triggers](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-timer).

## Learn More

- [GitHub Copilot SDK](https://github.com/github/copilot-sdk)
- [Copilot SDK Python docs](https://github.com/github/copilot-sdk/tree/main/python)
- [BYOK (Bring Your Own Key)](https://github.com/github/copilot-sdk/blob/main/docs/auth/byok.md)
- [Azure Developer CLI](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/)
