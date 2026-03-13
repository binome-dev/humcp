"""Linear project management tools using the Linear GraphQL API.

Requires a LINEAR_API_KEY environment variable (personal API key or OAuth2 token).

API Reference: https://linear.app/developers/graphql
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.project_management.schemas import (
    LinearIssueData,
    LinearIssueListData,
    LinearIssueListResponse,
    LinearIssueResponse,
    LinearTeamData,
    LinearTeamListData,
    LinearTeamListResponse,
)

logger = logging.getLogger("humcp.tools.linear")

LINEAR_GRAPHQL_ENDPOINT = "https://api.linear.app/graphql"


async def _execute_graphql(
    api_key: str,
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a GraphQL query against the Linear API.

    Args:
        api_key: Linear API key.
        query: GraphQL query string.
        variables: Optional query variables.

    Returns:
        The 'data' portion of the GraphQL response.

    Raises:
        Exception: If the request fails or contains GraphQL errors.
    """
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            LINEAR_GRAPHQL_ENDPOINT, json=payload, headers=headers
        )
        response.raise_for_status()

        result = response.json()
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        return result.get("data", {})


def _parse_issue(issue: dict) -> LinearIssueData:
    """Parse a Linear issue node into a LinearIssueData model.

    Args:
        issue: Raw issue dict from the Linear GraphQL API.

    Returns:
        Parsed LinearIssueData.
    """
    labels = []
    label_nodes = (
        issue.get("labels", {}).get("nodes", []) if issue.get("labels") else []
    )
    for label in label_nodes:
        if label.get("name"):
            labels.append(label["name"])

    return LinearIssueData(
        id=issue["id"],
        identifier=issue.get("identifier"),
        title=issue["title"],
        description=issue.get("description"),
        status=issue.get("state", {}).get("name") if issue.get("state") else None,
        assignee=issue.get("assignee", {}).get("name")
        if issue.get("assignee")
        else None,
        url=issue.get("url"),
        priority=issue.get("priority"),
        labels=labels,
    )


# Common GraphQL fragment for issue fields
_ISSUE_FIELDS = """
    id
    identifier
    title
    description
    url
    priority
    state { name }
    assignee { name }
    labels { nodes { name } }
"""


@tool()
async def linear_create_issue(
    title: str,
    description: str,
    team_id: str,
    project_id: str | None = None,
    assignee_id: str | None = None,
    priority: int | None = None,
    label_ids: list[str] | None = None,
) -> LinearIssueResponse:
    """Create a new issue in Linear.

    Args:
        title: The title of the new issue.
        description: The description of the new issue (Markdown supported).
        team_id: The ID of the team to create the issue in.
        project_id: Optional project ID to associate with the issue.
        assignee_id: Optional assignee user ID.
        priority: Optional priority (0=None, 1=Urgent, 2=High, 3=Medium, 4=Low).
        label_ids: Optional list of label IDs to apply.

    Returns:
        Details of the newly created Linear issue.
    """
    try:
        api_key = await resolve_credential("LINEAR_API_KEY")
        if not api_key:
            return LinearIssueResponse(
                success=False,
                error="Linear API key not configured. Set LINEAR_API_KEY environment variable.",
            )

        query = f"""
        mutation IssueCreate($input: IssueCreateInput!) {{
            issueCreate(input: $input) {{
                success
                issue {{
                    {_ISSUE_FIELDS}
                }}
            }}
        }}
        """

        input_vars: dict[str, Any] = {
            "title": title,
            "description": description,
            "teamId": team_id,
        }
        if project_id is not None:
            input_vars["projectId"] = project_id
        if assignee_id is not None:
            input_vars["assigneeId"] = assignee_id
        if priority is not None:
            input_vars["priority"] = priority
        if label_ids:
            input_vars["labelIds"] = label_ids

        response = await _execute_graphql(api_key, query, {"input": input_vars})

        if not response.get("issueCreate", {}).get("success"):
            return LinearIssueResponse(
                success=False, error="Linear issue creation failed."
            )

        issue = response["issueCreate"]["issue"]
        logger.info("Created Linear issue %s: %s", issue["id"], issue["title"])

        data = _parse_issue(issue)

        return LinearIssueResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to create Linear issue")
        return LinearIssueResponse(success=False, error=f"Failed to create issue: {e}")


@tool()
async def linear_get_issue(issue_id: str) -> LinearIssueResponse:
    """Retrieve details of a specific Linear issue by its ID.

    Args:
        issue_id: The unique identifier of the Linear issue.

    Returns:
        Issue details including title, description, status, priority, assignee, and labels.
    """
    try:
        api_key = await resolve_credential("LINEAR_API_KEY")
        if not api_key:
            return LinearIssueResponse(
                success=False,
                error="Linear API key not configured. Set LINEAR_API_KEY environment variable.",
            )

        query = f"""
        query IssueDetails($issueId: String!) {{
            issue(id: $issueId) {{
                {_ISSUE_FIELDS}
            }}
        }}
        """

        response = await _execute_graphql(api_key, query, {"issueId": issue_id})

        issue = response.get("issue")
        if not issue:
            return LinearIssueResponse(
                success=False,
                error=f"Issue with ID {issue_id} not found.",
            )

        data = _parse_issue(issue)

        return LinearIssueResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to get Linear issue %s", issue_id)
        return LinearIssueResponse(success=False, error=f"Failed to get issue: {e}")


@tool()
async def linear_update_issue(
    issue_id: str,
    title: str | None = None,
    description: str | None = None,
    state_id: str | None = None,
    assignee_id: str | None = None,
    priority: int | None = None,
    label_ids: list[str] | None = None,
) -> LinearIssueResponse:
    """Update an existing Linear issue.

    Args:
        issue_id: The ID of the issue to update.
        title: New issue title.
        description: New issue description (Markdown supported).
        state_id: New workflow state ID (use linear_list_issues to see available states).
        assignee_id: New assignee user ID. Pass empty string to unassign.
        priority: New priority (0=None, 1=Urgent, 2=High, 3=Medium, 4=Low).
        label_ids: New list of label IDs (replaces existing labels).

    Returns:
        Updated issue details.
    """
    try:
        api_key = await resolve_credential("LINEAR_API_KEY")
        if not api_key:
            return LinearIssueResponse(
                success=False,
                error="Linear API key not configured. Set LINEAR_API_KEY environment variable.",
            )

        input_vars: dict[str, Any] = {}
        if title is not None:
            input_vars["title"] = title
        if description is not None:
            input_vars["description"] = description
        if state_id is not None:
            input_vars["stateId"] = state_id
        if assignee_id is not None:
            input_vars["assigneeId"] = assignee_id if assignee_id else None
        if priority is not None:
            input_vars["priority"] = priority
        if label_ids is not None:
            input_vars["labelIds"] = label_ids

        if not input_vars:
            return LinearIssueResponse(
                success=False, error="At least one field must be provided to update."
            )

        query = f"""
        mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {{
            issueUpdate(id: $id, input: $input) {{
                success
                issue {{
                    {_ISSUE_FIELDS}
                }}
            }}
        }}
        """

        response = await _execute_graphql(
            api_key, query, {"id": issue_id, "input": input_vars}
        )

        if not response.get("issueUpdate", {}).get("success"):
            return LinearIssueResponse(
                success=False, error="Linear issue update failed."
            )

        issue = response["issueUpdate"]["issue"]
        logger.info("Updated Linear issue %s", issue_id)

        data = _parse_issue(issue)

        return LinearIssueResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to update Linear issue %s", issue_id)
        return LinearIssueResponse(success=False, error=f"Failed to update issue: {e}")


@tool()
async def linear_list_issues(
    team_id: str | None = None,
    project_id: str | None = None,
    limit: int = 25,
) -> LinearIssueListResponse:
    """List issues, optionally filtered by team or project.

    Args:
        team_id: Optional team ID to filter issues by.
        project_id: Optional project ID to filter issues by.
        limit: Maximum number of issues to return (max 50).

    Returns:
        List of issues matching the filters.
    """
    try:
        api_key = await resolve_credential("LINEAR_API_KEY")
        if not api_key:
            return LinearIssueListResponse(
                success=False,
                error="Linear API key not configured. Set LINEAR_API_KEY environment variable.",
            )

        if limit < 1:
            return LinearIssueListResponse(
                success=False, error="limit must be at least 1"
            )

        # Build filter
        filter_parts = []
        if team_id:
            filter_parts.append(f'team: {{ id: {{ eq: "{team_id}" }} }}')
        if project_id:
            filter_parts.append(f'project: {{ id: {{ eq: "{project_id}" }} }}')

        filter_str = ", ".join(filter_parts)
        filter_arg = f", filter: {{ {filter_str} }}" if filter_str else ""

        query = f"""
        query ListIssues($first: Int) {{
            issues(first: $first{filter_arg}) {{
                nodes {{
                    {_ISSUE_FIELDS}
                }}
            }}
        }}
        """

        response = await _execute_graphql(api_key, query, {"first": min(limit, 50)})

        nodes = response.get("issues", {}).get("nodes", [])
        issues = [_parse_issue(node) for node in nodes]

        logger.info("Listed %d Linear issues", len(issues))

        return LinearIssueListResponse(
            success=True,
            data=LinearIssueListData(issues=issues, total=len(issues)),
        )
    except Exception as e:
        logger.exception("Failed to list Linear issues")
        return LinearIssueListResponse(
            success=False, error=f"Failed to list issues: {e}"
        )


@tool()
async def linear_search_issues(
    query_text: str,
    limit: int = 25,
) -> LinearIssueListResponse:
    """Search for Linear issues by text query.

    Args:
        query_text: The search query string to match against issue titles and descriptions.
        limit: Maximum number of results to return (max 50).

    Returns:
        List of issues matching the search query.
    """
    try:
        api_key = await resolve_credential("LINEAR_API_KEY")
        if not api_key:
            return LinearIssueListResponse(
                success=False,
                error="Linear API key not configured. Set LINEAR_API_KEY environment variable.",
            )

        if limit < 1:
            return LinearIssueListResponse(
                success=False, error="limit must be at least 1"
            )

        query = f"""
        query SearchIssues($term: String!, $first: Int) {{
            searchIssues(term: $term, first: $first) {{
                nodes {{
                    {_ISSUE_FIELDS}
                }}
            }}
        }}
        """

        response = await _execute_graphql(
            api_key, query, {"term": query_text, "first": min(limit, 50)}
        )

        nodes = response.get("searchIssues", {}).get("nodes", [])
        issues = [_parse_issue(node) for node in nodes]

        logger.info(
            "Linear search returned %d results for: %s", len(issues), query_text
        )

        return LinearIssueListResponse(
            success=True,
            data=LinearIssueListData(issues=issues, total=len(issues)),
        )
    except Exception as e:
        logger.exception("Failed to search Linear issues for: %s", query_text)
        return LinearIssueListResponse(
            success=False, error=f"Failed to search issues: {e}"
        )


@tool()
async def linear_list_teams() -> LinearTeamListResponse:
    """List all teams in the Linear workspace.

    Returns:
        List of teams with their IDs, names, and key prefixes.
    """
    try:
        api_key = await resolve_credential("LINEAR_API_KEY")
        if not api_key:
            return LinearTeamListResponse(
                success=False,
                error="Linear API key not configured. Set LINEAR_API_KEY environment variable.",
            )

        query = """
        query Teams {
            teams {
                nodes {
                    id
                    name
                    key
                    description
                }
            }
        }
        """

        response = await _execute_graphql(api_key, query)

        nodes = response.get("teams", {}).get("nodes", [])
        teams = [
            LinearTeamData(
                id=team["id"],
                name=team["name"],
                key=team["key"],
                description=team.get("description"),
            )
            for team in nodes
        ]

        logger.info("Listed %d Linear teams", len(teams))

        return LinearTeamListResponse(
            success=True,
            data=LinearTeamListData(teams=teams, total=len(teams)),
        )
    except Exception as e:
        logger.exception("Failed to list Linear teams")
        return LinearTeamListResponse(success=False, error=f"Failed to list teams: {e}")
