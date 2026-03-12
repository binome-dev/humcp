"""Reddit tools for searching and browsing posts via PRAW."""

from __future__ import annotations

import logging
from typing import Any

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.social.schemas import (
    RedditComment,
    RedditCommentsData,
    RedditCommentsResponse,
    RedditHotPostsData,
    RedditHotPostsResponse,
    RedditPost,
    RedditPostData,
    RedditPostResponse,
    RedditSearchData,
    RedditSearchResponse,
    RedditSubredditInfo,
    RedditSubredditInfoData,
    RedditSubredditInfoResponse,
    RedditTopPostsData,
    RedditTopPostsResponse,
)

try:
    import praw  # type: ignore
except ImportError as err:
    raise ImportError(
        "praw is required for Reddit tools. Install with: pip install praw"
    ) from err

logger = logging.getLogger("humcp.tools.reddit")


def _get_reddit_client(
    client_id: str | None,
    client_secret: str | None,
    user_agent: str | None,
) -> praw.Reddit | None:
    """Create a read-only Reddit client from resolved credentials."""
    if not client_id or not client_secret:
        return None

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent or "HuMCP Reddit Tools v1.0",
    )


def _submission_to_post(submission: Any) -> RedditPost:
    """Convert a PRAW submission object to a RedditPost model."""
    return RedditPost(
        id=submission.id,
        title=submission.title,
        score=submission.score,
        url=submission.url,
        selftext=submission.selftext or "",
        author=str(submission.author) if submission.author else "[deleted]",
        permalink=f"https://reddit.com{submission.permalink}",
        created_utc=submission.created_utc,
        subreddit=str(submission.subreddit),
        num_comments=submission.num_comments,
    )


@tool()
async def reddit_search_posts(
    query: str,
    subreddit: str | None = None,
    sort: str = "relevance",
    time_filter: str = "all",
    limit: int = 10,
) -> RedditSearchResponse:
    """Search Reddit posts by query, optionally within a specific subreddit.

    Args:
        query: The search query string.
        subreddit: Optional subreddit to search within (e.g. "python"). Searches all of Reddit if omitted.
        sort: Sort order for results. One of "relevance", "hot", "top", "new", "comments". Default is "relevance".
        time_filter: Time period filter for results. One of "all", "day", "hour", "month", "week", "year". Default is "all".
        limit: Maximum number of results to return (default 10, max 100).

    Returns:
        Matching posts or an error message.
    """
    try:
        client_id = await resolve_credential("REDDIT_CLIENT_ID")
        client_secret = await resolve_credential("REDDIT_CLIENT_SECRET")
        user_agent = await resolve_credential("REDDIT_USER_AGENT")
        reddit = _get_reddit_client(client_id, client_secret, user_agent)
        if reddit is None:
            return RedditSearchResponse(
                success=False,
                error="Reddit API not configured. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.",
            )

        valid_sorts = {"relevance", "hot", "top", "new", "comments"}
        if sort not in valid_sorts:
            return RedditSearchResponse(
                success=False,
                error=f"Invalid sort '{sort}'. Must be one of: {', '.join(sorted(valid_sorts))}",
            )

        valid_time_filters = {"all", "day", "hour", "month", "week", "year"}
        if time_filter not in valid_time_filters:
            return RedditSearchResponse(
                success=False,
                error=f"Invalid time_filter '{time_filter}'. Must be one of: {', '.join(sorted(valid_time_filters))}",
            )

        limit = max(1, min(limit, 100))
        logger.info(
            "Reddit search query=%r subreddit=%s sort=%s limit=%d",
            query,
            subreddit,
            sort,
            limit,
        )

        if subreddit:
            target = reddit.subreddit(subreddit)
        else:
            target = reddit.subreddit("all")

        submissions = target.search(
            query,
            sort=sort,
            time_filter=time_filter,
            limit=limit,
        )
        posts = [_submission_to_post(s) for s in submissions]

        logger.info("Reddit search complete results=%d", len(posts))
        return RedditSearchResponse(
            success=True,
            data=RedditSearchData(
                query=query,
                subreddit=subreddit,
                results=posts,
            ),
        )
    except Exception as e:
        logger.exception("Reddit search failed")
        return RedditSearchResponse(success=False, error=f"Reddit search failed: {e}")


@tool()
async def reddit_get_post(post_id: str) -> RedditPostResponse:
    """Get a specific Reddit post by its ID.

    Args:
        post_id: The Reddit post ID (e.g. "1abc23d").

    Returns:
        The post details or an error message.
    """
    try:
        client_id = await resolve_credential("REDDIT_CLIENT_ID")
        client_secret = await resolve_credential("REDDIT_CLIENT_SECRET")
        user_agent = await resolve_credential("REDDIT_USER_AGENT")
        reddit = _get_reddit_client(client_id, client_secret, user_agent)
        if reddit is None:
            return RedditPostResponse(
                success=False,
                error="Reddit API not configured. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.",
            )

        logger.info("Reddit get post id=%s", post_id)
        submission = reddit.submission(id=post_id)
        # Force-load attributes
        _ = submission.title

        post = _submission_to_post(submission)
        return RedditPostResponse(
            success=True,
            data=RedditPostData(post=post),
        )
    except Exception as e:
        logger.exception("Reddit get post failed")
        return RedditPostResponse(success=False, error=f"Reddit get post failed: {e}")


@tool()
async def reddit_get_top_posts(
    subreddit: str,
    time_filter: str = "week",
    limit: int = 10,
) -> RedditTopPostsResponse:
    """Get the top posts from a subreddit for a given time period.

    Args:
        subreddit: Name of the subreddit (e.g. "python").
        time_filter: Time period filter. One of "hour", "day", "week", "month", "year", "all". Default is "week".
        limit: Maximum number of posts to return (default 10, max 100).

    Returns:
        Top posts or an error message.
    """
    try:
        client_id = await resolve_credential("REDDIT_CLIENT_ID")
        client_secret = await resolve_credential("REDDIT_CLIENT_SECRET")
        user_agent = await resolve_credential("REDDIT_USER_AGENT")
        reddit = _get_reddit_client(client_id, client_secret, user_agent)
        if reddit is None:
            return RedditTopPostsResponse(
                success=False,
                error="Reddit API not configured. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.",
            )

        valid_filters = {"hour", "day", "week", "month", "year", "all"}
        if time_filter not in valid_filters:
            return RedditTopPostsResponse(
                success=False,
                error=f"Invalid time_filter '{time_filter}'. Must be one of: {', '.join(sorted(valid_filters))}",
            )

        limit = max(1, min(limit, 100))
        logger.info(
            "Reddit top posts subreddit=%s time_filter=%s limit=%d",
            subreddit,
            time_filter,
            limit,
        )

        submissions = reddit.subreddit(subreddit).top(
            time_filter=time_filter, limit=limit
        )
        posts = [_submission_to_post(s) for s in submissions]

        logger.info("Reddit top posts complete results=%d", len(posts))
        return RedditTopPostsResponse(
            success=True,
            data=RedditTopPostsData(
                subreddit=subreddit,
                time_filter=time_filter,
                posts=posts,
            ),
        )
    except Exception as e:
        logger.exception("Reddit top posts failed")
        return RedditTopPostsResponse(
            success=False, error=f"Reddit top posts failed: {e}"
        )


@tool()
async def reddit_get_hot_posts(
    subreddit: str,
    limit: int = 10,
) -> RedditHotPostsResponse:
    """Get the current hot posts from a subreddit.

    Hot posts are ranked by Reddit's hotness algorithm, which considers
    recency and engagement (upvotes, comments).

    Args:
        subreddit: Name of the subreddit (e.g. "python").
        limit: Maximum number of posts to return (default 10, max 100).

    Returns:
        Hot posts or an error message.
    """
    try:
        client_id = await resolve_credential("REDDIT_CLIENT_ID")
        client_secret = await resolve_credential("REDDIT_CLIENT_SECRET")
        user_agent = await resolve_credential("REDDIT_USER_AGENT")
        reddit = _get_reddit_client(client_id, client_secret, user_agent)
        if reddit is None:
            return RedditHotPostsResponse(
                success=False,
                error="Reddit API not configured. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.",
            )

        limit = max(1, min(limit, 100))
        logger.info("Reddit hot posts subreddit=%s limit=%d", subreddit, limit)

        submissions = reddit.subreddit(subreddit).hot(limit=limit)
        posts = [_submission_to_post(s) for s in submissions]

        logger.info("Reddit hot posts complete results=%d", len(posts))
        return RedditHotPostsResponse(
            success=True,
            data=RedditHotPostsData(
                subreddit=subreddit,
                posts=posts,
            ),
        )
    except Exception as e:
        logger.exception("Reddit hot posts failed")
        return RedditHotPostsResponse(
            success=False, error=f"Reddit hot posts failed: {e}"
        )


@tool()
async def reddit_get_comments(
    post_id: str,
    sort: str = "best",
    limit: int = 20,
) -> RedditCommentsResponse:
    """Get top-level comments for a Reddit post.

    Args:
        post_id: The Reddit post ID (e.g. "1abc23d").
        sort: Sort order for comments. One of "best", "top", "new", "controversial", "old", "q&a". Default is "best".
        limit: Maximum number of top-level comments to return (default 20, max 100).

    Returns:
        List of top-level comments or an error message.
    """
    try:
        client_id = await resolve_credential("REDDIT_CLIENT_ID")
        client_secret = await resolve_credential("REDDIT_CLIENT_SECRET")
        user_agent = await resolve_credential("REDDIT_USER_AGENT")
        reddit = _get_reddit_client(client_id, client_secret, user_agent)
        if reddit is None:
            return RedditCommentsResponse(
                success=False,
                error="Reddit API not configured. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.",
            )

        limit = max(1, min(limit, 100))
        logger.info(
            "Reddit get comments post_id=%s sort=%s limit=%d", post_id, sort, limit
        )

        submission = reddit.submission(id=post_id)
        submission.comment_sort = sort
        submission.comment_limit = limit
        submission.comments.replace_more(limit=0)

        comments: list[RedditComment] = []
        for comment in submission.comments[:limit]:
            comments.append(
                RedditComment(
                    id=comment.id,
                    body=comment.body or "",
                    author=str(comment.author) if comment.author else "[deleted]",
                    score=comment.score,
                    created_utc=comment.created_utc,
                    permalink=f"https://reddit.com{comment.permalink}",
                    is_submitter=comment.is_submitter,
                )
            )

        logger.info("Reddit get comments complete results=%d", len(comments))
        return RedditCommentsResponse(
            success=True,
            data=RedditCommentsData(
                post_id=post_id,
                comments=comments,
            ),
        )
    except Exception as e:
        logger.exception("Reddit get comments failed")
        return RedditCommentsResponse(
            success=False, error=f"Reddit get comments failed: {e}"
        )


@tool()
async def reddit_get_subreddit_info(
    subreddit: str,
) -> RedditSubredditInfoResponse:
    """Get information about a subreddit including description, subscriber count, and rules.

    Args:
        subreddit: Name of the subreddit (e.g. "python").

    Returns:
        Subreddit metadata or an error message.
    """
    try:
        client_id = await resolve_credential("REDDIT_CLIENT_ID")
        client_secret = await resolve_credential("REDDIT_CLIENT_SECRET")
        user_agent = await resolve_credential("REDDIT_USER_AGENT")
        reddit = _get_reddit_client(client_id, client_secret, user_agent)
        if reddit is None:
            return RedditSubredditInfoResponse(
                success=False,
                error="Reddit API not configured. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.",
            )

        logger.info("Reddit get subreddit info name=%s", subreddit)

        sub = reddit.subreddit(subreddit)
        # Force load attributes
        _ = sub.display_name

        info = RedditSubredditInfo(
            display_name=sub.display_name,
            title=sub.title or "",
            public_description=sub.public_description or "",
            subscribers=sub.subscribers or 0,
            active_user_count=getattr(sub, "accounts_active", None),
            created_utc=sub.created_utc or 0,
            over18=sub.over18 or False,
            url=f"https://reddit.com{sub.url}",
        )

        return RedditSubredditInfoResponse(
            success=True,
            data=RedditSubredditInfoData(subreddit=info),
        )
    except Exception as e:
        logger.exception("Reddit get subreddit info failed")
        return RedditSubredditInfoResponse(
            success=False, error=f"Reddit get subreddit info failed: {e}"
        )
