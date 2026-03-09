"""Pydantic output schemas for social media tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# X / Twitter Schemas
# =============================================================================


class XTweetPublicMetrics(BaseModel):
    """Public engagement metrics for a tweet."""

    retweet_count: int = Field(0, description="Number of retweets")
    reply_count: int = Field(0, description="Number of replies")
    like_count: int = Field(0, description="Number of likes")
    quote_count: int = Field(0, description="Number of quote tweets")
    bookmark_count: int = Field(0, description="Number of bookmarks")
    impression_count: int = Field(0, description="Number of impressions")


class XTweet(BaseModel):
    """A single X/Twitter tweet."""

    id: str = Field(..., description="Tweet ID")
    text: str = Field(..., description="Tweet text content")
    author_id: str | None = Field(None, description="Author user ID")
    author_username: str | None = Field(None, description="Author username")
    created_at: str | None = Field(None, description="Creation timestamp")
    url: str | None = Field(None, description="URL to the tweet")
    public_metrics: XTweetPublicMetrics | None = Field(
        None, description="Public engagement metrics"
    )


class XPostTweetData(BaseModel):
    """Output data for x_post_tweet tool."""

    id: str = Field(..., description="Created tweet ID")
    text: str = Field(..., description="Tweet text")
    url: str = Field(..., description="URL to the created tweet")


class XSearchTweetsData(BaseModel):
    """Output data for x_search_tweets tool."""

    query: str = Field(..., description="The search query that was executed")
    count: int = Field(0, description="Number of results returned")
    tweets: list[XTweet] = Field(
        default_factory=list, description="List of matching tweets"
    )


class XUserTweetsData(BaseModel):
    """Output data for x_get_user_tweets tool."""

    user_id: str = Field(..., description="User ID whose tweets were fetched")
    username: str | None = Field(None, description="Username / handle")
    count: int = Field(0, description="Number of tweets returned")
    tweets: list[XTweet] = Field(
        default_factory=list, description="List of user tweets"
    )


class XUserData(BaseModel):
    """Output data for x_get_user tool."""

    id: str = Field(..., description="User ID")
    name: str = Field(..., description="Display name")
    username: str = Field(..., description="Username / handle")
    description: str | None = Field(None, description="User bio")
    profile_image_url: str | None = Field(None, description="Profile image URL")
    location: str | None = Field(None, description="User location")
    url: str | None = Field(None, description="User website URL")
    created_at: str | None = Field(None, description="Account creation date (ISO)")
    verified: bool = Field(False, description="Whether the user is verified")
    followers_count: int = Field(0, description="Number of followers")
    following_count: int = Field(0, description="Number of accounts followed")
    tweet_count: int = Field(0, description="Total number of tweets")
    listed_count: int = Field(0, description="Number of lists the user is a member of")


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class XPostTweetResponse(ToolResponse[XPostTweetData]):
    """Response schema for x_post_tweet tool."""

    pass


class XSearchTweetsResponse(ToolResponse[XSearchTweetsData]):
    """Response schema for x_search_tweets tool."""

    pass


class XUserResponse(ToolResponse[XUserData]):
    """Response schema for x_get_user tool."""

    pass


class XUserTweetsResponse(ToolResponse[XUserTweetsData]):
    """Response schema for x_get_user_tweets tool."""

    pass
