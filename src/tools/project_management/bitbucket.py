"""Bitbucket tools for repository, pull request, and commit management.

Uses the Bitbucket Cloud REST API 2.0. Requires BITBUCKET_USERNAME and
BITBUCKET_APP_PASSWORD environment variables.

API Reference: https://developer.atlassian.com/cloud/bitbucket/rest/
"""

from __future__ import annotations

import logging

import httpx

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.project_management.schemas import (
    BitbucketCommitData,
    BitbucketCommitListData,
    BitbucketCommitListResponse,
    BitbucketPullRequestData,
    BitbucketPullRequestListData,
    BitbucketPullRequestListResponse,
    BitbucketPullRequestResponse,
    BitbucketRepoData,
    BitbucketRepoListData,
    BitbucketRepoListResponse,
    BitbucketRepoResponse,
)

logger = logging.getLogger("humcp.tools.bitbucket")

BITBUCKET_API_BASE = "https://api.bitbucket.org/2.0"


async def _get_auth() -> tuple[tuple[str, str] | None, str | None]:
    """Build Bitbucket basic auth credentials from environment variables.

    Returns:
        A tuple of ((username, app_password), error_message).
    """
    username = await resolve_credential("BITBUCKET_USERNAME")
    app_password = await resolve_credential("BITBUCKET_APP_PASSWORD")

    if not username:
        return (
            None,
            "Bitbucket username not configured. Set BITBUCKET_USERNAME environment variable.",
        )
    if not app_password:
        return (
            None,
            "Bitbucket app password not configured. Set BITBUCKET_APP_PASSWORD environment variable.",
        )

    return (username, app_password), None


@tool()
async def bitbucket_list_repos(
    workspace: str,
    page_len: int = 25,
) -> BitbucketRepoListResponse:
    """List repositories in a Bitbucket workspace.

    Args:
        workspace: The Bitbucket workspace slug or UUID.
        page_len: Maximum number of repositories to return (max 100).

    Returns:
        List of repositories in the workspace.
    """
    try:
        auth, error = await _get_auth()
        if error or auth is None:
            return BitbucketRepoListResponse(success=False, error=error)

        if page_len < 1:
            return BitbucketRepoListResponse(
                success=False, error="page_len must be at least 1"
            )

        params = {"pagelen": min(page_len, 100)}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BITBUCKET_API_BASE}/repositories/{workspace}",
                params=params,
                auth=auth,
            )
            response.raise_for_status()
            data = response.json()

        repos = [
            BitbucketRepoData(
                slug=repo["slug"],
                name=repo.get("name", repo["slug"]),
                full_name=repo.get("full_name"),
                description=repo.get("description"),
                is_private=repo.get("is_private", False),
                language=repo.get("language"),
                url=repo.get("links", {}).get("html", {}).get("href"),
            )
            for repo in data.get("values", [])
        ]

        logger.info("Listed %d Bitbucket repos in workspace %s", len(repos), workspace)

        return BitbucketRepoListResponse(
            success=True,
            data=BitbucketRepoListData(
                repos=repos,
                total=data.get("size", len(repos)),
            ),
        )
    except Exception as e:
        logger.exception("Failed to list Bitbucket repos for workspace %s", workspace)
        return BitbucketRepoListResponse(
            success=False, error=f"Failed to list repos: {e}"
        )


@tool()
async def bitbucket_get_repo(
    workspace: str,
    repo_slug: str,
) -> BitbucketRepoResponse:
    """Get details of a specific Bitbucket repository.

    Args:
        workspace: The Bitbucket workspace slug or UUID.
        repo_slug: The repository slug.

    Returns:
        Repository details including name, description, language, and visibility.
    """
    try:
        auth, error = await _get_auth()
        if error or auth is None:
            return BitbucketRepoResponse(success=False, error=error)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BITBUCKET_API_BASE}/repositories/{workspace}/{repo_slug}",
                auth=auth,
            )
            response.raise_for_status()
            repo = response.json()

        data = BitbucketRepoData(
            slug=repo["slug"],
            name=repo.get("name", repo["slug"]),
            full_name=repo.get("full_name"),
            description=repo.get("description"),
            is_private=repo.get("is_private", False),
            language=repo.get("language"),
            url=repo.get("links", {}).get("html", {}).get("href"),
        )

        return BitbucketRepoResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to get Bitbucket repo %s/%s", workspace, repo_slug)
        return BitbucketRepoResponse(
            success=False, error=f"Failed to get repository: {e}"
        )


@tool()
async def bitbucket_create_pr(
    workspace: str,
    repo_slug: str,
    title: str,
    source_branch: str,
    dest_branch: str = "main",
    description: str = "",
    close_source_branch: bool = False,
) -> BitbucketPullRequestResponse:
    """Create a pull request in a Bitbucket repository.

    Args:
        workspace: The Bitbucket workspace slug or UUID.
        repo_slug: The repository slug.
        title: The title of the pull request.
        source_branch: The source branch name.
        dest_branch: The destination branch name (defaults to "main").
        description: Optional description for the pull request.
        close_source_branch: Whether to close the source branch after merge.

    Returns:
        Details of the newly created pull request.
    """
    try:
        auth, error = await _get_auth()
        if error or auth is None:
            return BitbucketPullRequestResponse(success=False, error=error)

        payload: dict = {
            "title": title,
            "description": description,
            "source": {"branch": {"name": source_branch}},
            "destination": {"branch": {"name": dest_branch}},
            "close_source_branch": close_source_branch,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BITBUCKET_API_BASE}/repositories/{workspace}/{repo_slug}/pullrequests",
                json=payload,
                auth=auth,
            )
            response.raise_for_status()
            pr = response.json()

        data = BitbucketPullRequestData(
            id=pr["id"],
            title=pr["title"],
            description=pr.get("description"),
            state=pr.get("state"),
            author=pr.get("author", {}).get("display_name")
            if pr.get("author")
            else None,
            source_branch=pr.get("source", {}).get("branch", {}).get("name"),
            dest_branch=pr.get("destination", {}).get("branch", {}).get("name"),
            url=pr.get("links", {}).get("html", {}).get("href"),
            created_on=pr.get("created_on"),
        )

        logger.info("Created Bitbucket PR #%d in %s/%s", pr["id"], workspace, repo_slug)

        return BitbucketPullRequestResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to create Bitbucket PR in %s/%s", workspace, repo_slug)
        return BitbucketPullRequestResponse(
            success=False, error=f"Failed to create pull request: {e}"
        )


@tool()
async def bitbucket_list_pull_requests(
    workspace: str,
    repo_slug: str,
    state: str = "OPEN",
    page_len: int = 25,
) -> BitbucketPullRequestListResponse:
    """List pull requests in a Bitbucket repository.

    Args:
        workspace: The Bitbucket workspace slug or UUID.
        repo_slug: The repository slug.
        state: Filter by PR state: "OPEN", "MERGED", "DECLINED", or "SUPERSEDED".
            Can be comma-separated for multiple states (e.g., "OPEN,MERGED").
        page_len: Maximum number of pull requests to return (max 50).

    Returns:
        List of pull requests matching the filter.
    """
    try:
        auth, error = await _get_auth()
        if error or auth is None:
            return BitbucketPullRequestListResponse(success=False, error=error)

        if page_len < 1:
            return BitbucketPullRequestListResponse(
                success=False, error="page_len must be at least 1"
            )

        params: dict = {
            "state": state,
            "pagelen": min(page_len, 50),
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BITBUCKET_API_BASE}/repositories/{workspace}/{repo_slug}/pullrequests",
                params=params,
                auth=auth,
            )
            response.raise_for_status()
            result = response.json()

        pull_requests = [
            BitbucketPullRequestData(
                id=pr["id"],
                title=pr["title"],
                description=pr.get("description"),
                state=pr.get("state"),
                author=pr.get("author", {}).get("display_name")
                if pr.get("author")
                else None,
                source_branch=pr.get("source", {}).get("branch", {}).get("name"),
                dest_branch=pr.get("destination", {}).get("branch", {}).get("name"),
                url=pr.get("links", {}).get("html", {}).get("href"),
                created_on=pr.get("created_on"),
            )
            for pr in result.get("values", [])
        ]

        logger.info(
            "Listed %d Bitbucket PRs in %s/%s (state=%s)",
            len(pull_requests),
            workspace,
            repo_slug,
            state,
        )

        return BitbucketPullRequestListResponse(
            success=True,
            data=BitbucketPullRequestListData(
                pull_requests=pull_requests,
                total=result.get("size", len(pull_requests)),
            ),
        )
    except Exception as e:
        logger.exception("Failed to list Bitbucket PRs in %s/%s", workspace, repo_slug)
        return BitbucketPullRequestListResponse(
            success=False, error=f"Failed to list pull requests: {e}"
        )


@tool()
async def bitbucket_list_commits(
    workspace: str,
    repo_slug: str,
    branch: str | None = None,
    page_len: int = 25,
) -> BitbucketCommitListResponse:
    """List commits in a Bitbucket repository.

    Args:
        workspace: The Bitbucket workspace slug or UUID.
        repo_slug: The repository slug.
        branch: Optional branch name or commit hash to list commits from.
        page_len: Maximum number of commits to return (max 100).

    Returns:
        List of commits in the repository.
    """
    try:
        auth, error = await _get_auth()
        if error or auth is None:
            return BitbucketCommitListResponse(success=False, error=error)

        if page_len < 1:
            return BitbucketCommitListResponse(
                success=False, error="page_len must be at least 1"
            )

        url = f"{BITBUCKET_API_BASE}/repositories/{workspace}/{repo_slug}/commits"
        if branch:
            url = f"{url}/{branch}"

        params = {"pagelen": min(page_len, 100)}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, auth=auth)
            response.raise_for_status()
            result = response.json()

        commits = [
            BitbucketCommitData(
                hash=commit["hash"],
                message=commit.get("message", ""),
                author=(
                    commit.get("author", {}).get("user", {}).get("display_name")
                    if commit.get("author", {}).get("user")
                    else commit.get("author", {}).get("raw", "").split("<")[0].strip()
                ),
                date=commit.get("date"),
                url=commit.get("links", {}).get("html", {}).get("href"),
            )
            for commit in result.get("values", [])
        ]

        logger.info(
            "Listed %d Bitbucket commits in %s/%s",
            len(commits),
            workspace,
            repo_slug,
        )

        return BitbucketCommitListResponse(
            success=True,
            data=BitbucketCommitListData(commits=commits, total=len(commits)),
        )
    except Exception as e:
        logger.exception(
            "Failed to list Bitbucket commits in %s/%s", workspace, repo_slug
        )
        return BitbucketCommitListResponse(
            success=False, error=f"Failed to list commits: {e}"
        )
