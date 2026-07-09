"""Foundry hosted-agent entry point for the repo digest sample."""
from datetime import UTC, datetime, timedelta
import json
import os
from typing import Annotated
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

INSTRUCTIONS = """
You create concise GitHub repository digests.

- If the user asks for a repo digest and does not provide a repo, use Azure/azure-functions-host.
- Call get_repo_digest when the user asks about recent repo activity, open PRs, new issues, closed issues, or failing workflow runs.
- Summarize merged PRs, open PRs needing attention, new issues, closed issues, and failing workflow runs from the requested window.
- Default to the last 24 hours unless the user asks for a different window.
- Keep responses short and action-oriented.
"""
DEFAULT_MODEL_DEPLOYMENT = "gpt-5-mini"
DEFAULT_DIGEST_REPO = os.environ.get("GITHUB_REPOSITORY") or "Azure/azure-functions-host"
GITHUB_API = "https://api.github.com"


def _project_endpoint() -> str:
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT") or os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
    if not endpoint:
        raise RuntimeError("Set FOUNDRY_PROJECT_ENDPOINT to your Microsoft Foundry project endpoint.")
    return endpoint


def _github_get(path: str) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "simple-agent-foundry-hosted-python",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(
        f"{GITHUB_API}{path}",
        headers=headers,
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed with {exc.code}: {detail}") from exc


@tool
def get_repo_digest(
    repo: Annotated[
        str,
        "GitHub repository in owner/name format. Defaults to Azure/azure-functions-host.",
    ] = DEFAULT_DIGEST_REPO,
    hours: Annotated[int, "Number of hours of repo activity to include."] = 24,
) -> str:
    """Return recent public GitHub activity for a repository digest."""
    since = datetime.now(UTC) - timedelta(hours=hours)
    since_iso = since.isoformat(timespec="seconds").replace("+00:00", "Z")
    encoded_repo = quote(repo.strip() or DEFAULT_DIGEST_REPO, safe="/")

    pulls = _github_get(f"/repos/{encoded_repo}/pulls?state=all&sort=updated&direction=desc&per_page=30")
    issues = _github_get(f"/repos/{encoded_repo}/issues?state=all&since={quote(since_iso)}&per_page=30")
    runs = _github_get(f"/repos/{encoded_repo}/actions/runs?created=>={quote(since_iso)}&per_page=20")

    merged_prs = [
        f"#{pr['number']} {pr['title']} by {pr['user']['login']}"
        for pr in pulls
        if pr.get("merged_at") and pr["merged_at"] >= since_iso
    ][:10]
    open_prs = [
        f"#{pr['number']} {pr['title']} by {pr['user']['login']} (updated {pr['updated_at']})"
        for pr in pulls
        if pr.get("state") == "open"
    ][:10]
    new_issues = [
        f"#{issue['number']} {issue['title']} by {issue['user']['login']}"
        for issue in issues
        if "pull_request" not in issue and issue["state"] == "open" and issue["created_at"] >= since_iso
    ][:10]
    closed_issues = [
        f"#{issue['number']} {issue['title']}"
        for issue in issues
        if "pull_request" not in issue and issue["state"] == "closed" and (issue.get("closed_at") or "") >= since_iso
    ][:10]
    failing_runs = [
        f"{run['name']} on {run['head_branch']} ({run['conclusion'] or run['status']})"
        for run in runs.get("workflow_runs", [])
        if run.get("conclusion") in {"failure", "timed_out", "cancelled", "action_required"}
    ][:10]

    return json.dumps(
        {
            "repo": repo.strip() or DEFAULT_DIGEST_REPO,
            "window": f"last {hours} hours",
            "merged_prs": merged_prs,
            "open_prs_needing_attention": open_prs,
            "new_issues": new_issues,
            "closed_issues": closed_issues,
            "failing_workflow_runs": failing_runs,
        },
        indent=2,
    )


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
        tools=[get_repo_digest],
        default_options={"store": False},
    )

    server = ResponsesHostServer(agent)
    server.run()


if __name__ == "__main__":
    main()
