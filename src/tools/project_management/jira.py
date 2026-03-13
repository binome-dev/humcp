"""Jira project management tools for issue tracking and management.

Uses the Jira REST API via the jira Python library. Requires JIRA_URL,
JIRA_USERNAME, and JIRA_API_TOKEN environment variables.

API Reference: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
"""

from __future__ import annotations

import logging
from typing import cast

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.project_management.schemas import (
    JiraCommentData,
    JiraCommentResponse,
    JiraIssueData,
    JiraIssueListData,
    JiraIssueListResponse,
    JiraIssueResponse,
    JiraProjectData,
    JiraProjectListData,
    JiraProjectListResponse,
    JiraTransitionData,
    JiraTransitionListData,
    JiraTransitionListResponse,
    JiraTransitionResponse,
)

try:
    from jira import JIRA, Issue
except ImportError as err:
    raise ImportError(
        "jira is required for Jira tools. Install with: pip install jira"
    ) from err

logger = logging.getLogger("humcp.tools.jira")


async def _get_jira_client() -> tuple[JIRA | None, str | None, str | None]:
    """Create a Jira client from environment variables.

    Returns:
        A tuple of (client, server_url, error_message).
    """
    server_url = await resolve_credential("JIRA_URL")
    username = await resolve_credential("JIRA_USERNAME")
    api_token = await resolve_credential("JIRA_API_TOKEN")

    if not server_url:
        return None, None, "Jira URL not configured. Set JIRA_URL environment variable."
    if not username:
        return (
            None,
            None,
            "Jira username not configured. Set JIRA_USERNAME environment variable.",
        )
    if not api_token:
        return (
            None,
            None,
            "Jira API token not configured. Set JIRA_API_TOKEN environment variable.",
        )

    client = JIRA(server=server_url, basic_auth=(username, api_token))
    return client, server_url, None


def _issue_to_data(issue: Issue, server_url: str | None) -> JiraIssueData:
    """Convert a Jira Issue object to JiraIssueData.

    Args:
        issue: A Jira Issue object.
        server_url: The Jira server base URL.

    Returns:
        A JiraIssueData Pydantic model.
    """
    priority_name = None
    if hasattr(issue.fields, "priority") and issue.fields.priority:
        priority_name = issue.fields.priority.name

    labels: list[str] = []
    if hasattr(issue.fields, "labels") and issue.fields.labels:
        labels = list(issue.fields.labels)

    return JiraIssueData(
        key=issue.key,
        project=issue.fields.project.key
        if hasattr(issue.fields, "project") and issue.fields.project
        else None,
        issue_type=issue.fields.issuetype.name
        if hasattr(issue.fields, "issuetype") and issue.fields.issuetype
        else None,
        summary=issue.fields.summary,
        description=issue.fields.description or None,
        status=issue.fields.status.name
        if hasattr(issue.fields, "status") and issue.fields.status
        else None,
        priority=priority_name,
        assignee=(
            issue.fields.assignee.displayName
            if hasattr(issue.fields, "assignee") and issue.fields.assignee
            else None
        ),
        reporter=(
            issue.fields.reporter.displayName
            if hasattr(issue.fields, "reporter") and issue.fields.reporter
            else None
        ),
        labels=labels,
        url=f"{server_url}/browse/{issue.key}" if server_url else None,
    )


@tool()
async def jira_get_issue(issue_key: str) -> JiraIssueResponse:
    """Retrieve details of a specific Jira issue by its key (e.g., PROJ-123).

    Args:
        issue_key: The Jira issue key to retrieve (e.g., PROJ-123).

    Returns:
        Issue details including key, summary, description, status, priority, assignee, and labels.
    """
    try:
        client, server_url, error = await _get_jira_client()
        if error or client is None:
            return JiraIssueResponse(success=False, error=error)

        issue = cast(Issue, client.issue(issue_key))
        data = _issue_to_data(issue, server_url)

        return JiraIssueResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to get Jira issue %s", issue_key)
        return JiraIssueResponse(success=False, error=f"Failed to get issue: {e}")


@tool()
async def jira_create_issue(
    project_key: str,
    summary: str,
    description: str = "",
    issue_type: str = "Task",
    priority: str | None = None,
    assignee: str | None = None,
    labels: list[str] | None = None,
) -> JiraIssueResponse:
    """Create a new issue in a Jira project.

    Args:
        project_key: The project key to create the issue in (e.g., PROJ).
        summary: The issue summary/title.
        description: The issue description.
        issue_type: The type of issue (e.g., Task, Bug, Story, Epic).
        priority: Optional priority name (e.g., High, Medium, Low).
        assignee: Optional assignee account ID or username.
        labels: Optional list of label names.

    Returns:
        Details of the newly created issue.
    """
    try:
        client, server_url, error = await _get_jira_client()
        if error or client is None:
            return JiraIssueResponse(success=False, error=error)

        issue_dict: dict = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
        }
        if priority:
            issue_dict["priority"] = {"name": priority}
        if assignee:
            issue_dict["assignee"] = {"name": assignee}
        if labels:
            issue_dict["labels"] = labels

        new_issue = client.create_issue(fields=issue_dict)
        issue = cast(Issue, client.issue(new_issue.key))

        logger.info("Created Jira issue %s in project %s", new_issue.key, project_key)

        data = _issue_to_data(issue, server_url)

        return JiraIssueResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to create Jira issue in project %s", project_key)
        return JiraIssueResponse(success=False, error=f"Failed to create issue: {e}")


@tool()
async def jira_search_issues(
    jql: str,
    max_results: int = 50,
) -> JiraIssueListResponse:
    """Search for Jira issues using JQL (Jira Query Language).

    Args:
        jql: The JQL query string (e.g., "project = PROJ AND status = Open").
        max_results: Maximum number of results to return (max 100).

    Returns:
        List of issues matching the JQL query.
    """
    try:
        client, server_url, error = await _get_jira_client()
        if error or client is None:
            return JiraIssueListResponse(success=False, error=error)

        if max_results < 1:
            return JiraIssueListResponse(
                success=False, error="max_results must be at least 1"
            )

        issues = client.search_issues(jql, maxResults=min(max_results, 100))

        issue_list = [
            _issue_to_data(cast(Issue, issue), server_url) for issue in issues
        ]

        logger.info("Jira search returned %d results for JQL: %s", len(issue_list), jql)

        return JiraIssueListResponse(
            success=True,
            data=JiraIssueListData(issues=issue_list, total=len(issue_list)),
        )
    except Exception as e:
        logger.exception("Failed to search Jira issues with JQL: %s", jql)
        return JiraIssueListResponse(
            success=False, error=f"Failed to search issues: {e}"
        )


@tool()
async def jira_transition_issue(
    issue_key: str,
    transition_name: str,
) -> JiraTransitionResponse:
    """Transition a Jira issue to a new status (e.g., move from "To Do" to "In Progress").

    Args:
        issue_key: The Jira issue key (e.g., PROJ-123).
        transition_name: The name of the transition to perform (e.g., "Start Progress", "Done").

    Returns:
        Details of the transition that was performed.
    """
    try:
        client, _server_url, error = await _get_jira_client()
        if error or client is None:
            return JiraTransitionResponse(success=False, error=error)

        transitions = client.transitions(issue_key)
        target_transition = None
        for t in transitions:
            if t["name"].lower() == transition_name.lower():
                target_transition = t
                break

        if not target_transition:
            available = [t["name"] for t in transitions]
            return JiraTransitionResponse(
                success=False,
                error=f"Transition '{transition_name}' not found. Available transitions: {', '.join(available)}",
            )

        client.transition_issue(issue_key, target_transition["id"])

        logger.info("Transitioned Jira issue %s via '%s'", issue_key, transition_name)

        data = JiraTransitionData(
            id=str(target_transition["id"]),
            name=target_transition["name"],
            to_status=target_transition.get("to", {}).get("name"),
        )

        return JiraTransitionResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to transition Jira issue %s", issue_key)
        return JiraTransitionResponse(
            success=False, error=f"Failed to transition issue: {e}"
        )


@tool()
async def jira_list_transitions(
    issue_key: str,
) -> JiraTransitionListResponse:
    """List all available transitions for a Jira issue.

    Use this to discover what status changes are possible for an issue before
    calling jira_transition_issue. The available transitions depend on the
    issue's current status and the project's workflow configuration.

    Args:
        issue_key: The Jira issue key (e.g., PROJ-123).

    Returns:
        List of available transitions with their IDs, names, and target statuses.
    """
    try:
        client, _server_url, error = await _get_jira_client()
        if error or client is None:
            return JiraTransitionListResponse(success=False, error=error)

        transitions = client.transitions(issue_key)

        transition_list = [
            JiraTransitionData(
                id=str(t["id"]),
                name=t["name"],
                to_status=t.get("to", {}).get("name"),
            )
            for t in transitions
        ]

        logger.info(
            "Listed %d transitions for Jira issue %s",
            len(transition_list),
            issue_key,
        )

        return JiraTransitionListResponse(
            success=True,
            data=JiraTransitionListData(
                issue_key=issue_key,
                transitions=transition_list,
                total=len(transition_list),
            ),
        )
    except Exception as e:
        logger.exception("Failed to list transitions for Jira issue %s", issue_key)
        return JiraTransitionListResponse(
            success=False, error=f"Failed to list transitions: {e}"
        )


@tool()
async def jira_add_comment(
    issue_key: str,
    body: str,
) -> JiraCommentResponse:
    """Add a comment to a Jira issue.

    Args:
        issue_key: The Jira issue key (e.g., PROJ-123).
        body: The comment body text.

    Returns:
        Details of the newly created comment.
    """
    try:
        client, server_url, error = await _get_jira_client()
        if error or client is None:
            return JiraCommentResponse(success=False, error=error)

        comment = client.add_comment(issue_key, body)

        logger.info("Added comment to Jira issue %s", issue_key)

        data = JiraCommentData(
            id=comment.id,
            body=comment.body,
            author=(
                comment.author.displayName
                if hasattr(comment, "author") and comment.author
                else None
            ),
            created=str(comment.created) if hasattr(comment, "created") else None,
            url=f"{server_url}/browse/{issue_key}?focusedCommentId={comment.id}"
            if server_url
            else None,
        )

        return JiraCommentResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to add comment to Jira issue %s", issue_key)
        return JiraCommentResponse(success=False, error=f"Failed to add comment: {e}")


@tool()
async def jira_list_projects() -> JiraProjectListResponse:
    """List all Jira projects accessible to the authenticated user.

    Returns:
        List of Jira projects with their keys, names, and leads.
    """
    try:
        client, server_url, error = await _get_jira_client()
        if error or client is None:
            return JiraProjectListResponse(success=False, error=error)

        projects = client.projects()

        project_list = [
            JiraProjectData(
                key=p.key,
                name=p.name,
                project_type=getattr(p, "projectTypeKey", None),
                lead=getattr(p, "lead", {}).get("displayName")
                if isinstance(getattr(p, "lead", None), dict)
                else (
                    p.lead.displayName
                    if hasattr(p, "lead") and p.lead and hasattr(p.lead, "displayName")
                    else None
                ),
                url=f"{server_url}/browse/{p.key}" if server_url else None,
            )
            for p in projects
        ]

        logger.info("Listed %d Jira projects", len(project_list))

        return JiraProjectListResponse(
            success=True,
            data=JiraProjectListData(projects=project_list, total=len(project_list)),
        )
    except Exception as e:
        logger.exception("Failed to list Jira projects")
        return JiraProjectListResponse(
            success=False, error=f"Failed to list projects: {e}"
        )
