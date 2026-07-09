# Simple Agent QuickStart (Python Foundry Hosted Agent)

A simple AI agent built with Microsoft Agent Framework and hosted by Microsoft Foundry Hosted Agents. This branch pivots the original Azure Functions host to Foundry Agent Service while keeping the same sample idea: Asimov's Three Laws of Robotics summarized as a TLDR in exactly five words.

> Looking for equivalent Functions samples? See [Python](https://github.com/Azure-Samples/simple-agent-functions-python), [C#](https://github.com/Azure-Samples/simple-agent-functions-dotnet), or [TypeScript](https://github.com/Azure-Samples/simple-agent-functions-typescript).

## Prerequisites

- [Python 3.13+](https://www.python.org/downloads/) via [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
- [Azure Developer CLI 1.27.0+](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd)
- The `microsoft.foundry` azd extension:

  ```bash
  azd ext install microsoft.foundry
  ```

  If `azd ext list` shows the Foundry extensions as incompatible, update azd:

  ```bash
  brew uninstall azd && brew install --cask azure/azd/azd
  ```

- An Azure subscription with access to Microsoft Foundry Hosted Agents. Foundry model usage is billed per token, so set spending alerts before deploying real workloads.

## Quickstart

1. Authenticate:

   ```bash
   az login
   azd auth login
   ```

2. Install dependencies:

   ```bash
   uv sync
   ```

3. Configure a Foundry project and model. If you do not already have a project, `azd provision` can create the project, model deployment, Application Insights, and container registry from `azure.yaml`.

   ```bash
   azd provision
   ```

4. Run the hosted agent locally:

   ```bash
   azd ai agent run
   ```

5. Test the local agent in a new terminal:

   ```bash
   azd ai agent invoke --local "what are the laws"
   ```

   Or use curl directly:

   ```bash
   curl -sS -X POST http://localhost:8088/responses \
     -H "Content-Type: application/json" \
     -d '{"input": "what are the laws", "stream": false}'
   ```

   You can also use the interactive chat client:

   ```bash
   uv run chat.py
   ```

6. Deploy to Foundry Agent Service:

   ```bash
   azd deploy
   ```

7. Invoke the deployed hosted agent:

   ```bash
   azd ai agent invoke "what are the laws"
   ```

## Source Code

The agent logic is in [`main.py`](main.py). It creates a `FoundryChatClient`, configures an Agent Framework `Agent` with the sample instructions, and exposes it through `ResponsesHostServer` using the OpenAI-compatible Responses protocol. [`agent.yaml`](agent.yaml) describes the hosted agent runtime and protocol for the Foundry agent tooling.

[`chat.py`](chat.py) is a lightweight console client that POSTs messages to `/responses`. It defaults to `http://localhost:8088` for local runs. Set `AGENT_URL` to point it at another compatible endpoint.

## Configuration

For local runs without `azd ai agent run`, copy `.env.example` to `.env` and set:

```bash
FOUNDRY_PROJECT_ENDPOINT="https://<your-ai-services>.services.ai.azure.com/api/projects/<your-project-name>"
AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-5-mini"
```

Hosted Agents inject `FOUNDRY_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT_NAME`, and Application Insights telemetry settings into the deployed container.

## Learn More

- [Foundry Hosted Agents with Agent Framework](https://learn.microsoft.com/en-us/agent-framework/hosting/foundry-hosted-agent?pivots=programming-language-python)
- [Quickstart: Deploy your first hosted agent](https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/quickstart-hosted-agent?pivots=azd)
- [Foundry hosted Agent Framework Python samples](https://github.com/microsoft-foundry/foundry-samples/tree/main/samples/python/hosted-agents/agent-framework)
