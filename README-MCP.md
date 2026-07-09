# MCP extension notes

This sample exposes the live repo data fetcher as an Azure Functions MCP extension tool and can consume that same Functions-hosted MCP service from the Copilot SDK.

The full Azure Functions tutorial belongs in Microsoft Learn. Start with [Tutorial: Host an MCP server on Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-mcp-tutorial), then use these sample-specific notes to see how the pieces map into this repo.

## Expose a Functions MCP tool

The repo digest data fetcher is exposed from [`function_app.py`](function_app.py) with the Python v2 Functions programming model:

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

Remote endpoints require the `mcp_extension` system key unless `host.json` is configured for anonymous webhook authorization. Get the deployed key with:

```bash
az functionapp keys list \
  --resource-group <resource-group> \
  --name <function-app-name> \
  --query systemKeys.mcp_extension \
  --output tsv
```

## Consume the Functions MCP service from Copilot SDK

Pass the Functions MCP endpoint as a remote HTTP MCP server when creating a Copilot SDK session:

```python
session = await client.create_session(
    on_permission_request=PermissionHandler.approve_all,
    mcp_servers={
        "repo-digest-functions": {
            "type": "http",
            "url": "https://<app-name>.azurewebsites.net/runtime/webhooks/mcp",
            "headers": {"x-functions-key": "<mcp_extension system key>"},
            "tools": ["get_repo_digest_context"],
        }
    },
)
```

For local loopback in this sample, set:

```bash
export COPILOT_MCP_SERVER_URL="http://localhost:7071/runtime/webhooks/mcp"
```

For a deployed Function App endpoint, also set:

```bash
export MCP_EXTENSION_KEY="<mcp_extension system key>"
```

When `COPILOT_MCP_SERVER_URL` is set, `function_app.py` passes the MCP server into `CopilotClient.create_session` and asks the model to call `get_repo_digest_context` for live GitHub data. If `COPILOT_MCP_SERVER_URL` is not set, the sample falls back to fetching public GitHub REST data directly before sending the prompt to the model.

## References

- [Tutorial: Host an MCP server on Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-mcp-tutorial)
- [Model context protocol bindings for Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-mcp)
- [MCP tool trigger for Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-mcp-tool-trigger)
- [Using MCP servers with the GitHub Copilot SDK](https://github.com/github/copilot-sdk/blob/main/docs/features/mcp.md)
