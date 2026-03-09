"""GitHub tools for repository, issue, pull request, commit, and release management.

Uses the GitHub REST API v3. Requires a GITHUB_TOKEN environment variable
with appropriate scopes (repo, read:org).

API Reference: https://docs.github.com/en/rest
"""

from __future__ import annotations

import logging

import httpx

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.project_management.schemas import (
    GitHubCommitData,
    GitHubCommitListData,
    GitHubCommitListResponse,
    GitHubIssueData,
    GitHubIssueListData,
    GitHubIssueListResponse,
    GitHubIssueResponse,
    GitHubPullRequestData,
    GitHubPullRequestListData,
    GitHubPullRequestListResponse,
    GitHubPullRequestResponse,
    GitHubReleaseData,
    GitHubReleaseListData,
    GitHubReleaseListResponse,
    GitHubRepoData,
    GitHubRepoResponse,
)

logger = logging.getLogger("humcp.tools.github")

GITHUB_API_BASE = "https://api.github.com"


async def _get_headers() -> tuple[dict[str, str] | None, str | None]:
    """Build GitHub API headers from environment variables.

    Returns:
        A tuple of (headers_dict, error_message).
    """
    token = await resolve_credential("GITHUB_TOKEN")
    if not token:
        return (
            None,
            "GitHub token not configured. Set GITHUB_TOKEN environment variable.",
        )

    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }, None


@tool()
async def github_get_repo(
    owner: str,
    repo: str,
) -> GitHubRepoResponse:
    """Get details of a GitHub repository.

    Args:
        owner: The repository owner (user or organization).
        repo: The repository name.

    Returns:
        Repository details including name, description, stars, forks, and language.
    """
    try:
        headers, error = await _get_headers()
        if error or headers is None:
            return GitHubRepoResponse(success=False, error=error)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
                headers=headers,
            )
            response.raise_for_status()
            repo_data = response.json()

        data = GitHubRepoData(
            name=repo_data["name"],
            full_name=repo_data["full_name"],
            description=repo_data.get("description"),
            url=repo_data.get("html_url"),
            stars=repo_data.get("stargazers_count"),
            forks=repo_data.get("forks_count"),
            language=repo_data.get("language"),
            is_private=repo_data.get("private", False),
            default_branch=repo_data.get("default_branch"),
            open_issues_count=repo_data.get("open_issues_count"),
        )

        return GitHubRepoResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to get GitHub repo %s/%s", owner, repo)
        return GitHubRepoResponse(success=False, error=f"Failed to get repository: {e}")


@tool()
async def github_list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    labels: str | None = None,
    assignee: str | None = None,
    sort: str = "created",
    direction: str = "desc",
    per_page: int = 30,
) -> GitHubIssueListResponse:
    """List issues in a GitHub repository. Pull requests are excluded.

    Args:
        owner: The repository owner (user or organization).
        repo: The repository name.
        state: Filter by issue state: "open", "closed", or "all".
        labels: Comma-separated list of label names to filter by (e.g., "bug,enhancement").
        assignee: Filter by assignee login. Use "none" for unassigned or "*" for any.
        sort: Sort field: "created", "updated", or "comments".
        direction: Sort direction: "asc" or "desc".
        per_page: Number of issues per page (max 100).

    Returns:
        List of issues in the repository.
    """
    try:
        headers, error = await _get_headers()
        if error or headers is None:
            return GitHubIssueListResponse(success=False, error=error)

        if state not in ("open", "closed", "all"):
            return GitHubIssueListResponse(
                success=False,
                error="state must be one of: open, closed, all",
            )

        if sort not in ("created", "updated", "comments"):
            return GitHubIssueListResponse(
                success=False,
                error="sort must be one of: created, updated, comments",
            )

        if per_page < 1:
            return GitHubIssueListResponse(
                success=False, error="per_page must be at least 1"
            )

        params: dict = {
            "state": state,
            "sort": sort,
            "direction": direction,
            "per_page": min(per_page, 100),
        }
        if labels:
            params["labels"] = labels
        if assignee:
            params["assignee"] = assignee

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            issues_json = response.json()

        # Filter out pull requests (GitHub API returns PRs in issues endpoint)
        issues = [
            GitHubIssueData(
                number=issue["number"],
                title=issue["title"],
                body=issue.get("body"),
                state=issue.get("state"),
                assignee=(
                    issue["assignee"]["login"] if issue.get("assignee") else None
                ),
                url=issue.get("html_url"),
                labels=[label["name"] for label in issue.get("labels", [])],
                created_at=issue.get("created_at"),
                updated_at=issue.get("updated_at"),
            )
            for issue in issues_json
            if "pull_request" not in issue
        ]

        logger.info(
            "Listed %d GitHub issues for %s/%s (state=%s)",
            len(issues),
            owner,
            repo,
            state,
        )

        return GitHubIssueListResponse(
            success=True,
            data=GitHubIssueListData(issues=issues, total=len(issues)),
        )
    except Exception as e:
        logger.exception("Failed to list GitHub issues for %s/%s", owner, repo)
        return GitHubIssueListResponse(
            success=False, error=f"Failed to list issues: {e}"
        )


@tool()
async def github_create_issue(
    owner: str,
    repo: str,
    title: str,
    body: str = "",
    labels: list[str] | None = None,
    assignees: list[str] | None = None,
    milestone: int | None = None,
) -> GitHubIssueResponse:
    """Create a new issue in a GitHub repository.

    Args:
        owner: The repository owner (user or organization).
        repo: The repository name.
        title: The issue title.
        body: The issue body/description (Markdown supported).
        labels: Optional list of label names to apply.
        assignees: Optional list of GitHub usernames to assign.
        milestone: Optional milestone number to associate with.

    Returns:
        Details of the newly created issue.
    """
    try:
        headers, error = await _get_headers()
        if error or headers is None:
            return GitHubIssueResponse(success=False, error=error)

        payload: dict = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        if assignees:
            payload["assignees"] = assignees
        if milestone is not None:
            payload["milestone"] = milestone

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            issue = response.json()

        logger.info("Created GitHub issue #%d in %s/%s", issue["number"], owner, repo)

        data = GitHubIssueData(
            number=issue["number"],
            title=issue["title"],
            body=issue.get("body"),
            state=issue.get("state"),
            assignee=(issue["assignee"]["login"] if issue.get("assignee") else None),
            url=issue.get("html_url"),
            labels=[label["name"] for label in issue.get("labels", [])],
            created_at=issue.get("created_at"),
            updated_at=issue.get("updated_at"),
        )

        return GitHubIssueResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to create GitHub issue in %s/%s", owner, repo)
        return GitHubIssueResponse(success=False, error=f"Failed to create issue: {e}")


@tool()
async def github_list_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    sort: str = "created",
    direction: str = "desc",
    per_page: int = 30,
) -> GitHubPullRequestListResponse:
    """List pull requests in a GitHub repository.

    Args:
        owner: The repository owner (user or organization).
        repo: The repository name.
        state: Filter by PR state: "open", "closed", or "all".
        sort: Sort field: "created", "updated", or "popularity".
        direction: Sort direction: "asc" or "desc".
        per_page: Number of pull requests per page (max 100).

    Returns:
        List of pull requests in the repository.
    """
    try:
        headers, error = await _get_headers()
        if error or headers is None:
            return GitHubPullRequestListResponse(success=False, error=error)

        if state not in ("open", "closed", "all"):
            return GitHubPullRequestListResponse(
                success=False,
                error="state must be one of: open, closed, all",
            )

        if per_page < 1:
            return GitHubPullRequestListResponse(
                success=False, error="per_page must be at least 1"
            )

        params = {
            "state": state,
            "sort": sort,
            "direction": direction,
            "per_page": min(per_page, 100),
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            prs_json = response.json()

        pull_requests = [
            GitHubPullRequestData(
                number=pr["number"],
                title=pr["title"],
                body=pr.get("body"),
                state=pr.get("state"),
                merged=pr.get("merged_at") is not None,
                head_branch=pr.get("head", {}).get("ref"),
                base_branch=pr.get("base", {}).get("ref"),
                user=pr.get("user", {}).get("login") if pr.get("user") else None,
                url=pr.get("html_url"),
                created_at=pr.get("created_at"),
            )
            for pr in prs_json
        ]

        logger.info(
            "Listed %d GitHub PRs for %s/%s (state=%s)",
            len(pull_requests),
            owner,
            repo,
            state,
        )

        return GitHubPullRequestListResponse(
            success=True,
            data=GitHubPullRequestListData(
                pull_requests=pull_requests, total=len(pull_requests)
            ),
        )
    except Exception as e:
        logger.exception("Failed to list GitHub PRs for %s/%s", owner, repo)
        return GitHubPullRequestListResponse(
            success=False, error=f"Failed to list pull requests: {e}"
        )


@tool()
async def github_get_pull_request(
    owner: str,
    repo: str,
    pull_number: int,
) -> GitHubPullRequestResponse:
    """Get details of a specific pull request in a GitHub repository.

    Args:
        owner: The repository owner (user or organization).
        repo: The repository name.
        pull_number: The pull request number.

    Returns:
        Detailed information about the pull request including title, body, state,
        branches, and merge status.
    """
    try:
        headers, error = await _get_headers()
        if error or headers is None:
            return GitHubPullRequestResponse(success=False, error=error)

        if pull_number < 1:
            return GitHubPullRequestResponse(
                success=False, error="pull_number must be at least 1"
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pull_number}",
                headers=headers,
            )
            response.raise_for_status()
            pr = response.json()

        data = GitHubPullRequestData(
            number=pr["number"],
            title=pr["title"],
            body=pr.get("body"),
            state=pr.get("state"),
            merged=pr.get("merged", False),
            head_branch=pr.get("head", {}).get("ref"),
            base_branch=pr.get("base", {}).get("ref"),
            user=pr.get("user", {}).get("login") if pr.get("user") else None,
            url=pr.get("html_url"),
            created_at=pr.get("created_at"),
        )

        logger.info("Retrieved GitHub PR #%d in %s/%s", pull_number, owner, repo)

        return GitHubPullRequestResponse(success=True, data=data)
    except Exception as e:
        logger.exception(
            "Failed to get GitHub PR #%d in %s/%s", pull_number, owner, repo
        )
        return GitHubPullRequestResponse(
            success=False, error=f"Failed to get pull request: {e}"
        )


@tool()
async def github_create_pull_request(
    owner: str,
    repo: str,
    title: str,
    head: str,
    base: str,
    body: str = "",
    draft: bool = False,
) -> GitHubPullRequestResponse:
    """Create a new pull request in a GitHub repository.

    Args:
        owner: The repository owner (user or organization).
        repo: The repository name.
        title: The pull request title.
        head: The branch containing changes (e.g., "feature-branch" or "user:feature-branch" for cross-repo).
        base: The branch to merge into (e.g., "main").
        body: The pull request description (Markdown supported).
        draft: Whether to create the PR as a draft.

    Returns:
        Details of the newly created pull request.
    """
    try:
        headers, error = await _get_headers()
        if error or headers is None:
            return GitHubPullRequestResponse(success=False, error=error)

        payload: dict = {
            "title": title,
            "head": head,
            "base": base,
            "body": body,
            "draft": draft,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            pr = response.json()

        logger.info("Created GitHub PR #%d in %s/%s", pr["number"], owner, repo)

        data = GitHubPullRequestData(
            number=pr["number"],
            title=pr["title"],
            body=pr.get("body"),
            state=pr.get("state"),
            merged=pr.get("merged", False),
            head_branch=pr.get("head", {}).get("ref"),
            base_branch=pr.get("base", {}).get("ref"),
            user=pr.get("user", {}).get("login") if pr.get("user") else None,
            url=pr.get("html_url"),
            created_at=pr.get("created_at"),
        )

        return GitHubPullRequestResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to create GitHub PR in %s/%s", owner, repo)
        return GitHubPullRequestResponse(
            success=False, error=f"Failed to create pull request: {e}"
        )


@tool()
async def github_list_commits(
    owner: str,
    repo: str,
    sha: str | None = None,
    path: str | None = None,
    author: str | None = None,
    per_page: int = 30,
) -> GitHubCommitListResponse:
    """List commits in a GitHub repository.

    Args:
        owner: The repository owner (user or organization).
        repo: The repository name.
        sha: Branch name or commit SHA to list commits from. Defaults to the default branch.
        path: Only commits containing this file path will be returned.
        author: GitHub login or email to filter commits by author.
        per_page: Number of commits per page (max 100).

    Returns:
        List of commits in the repository.
    """
    try:
        headers, error = await _get_headers()
        if error or headers is None:
            return GitHubCommitListResponse(success=False, error=error)

        if per_page < 1:
            return GitHubCommitListResponse(
                success=False, error="per_page must be at least 1"
            )

        params: dict = {"per_page": min(per_page, 100)}
        if sha:
            params["sha"] = sha
        if path:
            params["path"] = path
        if author:
            params["author"] = author

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            commits_json = response.json()

        commits = [
            GitHubCommitData(
                sha=commit["sha"],
                message=commit.get("commit", {}).get("message", ""),
                author=(
                    commit.get("author", {}).get("login")
                    if commit.get("author")
                    else commit.get("commit", {}).get("author", {}).get("name")
                ),
                date=commit.get("commit", {}).get("author", {}).get("date"),
                url=commit.get("html_url"),
            )
            for commit in commits_json
        ]

        logger.info("Listed %d GitHub commits for %s/%s", len(commits), owner, repo)

        return GitHubCommitListResponse(
            success=True,
            data=GitHubCommitListData(commits=commits, total=len(commits)),
        )
    except Exception as e:
        logger.exception("Failed to list GitHub commits for %s/%s", owner, repo)
        return GitHubCommitListResponse(
            success=False, error=f"Failed to list commits: {e}"
        )


@tool()
async def github_list_releases(
    owner: str,
    repo: str,
    per_page: int = 30,
) -> GitHubReleaseListResponse:
    """List releases in a GitHub repository, ordered by creation date descending.

    Args:
        owner: The repository owner (user or organization).
        repo: The repository name.
        per_page: Number of releases per page (max 100).

    Returns:
        List of releases in the repository.
    """
    try:
        headers, error = await _get_headers()
        if error or headers is None:
            return GitHubReleaseListResponse(success=False, error=error)

        if per_page < 1:
            return GitHubReleaseListResponse(
                success=False, error="per_page must be at least 1"
            )

        params = {"per_page": min(per_page, 100)}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/releases",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            releases_json = response.json()

        releases = [
            GitHubReleaseData(
                id=release["id"],
                tag_name=release["tag_name"],
                name=release.get("name"),
                body=release.get("body"),
                draft=release.get("draft", False),
                prerelease=release.get("prerelease", False),
                published_at=release.get("published_at"),
                url=release.get("html_url"),
            )
            for release in releases_json
        ]

        logger.info("Listed %d GitHub releases for %s/%s", len(releases), owner, repo)

        return GitHubReleaseListResponse(
            success=True,
            data=GitHubReleaseListData(releases=releases, total=len(releases)),
        )
    except Exception as e:
        logger.exception("Failed to list GitHub releases for %s/%s", owner, repo)
        return GitHubReleaseListResponse(
            success=False, error=f"Failed to list releases: {e}"
        )
