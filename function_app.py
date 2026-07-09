import os
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
import azure.functions as func
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from copilot import CopilotClient, PermissionHandler

app = func.FunctionApp()
client = CopilotClient()

DEFAULT_REPOSITORY = "Azure/azure-functions-host"
PACIFIC_TIME = ZoneInfo("America/Los_Angeles")
GITHUB_API = "https://api.github.com"

instructions = """
    You create concise daily GitHub repository digests from live repository data.
    Focus on what changed, what needs attention, and useful next actions.
    Use clear sample language and do not invent activity that is not in the data.
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
    mcp_server_url = os.environ.get("COPILOT_MCP_SERVER_URL")
    if mcp_server_url:
        headers = {}
        mcp_extension_key = os.environ.get("MCP_EXTENSION_KEY")
        if mcp_extension_key:
            headers["x-functions-key"] = mcp_extension_key
        config["mcp_servers"] = {
            "repo-digest-functions": {
                "type": "http",
                "url": mcp_server_url,
                "headers": headers,
                "tools": ["get_repo_digest_context"],
            }
        }
    return config


def _repository_from_prompt(prompt: str) -> str:
    match = re.search(r"\b([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\b", prompt)
    return match.group(1) if match else os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPOSITORY)


def _github_get(path: str, query: dict | None = None) -> dict | list:
    url = f"{GITHUB_API}{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "simple-agent-functions-python",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API returned {exc.code} for {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub API request failed for {url}: {exc.reason}") from exc


def _brief_user(item: dict) -> str:
    user = item.get("user") or {}
    return user.get("login", "unknown")


def _repo_digest_context(repository: str) -> dict:
    owner, repo = repository.split("/", 1)
    since = datetime.now(timezone.utc) - timedelta(days=1)
    since_text = since.isoformat(timespec="seconds").replace("+00:00", "Z")

    repo_info = _github_get(f"/repos/{owner}/{repo}")
    pulls = _github_get(
        f"/repos/{owner}/{repo}/pulls",
        {"state": "open", "sort": "updated", "direction": "desc", "per_page": 20},
    )
    issues = _github_get(
        f"/repos/{owner}/{repo}/issues",
        {"state": "open", "sort": "updated", "direction": "desc", "since": since_text, "per_page": 20},
    )
    runs = _github_get(
        f"/repos/{owner}/{repo}/actions/runs",
        {"status": "completed", "per_page": 20},
    )

    recent_pulls = [
        {
            "number": item["number"],
            "title": item["title"],
            "author": _brief_user(item),
            "updated_at": item["updated_at"],
            "url": item["html_url"],
        }
        for item in pulls
        if item.get("updated_at", "") >= since_text
    ][:10]

    recent_issues = [
        {
            "number": item["number"],
            "title": item["title"],
            "author": _brief_user(item),
            "updated_at": item["updated_at"],
            "url": item["html_url"],
        }
        for item in issues
        if "pull_request" not in item
    ][:10]

    failed_runs = [
        {
            "name": item.get("name"),
            "conclusion": item.get("conclusion"),
            "branch": item.get("head_branch"),
            "created_at": item.get("created_at"),
            "url": item.get("html_url"),
        }
        for item in runs.get("workflow_runs", [])
        if item.get("created_at", "") >= since_text
        and item.get("conclusion") in {"failure", "timed_out", "cancelled", "action_required"}
    ][:10]

    return {
        "repository": repository,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "lookback": "24 hours",
        "stars": repo_info.get("stargazers_count"),
        "forks": repo_info.get("forks_count"),
        "open_issues": repo_info.get("open_issues_count"),
        "recent_open_pull_requests": recent_pulls,
        "recent_open_issues": recent_issues,
        "recent_workflow_failures": failed_runs,
    }


async def _run_digest(prompt: str) -> str:
    repository = _repository_from_prompt(prompt)
    config = _session_config()
    if "mcp_servers" in config:
        digest_prompt = f"""
Create a concise daily repo digest for {repository}.

Use the `get_repo_digest_context` MCP tool to get live GitHub data before writing the digest.

User request:
{prompt}

Return:
1. A one-line summary.
2. Pull requests updated in the last 24 hours.
3. Issues updated in the last 24 hours.
4. Workflow failures from the last 24 hours.
5. Suggested next actions.

If a section has no items, say "None found".
"""
    else:
        context = _repo_digest_context(repository)
        digest_prompt = f"""
Create a concise daily repo digest for {repository}.

User request:
{prompt}

Live GitHub data:
{json.dumps(context, indent=2)}

Return:
1. A one-line summary.
2. Pull requests updated in the last 24 hours.
3. Issues updated in the last 24 hours.
4. Workflow failures from the last 24 hours.
5. Suggested next actions.

If a section has no items, say "None found".
"""
    session = await client.create_session(**config)
    try:
        reply = await session.send_and_wait({"prompt": digest_prompt})
        return (reply.data.content if reply and reply.data else None) or "No response"
    finally:
        await session.destroy()


@app.mcp_tool()
@app.mcp_tool_property(
    arg_name="repository",
    description="Public GitHub repository in owner/name format. Defaults to Azure/azure-functions-host.",
    is_required=False,
)
def get_repo_digest_context(repository: str = DEFAULT_REPOSITORY) -> str:
    """Return live GitHub data for a daily repository digest."""
    repository = repository or os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPOSITORY)
    return json.dumps(_repo_digest_context(repository), indent=2)


@app.route(route="ask", methods=["POST"])
async def ask(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP trigger that sends a message to the Copilot SDK agent."""
    prompt = req.get_body().decode("utf-8") or f"Create a concise daily repo digest for {DEFAULT_REPOSITORY}."
    try:
        response_text = await _run_digest(prompt)
    except RuntimeError as exc:
        logging.exception("Could not create repo digest.")
        return func.HttpResponse(str(exc), status_code=502, mimetype="text/plain")

    return func.HttpResponse(response_text, mimetype="text/plain")


@app.timer_trigger(
    schedule="0 0 16,17 * * *",
    arg_name="daily_digest_timer",
    run_on_startup=False,
    use_monitor=True,
)
async def daily_repo_digest(daily_digest_timer: func.TimerRequest) -> None:
    """Runs the digest once per day at 9 AM Pacific."""
    now_pacific = datetime.now(PACIFIC_TIME)
    if now_pacific.hour != 9:
        logging.info("Skipping daily repo digest because it is %s Pacific.", now_pacific.strftime("%H:%M"))
        return

    if daily_digest_timer.past_due:
        logging.info("Daily repo digest timer is past due.")

    prompt = f"Create a concise daily repo digest for {os.environ.get('GITHUB_REPOSITORY', DEFAULT_REPOSITORY)}."
    digest = await _run_digest(prompt)
    logging.info("Daily repo digest:\n%s", digest)
