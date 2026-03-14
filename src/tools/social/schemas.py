"""Pydantic output schemas for social media tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# Reddit Schemas
# =============================================================================


class RedditPost(BaseModel):
    """A single Reddit post."""

    id: str = Field(..., description="Post ID")
    title: str = Field(..., description="Post title")
    score: int = Field(..., description="Post score (upvotes minus downvotes)")
    url: str = Field(..., description="Post URL")
    selftext: str = Field("", description="Self-text content of the post")
    author: str = Field(..., description="Author username")
    permalink: str = Field(..., description="Permalink to the post on Reddit")
    created_utc: float = Field(..., description="UTC timestamp of post creation")
    subreddit: str = Field(..., description="Subreddit name")
    num_comments: int = Field(0, description="Number of comments")


class RedditSearchData(BaseModel):
    """Output data for reddit_search_posts tool."""

    query: str = Field(..., description="The search query that was executed")
    subreddit: str | None = Field(None, description="Subreddit searched in, if any")
    results: list[RedditPost] = Field(
        default_factory=list, description="List of matching posts"
    )


class RedditPostData(BaseModel):
    """Output data for reddit_get_post tool."""

    post: RedditPost = Field(..., description="The requested post")


class RedditTopPostsData(BaseModel):
    """Output data for reddit_get_top_posts tool."""

    subreddit: str = Field(..., description="Subreddit name")
    time_filter: str = Field(..., description="Time filter used")
    posts: list[RedditPost] = Field(
        default_factory=list, description="List of top posts"
    )


class RedditHotPostsData(BaseModel):
    """Output data for reddit_get_hot_posts tool."""

    subreddit: str = Field(..., description="Subreddit name")
    posts: list[RedditPost] = Field(
        default_factory=list, description="List of hot posts"
    )


class RedditNewPostsData(BaseModel):
    """Output data for reddit_get_new_posts tool."""

    subreddit: str = Field(..., description="Subreddit name")
    posts: list[RedditPost] = Field(
        default_factory=list, description="List of newest posts"
    )


class RedditComment(BaseModel):
    """A single Reddit comment."""

    id: str = Field(..., description="Comment ID")
    body: str = Field("", description="Comment text")
    author: str = Field("[deleted]", description="Author username")
    score: int = Field(0, description="Comment score")
    created_utc: float = Field(0, description="UTC timestamp of creation")
    permalink: str = Field("", description="Permalink to the comment")
    is_submitter: bool = Field(
        False, description="Whether the author is the post author"
    )


class RedditCommentsData(BaseModel):
    """Output data for reddit_get_comments tool."""

    post_id: str = Field(..., description="Parent post ID")
    comments: list[RedditComment] = Field(
        default_factory=list, description="List of top-level comments"
    )


class RedditSubredditInfo(BaseModel):
    """Information about a subreddit."""

    display_name: str = Field(..., description="Subreddit display name")
    title: str = Field("", description="Subreddit title")
    public_description: str = Field("", description="Public description")
    subscribers: int = Field(0, description="Number of subscribers")
    active_user_count: int | None = Field(None, description="Active users online")
    created_utc: float = Field(0, description="UTC timestamp of creation")
    over18: bool = Field(False, description="Whether the subreddit is NSFW")
    url: str = Field("", description="Subreddit URL path")


class RedditSubredditInfoData(BaseModel):
    """Output data for reddit_get_subreddit_info tool."""

    subreddit: RedditSubredditInfo = Field(..., description="Subreddit information")


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
# Hacker News Schemas
# =============================================================================


class HackerNewsStory(BaseModel):
    """A single Hacker News story."""

    id: int = Field(..., description="Story ID")
    title: str = Field(..., description="Story title")
    url: str | None = Field(None, description="Story URL (None for Ask HN etc.)")
    score: int = Field(0, description="Story score")
    by: str = Field(..., description="Author username")
    time: int = Field(..., description="Unix timestamp of creation")
    descendants: int = Field(0, description="Number of comments")
    type: str = Field("story", description="Item type")


class HackerNewsTopStoriesData(BaseModel):
    """Output data for hackernews_get_top_stories tool."""

    stories: list[HackerNewsStory] = Field(
        default_factory=list, description="List of top stories"
    )


class HackerNewsStoryData(BaseModel):
    """Output data for hackernews_get_story tool."""

    story: HackerNewsStory = Field(..., description="The requested story")


class HackerNewsSearchResult(BaseModel):
    """A single Hacker News search result from Algolia."""

    objectID: str = Field(..., description="Story ID")
    title: str = Field(..., description="Story title")
    url: str | None = Field(None, description="Story URL")
    points: int | None = Field(None, description="Story score / points")
    author: str | None = Field(None, description="Author username")
    created_at: str | None = Field(None, description="Creation timestamp (ISO)")
    num_comments: int | None = Field(None, description="Number of comments")


class HackerNewsSearchData(BaseModel):
    """Output data for hackernews_search tool."""

    query: str = Field(..., description="The search query that was executed")
    results: list[HackerNewsSearchResult] = Field(
        default_factory=list, description="List of search results"
    )


class HackerNewsUser(BaseModel):
    """A Hacker News user profile."""

    id: str = Field(..., description="Username")
    created: int = Field(..., description="Unix timestamp of account creation")
    karma: int = Field(0, description="User karma score")
    about: str | None = Field(None, description="User bio (HTML)")
    submitted: list[int] = Field(
        default_factory=list,
        description="List of submitted item IDs (most recent first)",
    )


class HackerNewsUserData(BaseModel):
    """Output data for hackernews_get_user tool."""

    user: HackerNewsUser = Field(..., description="The requested user profile")


class HackerNewsComment(BaseModel):
    """A single Hacker News comment."""

    id: int = Field(..., description="Comment ID")
    by: str | None = Field(None, description="Author username")
    text: str | None = Field(None, description="Comment text (HTML)")
    time: int = Field(0, description="Unix timestamp of creation")
    parent: int = Field(0, description="Parent item ID")
    kids: list[int] = Field(default_factory=list, description="Child comment IDs")


class HackerNewsCommentsData(BaseModel):
    """Output data for hackernews_get_comments tool."""

    story_id: int = Field(..., description="Parent story ID")
    comments: list[HackerNewsComment] = Field(
        default_factory=list, description="List of comments"
    )


# =============================================================================
# YouTube Schemas
# =============================================================================


class YouTubeVideo(BaseModel):
    """A single YouTube video search result."""

    video_id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Video title")
    description: str | None = Field(None, description="Video description snippet")
    channel_id: str | None = Field(None, description="Channel ID")
    channel_title: str | None = Field(None, description="Channel name")
    published_at: str | None = Field(None, description="Publish date (ISO)")
    thumbnail_url: str | None = Field(None, description="Thumbnail URL")


class YouTubeSearchData(BaseModel):
    """Output data for youtube_search tool."""

    query: str = Field(..., description="The search query that was executed")
    results: list[YouTubeVideo] = Field(
        default_factory=list, description="List of matching videos"
    )


class YouTubeVideoInfoData(BaseModel):
    """Output data for youtube_get_video_info tool."""

    video_id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Video title")
    description: str | None = Field(None, description="Video description")
    channel_title: str | None = Field(None, description="Channel name")
    published_at: str | None = Field(None, description="Publish date (ISO)")
    view_count: int | None = Field(None, description="Number of views")
    like_count: int | None = Field(None, description="Number of likes")
    comment_count: int | None = Field(None, description="Number of comments")
    duration: str | None = Field(None, description="Video duration (ISO 8601)")
    thumbnail_url: str | None = Field(None, description="Thumbnail URL")


class YouTubeCaptionsData(BaseModel):
    """Output data for youtube_get_captions tool."""

    video_id: str = Field(..., description="YouTube video ID")
    captions: str = Field(..., description="Concatenated caption text")


class YouTubeChannelData(BaseModel):
    """Output data for youtube_get_channel tool."""

    channel_id: str = Field(..., description="YouTube channel ID")
    title: str = Field(..., description="Channel name")
    description: str | None = Field(None, description="Channel description")
    custom_url: str | None = Field(None, description="Custom channel URL handle")
    published_at: str | None = Field(None, description="Channel creation date (ISO)")
    thumbnail_url: str | None = Field(None, description="Channel thumbnail URL")
    subscriber_count: int | None = Field(None, description="Number of subscribers")
    video_count: int | None = Field(None, description="Number of uploaded videos")
    view_count: int | None = Field(None, description="Total channel views")
    uploads_playlist_id: str | None = Field(
        None, description="Playlist ID for the channel's uploaded videos"
    )


class YouTubePlaylistItem(BaseModel):
    """A single item in a YouTube playlist."""

    video_id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Video title")
    description: str | None = Field(None, description="Video description snippet")
    channel_id: str | None = Field(None, description="Video owner channel ID")
    channel_title: str | None = Field(None, description="Video owner channel name")
    published_at: str | None = Field(None, description="Date added to playlist (ISO)")
    position: int = Field(0, description="Position in the playlist")
    thumbnail_url: str | None = Field(None, description="Thumbnail URL")


class YouTubePlaylistItemsData(BaseModel):
    """Output data for youtube_get_playlist_items tool."""

    playlist_id: str = Field(..., description="Playlist ID")
    items: list[YouTubePlaylistItem] = Field(
        default_factory=list, description="List of playlist items"
    )
    total_results: int | None = Field(None, description="Total items in the playlist")


class YouTubeComment(BaseModel):
    """A single YouTube comment."""

    comment_id: str = Field(..., description="Comment ID")
    text: str = Field(..., description="Comment text")
    author: str = Field(..., description="Comment author display name")
    author_channel_id: str | None = Field(None, description="Author channel ID")
    like_count: int = Field(0, description="Number of likes on the comment")
    published_at: str | None = Field(None, description="Publish date (ISO)")
    updated_at: str | None = Field(None, description="Last update date (ISO)")
    reply_count: int = Field(0, description="Number of replies to this comment")


class YouTubeCommentsData(BaseModel):
    """Output data for youtube_get_comments tool."""

    video_id: str = Field(..., description="YouTube video ID")
    comments: list[YouTubeComment] = Field(
        default_factory=list, description="List of top-level comments"
    )
    total_results: int | None = Field(None, description="Total number of comments")


class XGetTweetData(BaseModel):
    """Output data for x_get_tweet tool."""

    tweet: XTweet = Field(..., description="The requested tweet")


class XReplyTweetData(BaseModel):
    """Output data for x_reply_to_tweet tool."""

    id: str = Field(..., description="Created reply tweet ID")
    text: str = Field(..., description="Reply tweet text")
    in_reply_to_tweet_id: str = Field(
        ..., description="Tweet ID that was replied to"
    )
    url: str = Field(..., description="URL to the reply tweet")


class XMentionsData(BaseModel):
    """Output data for x_get_mentions tool."""

    user_id: str = Field(..., description="User ID whose mentions were fetched")
    count: int = Field(0, description="Number of mentions returned")
    tweets: list[XTweet] = Field(
        default_factory=list, description="List of mention tweets"
    )


# =============================================================================
# LinkedIn Schemas
# =============================================================================


class LinkedInProfileData(BaseModel):
    """Output data for linkedin_get_profile tool."""

    urn: str | None = Field(None, description="LinkedIn member URN")
    first_name: str | None = Field(None, description="First name")
    last_name: str | None = Field(None, description="Last name")
    headline: str | None = Field(None, description="Profile headline")
    vanity_name: str | None = Field(None, description="Vanity/public profile URL slug")


class LinkedInShareData(BaseModel):
    """Output data for linkedin_create_share tool."""

    share_id: str | None = Field(None, description="ID of the created share/post")
    url: str | None = Field(None, description="URL to the created post")


# =============================================================================
# Instagram Business Schemas
# =============================================================================


class InstagramProfileData(BaseModel):
    """Output data for instagram_get_profile tool."""

    id: str | None = Field(None, description="Instagram Business account ID")
    username: str | None = Field(None, description="Instagram username")
    name: str | None = Field(None, description="Account display name")
    followers_count: int | None = Field(None, description="Number of followers")
    media_count: int | None = Field(None, description="Number of media posts")
    biography: str | None = Field(None, description="Profile biography")


class InstagramMediaData(BaseModel):
    """Output data for instagram_get_recent_media tool."""

    account_id: str = Field(..., description="Instagram Business account ID")
    count: int = Field(0, description="Number of media items returned")
    media: list[dict] = Field(
        default_factory=list, description="List of recent media items"
    )


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class RedditSearchResponse(ToolResponse[RedditSearchData]):
    """Response schema for reddit_search_posts tool."""

    pass


class RedditPostResponse(ToolResponse[RedditPostData]):
    """Response schema for reddit_get_post tool."""

    pass


class RedditTopPostsResponse(ToolResponse[RedditTopPostsData]):
    """Response schema for reddit_get_top_posts tool."""

    pass


class XPostTweetResponse(ToolResponse[XPostTweetData]):
    """Response schema for x_post_tweet tool."""

    pass


class XSearchTweetsResponse(ToolResponse[XSearchTweetsData]):
    """Response schema for x_search_tweets tool."""

    pass


class XUserResponse(ToolResponse[XUserData]):
    """Response schema for x_get_user tool."""

    pass


class HackerNewsTopStoriesResponse(ToolResponse[HackerNewsTopStoriesData]):
    """Response schema for hackernews_get_top_stories tool."""

    pass


class HackerNewsStoryResponse(ToolResponse[HackerNewsStoryData]):
    """Response schema for hackernews_get_story tool."""

    pass


class HackerNewsSearchResponse(ToolResponse[HackerNewsSearchData]):
    """Response schema for hackernews_search tool."""

    pass


class YouTubeSearchResponse(ToolResponse[YouTubeSearchData]):
    """Response schema for youtube_search tool."""

    pass


class YouTubeVideoInfoResponse(ToolResponse[YouTubeVideoInfoData]):
    """Response schema for youtube_get_video_info tool."""

    pass


class YouTubeCaptionsResponse(ToolResponse[YouTubeCaptionsData]):
    """Response schema for youtube_get_captions tool."""

    pass


class YouTubeChannelResponse(ToolResponse[YouTubeChannelData]):
    """Response schema for youtube_get_channel tool."""

    pass


class YouTubePlaylistItemsResponse(ToolResponse[YouTubePlaylistItemsData]):
    """Response schema for youtube_get_playlist_items tool."""

    pass


class HackerNewsUserResponse(ToolResponse[HackerNewsUserData]):
    """Response schema for hackernews_get_user tool."""

    pass


class HackerNewsCommentsResponse(ToolResponse[HackerNewsCommentsData]):
    """Response schema for hackernews_get_comments tool."""

    pass


class HackerNewsSearchByDateResponse(ToolResponse[HackerNewsSearchData]):
    """Response schema for hackernews_search_by_date tool."""

    pass


class RedditHotPostsResponse(ToolResponse[RedditHotPostsData]):
    """Response schema for reddit_get_hot_posts tool."""

    pass


class RedditCommentsResponse(ToolResponse[RedditCommentsData]):
    """Response schema for reddit_get_comments tool."""

    pass


class RedditSubredditInfoResponse(ToolResponse[RedditSubredditInfoData]):
    """Response schema for reddit_get_subreddit_info tool."""

    pass


class XUserTweetsResponse(ToolResponse[XUserTweetsData]):
    """Response schema for x_get_user_tweets tool."""

    pass


class RedditNewPostsResponse(ToolResponse[RedditNewPostsData]):
    """Response schema for reddit_get_new_posts tool."""

    pass


class YouTubeCommentsResponse(ToolResponse[YouTubeCommentsData]):
    """Response schema for youtube_get_comments tool."""

    pass


class XGetTweetResponse(ToolResponse[XGetTweetData]):
    """Response schema for x_get_tweet tool."""

    pass


class XReplyTweetResponse(ToolResponse[XReplyTweetData]):
    """Response schema for x_reply_to_tweet tool."""

    pass


class XMentionsResponse(ToolResponse[XMentionsData]):
    """Response schema for x_get_mentions tool."""

    pass


class LinkedInProfileResponse(ToolResponse[LinkedInProfileData]):
    """Response schema for linkedin_get_profile tool."""

    pass


class LinkedInShareResponse(ToolResponse[LinkedInShareData]):
    """Response schema for linkedin_create_share tool."""

    pass


class InstagramProfileResponse(ToolResponse[InstagramProfileData]):
    """Response schema for instagram_get_profile tool."""

    pass


class InstagramMediaResponse(ToolResponse[InstagramMediaData]):
    """Response schema for instagram_get_recent_media tool."""

    pass
