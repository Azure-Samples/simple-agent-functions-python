# Repo Digest Agent QuickStart (Python Foundry Hosted Agent)

A simple AI agent built with Microsoft Agent Framework and hosted by Microsoft Foundry Hosted Agents. It creates live GitHub repository digests for recent pull requests, issues, and workflow failures, and includes a Foundry Routine that runs the digest every day at 9 AM Pacific time. The default repository is `microsoft-foundry/foundry-samples`.

> Looking for equivalent Functions samples? See [Python](https://github.com/Azure-Samples/simple-agent-functions-python), [C#](https://github.com/Azure-Samples/simple-agent-functions-dotnet), or [TypeScript](https://github.com/Azure-Samples/simple-agent-functions-typescript).

## Prerequisites

- Python 3.13+ via [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Azure Developer CLI 1.27.0+](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd)
- The `microsoft.foundry` azd extension:

  ```bash
  azd ext install microsoft.foundry
  ```

- An Azure subscription with access to Microsoft Foundry Hosted Agents. Foundry model usage is billed per token, so set spending alerts before deploying real workloads.

## Quickstart

1. Authenticate:

   ```bash
   azd auth login
   ```

2. Install dependencies:

   ```bash
   uv sync
   ```

3. Create or update the Foundry project, model deployment, Application Insights, and container registry from `azure.yaml`:

   ```bash
   azd provision
   ```

4. Run the hosted agent locally:

   ```bash
   azd ai agent run
   ```

5. Test the local agent in a new terminal:

   ```bash
   azd ai agent invoke --local "Create a concise daily repo digest."
   ```

   Or use curl directly:

   ```bash
   curl -sS -X POST http://localhost:8088/responses \
     -H "Content-Type: application/json" \
     -d '{"input": "Create a concise daily repo digest.", "stream": false}'
   ```

   You can also use the interactive chat client:

   ```bash
   uv run chat.py
   ```

6. Deploy the hosted agent and daily routine:

   ```bash
   azd deploy
   ```

7. Invoke the deployed agent:

   ```bash
   azd ai agent invoke "Create a concise daily repo digest."
   ```

8. Verify the scheduled routine and run it once:

   ```bash
   azd ai routine show daily-repo-digest
   azd ai routine dispatch daily-repo-digest
   ```

## Source Code

The agent logic is in [`main.py`](main.py). It creates a `FoundryChatClient`, configures an Agent Framework `Agent`, and exposes it through `ResponsesHostServer` using the OpenAI-compatible Responses protocol. [`agent.yaml`](agent.yaml) describes the hosted agent runtime and protocol for the Foundry agent tooling.

Ask for a digest with an optional repo such as `microsoft-foundry/foundry-samples`; if you omit the repo, the agent uses `microsoft-foundry/foundry-samples` by default. The sample uses public GitHub APIs for a no-secret quickstart.

[`chat.py`](chat.py) is a lightweight console client that POSTs messages to `/responses`. It defaults to `http://localhost:8088` for local runs. Use it to ask live follow-up questions about the default repo or another public repo. Set `AGENT_URL` to point it at another compatible endpoint.

[`azure.yaml`](azure.yaml) also declares `daily-repo-digest`, a Foundry Routine that invokes the hosted agent daily at 9:00 AM in the `America/Los_Angeles` time zone.

## Daily Routine

The timer is declared in [`azure.yaml`](azure.yaml) as a Foundry Routine named `daily-repo-digest`. It uses a recurring schedule trigger with cron expression `0 9 * * *` and `time_zone: America/Los_Angeles`, then invokes the hosted agent with `Create a concise daily repo digest for microsoft-foundry/foundry-samples.`

## Configuration

For local runs without `azd ai agent run`, copy `.env.example` to `.env` and set:

```bash
FOUNDRY_PROJECT_ENDPOINT="https://<your-ai-services>.services.ai.azure.com/api/projects/<your-project-name>"
AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-5-mini"
```

Hosted Agents inject `FOUNDRY_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT_NAME`, and Application Insights telemetry settings into the deployed container.

## Next steps

- Add tools and data sources via MCP: [Connect an MCP server on Azure Functions to Foundry Agent Service](https://learn.microsoft.com/en-us/azure/azure-functions/functions-mcp-foundry-tools) and [connect MCP server endpoints to Foundry agents](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol).
- Build durable, long-running agents: [Durable Extension for Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/integrations/durable-extension).

## Learn More

- [Foundry Hosted Agents with Agent Framework](https://learn.microsoft.com/en-us/agent-framework/hosting/foundry-hosted-agent?pivots=programming-language-python)
- [Quickstart: Deploy your first hosted agent](https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/quickstart-hosted-agent?pivots=azd)
- [Durable Extension for Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/integrations/durable-extension)
- [Foundry hosted Agent Framework Python samples](https://github.com/microsoft-foundry/foundry-samples/tree/main/samples/python/hosted-agents/agent-framework)
