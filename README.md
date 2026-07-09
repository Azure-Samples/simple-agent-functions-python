# Daily Repo Digest

This sample is a Foundry Hosted Agent built with Microsoft Agent Framework. It creates a daily GitHub repo digest for `Azure/azure-functions-host` by default.

The agent:

- Runs every day at 9 AM Pacific.
- Gathers useful GitHub repo info for [`Azure/azure-functions-host`](#configuration), including recent PRs, issues, and workflow failures.
- Answers interactive Ask/chat requests any time through the hosted agent Responses API.
- Uses a Foundry model deployment directly through Microsoft Agent Framework.

> Looking for equivalent Functions samples? See [Python](https://github.com/Azure-Samples/simple-agent-functions-python), [C#](https://github.com/Azure-Samples/simple-agent-functions-dotnet), or [TypeScript](https://github.com/Azure-Samples/simple-agent-functions-typescript).

## Prerequisites

- Python 3.13+ via [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Azure Developer CLI 1.27.0+](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd)
- The `microsoft.foundry` azd extension:

  ```bash
  azd ext install microsoft.foundry
  ```

- An Azure subscription with access to Microsoft Foundry Hosted Agents

## Run the agent locally

Install dependencies:

```bash
uv sync
```

Create or update the Foundry project, model deployment, Application Insights, and container registry from `azure.yaml`:

```bash
azd provision
```

By default, the digest runs against `Azure/azure-functions-host`.

Start the hosted agent locally:

```bash
azd ai agent run
```

Ask for a digest in another terminal:

```bash
azd ai agent invoke --local "Create a concise daily repo digest for Azure/azure-functions-host."
```

Or use the Responses API directly:

```bash
curl -sS -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "Create a concise daily repo digest for Azure/azure-functions-host.", "stream": false}'
```

You can also use the console chat client:

```bash
uv run chat.py
```

## Run the agent in cloud

Deploy the hosted agent and daily routine:

```bash
azd deploy
```

Invoke the deployed agent:

```bash
azd ai agent invoke "Create a concise daily repo digest for Azure/azure-functions-host."
```

Dispatch the daily routine on demand:

```bash
azd ai routine dispatch daily-repo-digest
```

## Configuration

`azure.yaml` configures the hosted agent with these defaults:

- Default repo: `Azure/azure-functions-host`
- Schedule: 9 AM Pacific
- Model deployment: `gpt-5-mini`

To digest a different repo, set it before `azd provision`:

```bash
azd env set GITHUB_REPOSITORY "owner/repo"
```

For local and cloud hosted-agent runs, that value becomes the `GITHUB_REPOSITORY` environment variable. Set `GITHUB_TOKEN` the same way if you want higher GitHub API rate limits.

## Files

- `main.py`: gathers GitHub data, defines the digest tool, creates the Agent Framework agent, and starts the hosted Responses server.
- `agent.yaml`: describes the hosted agent runtime and protocol.
- `azure.yaml`: declares the Foundry project, hosted agent, and daily routine.
- `chat.py`: local console client for interactive questions.

## Learn more

- [Foundry Hosted Agents with Agent Framework](https://learn.microsoft.com/en-us/agent-framework/hosting/foundry-hosted-agent?pivots=programming-language-python)
- [Quickstart: Deploy your first hosted agent](https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/quickstart-hosted-agent?pivots=azd)
- [Foundry hosted Agent Framework Python samples](https://github.com/microsoft-foundry/foundry-samples/tree/main/samples/python/hosted-agents/agent-framework)
