# Daily Repo Digest QuickStart (Python Copilot SDK on Azure Functions)

A simple AI agent built with the GitHub Copilot SDK, running as an Azure Function. It creates live daily GitHub repository digests for recent pull requests, issues, and workflow failures. The default repository is `Azure/azure-functions-host`.

> Looking for [C#](https://github.com/Azure-Samples/simple-agent-functions-dotnet) or [TypeScript](https://github.com/Azure-Samples/simple-agent-functions-typescript)?

## Prerequisites

- Python 3.13+ via [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local#install-the-azure-functions-core-tools)
- [Azurite](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite) for local Azure Functions storage
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

3. Start Azurite in a separate terminal:

   ```bash
   azurite --skipApiVersionCheck --silent --location ./.azurite
   ```

4. Run the function locally:

   ```bash
   uv run func start
   ```

5. Test the digest agent in another terminal:

   ```bash
   # Interactive chat client
   uv run chat.py

   # Or use curl directly
   curl -X POST http://localhost:7071/api/ask \
     -d "Create a concise daily repo digest for Azure/azure-functions-host."
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

[`chat.py`](chat.py) is a lightweight console client that POSTs messages to the function in a loop, giving you an interactive chat experience. It defaults to `http://localhost:7071` but can be pointed at a deployed instance via the `AGENT_URL` environment variable.

Ask for a digest with an optional public repo such as `Azure/azure-functions-host`. If you omit the repo, the agent uses `Azure/azure-functions-host` by default. Set `GITHUB_REPOSITORY` to change the default repository. Set `GITHUB_TOKEN` only if you want higher public GitHub API rate limits.

Local development uses [`pyproject.toml`](pyproject.toml) with `uv sync` and `uv run`. [`requirements.txt`](requirements.txt) is kept for Azure Functions packaging and should stay aligned with the dependencies in `pyproject.toml`.

## Daily Schedule

The timer trigger uses the Azure Functions NCRONTAB schedule `0 0 16,17 * * *`. Azure Functions timer schedules run in UTC for this Linux Functions sample, so the function wakes at both possible 9 AM Pacific UTC offsets and only creates a digest when the current `America/Los_Angeles` hour is 9. This keeps the sample aligned with Pacific daylight and standard time without adding a separate scheduler service.

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

- Add tools and data sources with Azure Functions custom bindings, Python helpers, or MCP integration: [MCP extension notes for this sample](MCP-extension-notes.md), [Tutorial: Host an MCP server on Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-mcp-tutorial), and [connect MCP server endpoints to Foundry agents](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol).
- Build durable, long-running Functions workflows: [Durable Functions overview](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview) and [Azure Functions timer triggers](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-timer).

## Learn More

- [GitHub Copilot SDK](https://github.com/github/copilot-sdk)
- [Copilot SDK Python docs](https://github.com/github/copilot-sdk/tree/main/python)
- [BYOK (Bring Your Own Key)](https://github.com/github/copilot-sdk/blob/main/docs/auth/byok.md)
- [Azure Developer CLI](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/)
