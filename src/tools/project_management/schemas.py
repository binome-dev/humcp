"""Pydantic output schemas for project management tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# Shared Issue / Task Schemas
# =============================================================================


class IssueData(BaseModel):
    """A single issue or task from any project management service."""

    id: str = Field(..., description="Unique identifier of the issue")
    title: str = Field(..., description="Title or summary of the issue")
    description: str | None = Field(
        None, description="Description or body of the issue"
    )
    status: str | None = Field(None, description="Current status of the issue")
    assignee: str | None = Field(
        None, description="Assignee display name or identifier"
    )
    url: str | None = Field(None, description="URL to view the issue in the browser")


class IssueListData(BaseModel):
    """A list of issues or tasks."""

    issues: list[IssueData] = Field(default_factory=list, description="List of issues")
    total: int | None = Field(None, description="Total number of matching issues")


# =============================================================================
# Jira-Specific Schemas
# =============================================================================


class JiraIssueData(BaseModel):
    """A Jira issue with Jira-specific fields."""

    key: str = Field(..., description="Jira issue key (e.g., PROJ-123)")
    project: str | None = Field(None, description="Project key")
    issue_type: str | None = Field(
        None, description="Issue type (e.g., Task, Bug, Story)"
    )
    summary: str = Field(..., description="Issue summary")
    description: str | None = Field(None, description="Issue description")
    status: str | None = Field(None, description="Current status")
    priority: str | None = Field(
        None, description="Issue priority (e.g., High, Medium, Low)"
    )
    assignee: str | None = Field(None, description="Assignee display name")
    reporter: str | None = Field(None, description="Reporter display name")
    labels: list[str] = Field(default_factory=list, description="Issue labels")
    url: str | None = Field(None, description="URL to the issue")


class JiraIssueListData(BaseModel):
    """A list of Jira issues from a JQL search."""

    issues: list[JiraIssueData] = Field(
        default_factory=list, description="List of Jira issues"
    )
    total: int | None = Field(None, description="Total number of matching issues")


class JiraProjectData(BaseModel):
    """A Jira project."""

    key: str = Field(..., description="Project key (e.g., PROJ)")
    name: str = Field(..., description="Project name")
    project_type: str | None = Field(None, description="Project type key")
    lead: str | None = Field(None, description="Project lead display name")
    url: str | None = Field(None, description="URL to the project")


class JiraProjectListData(BaseModel):
    """A list of Jira projects."""

    projects: list[JiraProjectData] = Field(
        default_factory=list, description="List of Jira projects"
    )
    total: int | None = Field(None, description="Total number of projects")


class JiraTransitionData(BaseModel):
    """A Jira issue transition."""

    id: str = Field(..., description="Transition ID")
    name: str = Field(..., description="Transition name")
    to_status: str | None = Field(None, description="Target status name")


class JiraTransitionListData(BaseModel):
    """A list of available transitions for a Jira issue."""

    issue_key: str = Field(..., description="The Jira issue key")
    transitions: list[JiraTransitionData] = Field(
        default_factory=list, description="List of available transitions"
    )
    total: int | None = Field(None, description="Total number of available transitions")


class JiraCommentData(BaseModel):
    """A Jira issue comment."""

    id: str = Field(..., description="Comment ID")
    body: str = Field(..., description="Comment body text")
    author: str | None = Field(None, description="Author display name")
    created: str | None = Field(None, description="Creation timestamp")
    url: str | None = Field(None, description="URL to the comment")


# =============================================================================
# Linear-Specific Schemas
# =============================================================================


class LinearIssueData(BaseModel):
    """A Linear issue."""

    id: str = Field(..., description="Linear issue ID")
    identifier: str | None = Field(None, description="Issue identifier (e.g., ENG-123)")
    title: str = Field(..., description="Issue title")
    description: str | None = Field(None, description="Issue description (Markdown)")
    status: str | None = Field(None, description="Issue state name")
    assignee: str | None = Field(None, description="Assignee name")
    url: str | None = Field(None, description="URL to the issue")
    priority: int | None = Field(
        None, description="Priority level (0=None, 1=Urgent, 2=High, 3=Medium, 4=Low)"
    )
    labels: list[str] = Field(default_factory=list, description="Label names")


class LinearIssueListData(BaseModel):
    """A list of Linear issues."""

    issues: list[LinearIssueData] = Field(
        default_factory=list, description="List of Linear issues"
    )
    total: int | None = Field(None, description="Total count of issues")


class LinearTeamData(BaseModel):
    """A Linear team."""

    id: str = Field(..., description="Team ID")
    name: str = Field(..., description="Team name")
    key: str = Field(..., description="Team key prefix (e.g., ENG)")
    description: str | None = Field(None, description="Team description")


class LinearTeamListData(BaseModel):
    """A list of Linear teams."""

    teams: list[LinearTeamData] = Field(
        default_factory=list, description="List of teams"
    )
    total: int | None = Field(None, description="Total count of teams")


class LinearCycleData(BaseModel):
    """A Linear cycle (sprint)."""

    id: str = Field(..., description="Cycle ID")
    number: int = Field(..., description="Cycle number within the team")
    name: str | None = Field(None, description="Cycle name")
    starts_at: str | None = Field(None, description="Cycle start date (ISO 8601)")
    ends_at: str | None = Field(None, description="Cycle end date (ISO 8601)")
    completed_at: str | None = Field(
        None, description="Cycle completion date (ISO 8601)"
    )
    progress: float | None = Field(
        None, description="Cycle progress as a fraction (0.0 to 1.0)"
    )
    scope_count: int | None = Field(
        None, description="Total number of issues in the cycle"
    )
    completed_count: int | None = Field(None, description="Number of completed issues")


class LinearCycleListData(BaseModel):
    """A list of Linear cycles."""

    cycles: list[LinearCycleData] = Field(
        default_factory=list, description="List of cycles"
    )
    total: int | None = Field(None, description="Total count of cycles")


# =============================================================================
# ClickUp-Specific Schemas
# =============================================================================


class ClickUpTaskData(BaseModel):
    """A ClickUp task."""

    id: str = Field(..., description="ClickUp task ID")
    name: str = Field(..., description="Task name")
    description: str | None = Field(None, description="Task description")
    status: str | None = Field(None, description="Task status")
    priority: str | None = Field(None, description="Task priority")
    assignees: list[str] = Field(
        default_factory=list, description="List of assignee names"
    )
    due_date: str | None = Field(None, description="Due date as Unix timestamp in ms")
    url: str | None = Field(None, description="URL to the task")


class ClickUpTaskListData(BaseModel):
    """A list of ClickUp tasks."""

    tasks: list[ClickUpTaskData] = Field(
        default_factory=list, description="List of tasks"
    )
    total: int | None = Field(None, description="Total count of tasks")


class ClickUpSpaceData(BaseModel):
    """A ClickUp space."""

    id: str = Field(..., description="Space ID")
    name: str = Field(..., description="Space name")
    private: bool = Field(False, description="Whether the space is private")


class ClickUpSpaceListData(BaseModel):
    """A list of ClickUp spaces."""

    spaces: list[ClickUpSpaceData] = Field(
        default_factory=list, description="List of spaces"
    )
    total: int | None = Field(None, description="Total count of spaces")


class ClickUpCommentData(BaseModel):
    """A ClickUp task comment."""

    id: str = Field(..., description="Comment ID")
    comment_text: str = Field(..., description="Comment text content")
    user: str | None = Field(None, description="Commenter display name")
    date: str | None = Field(None, description="Comment timestamp (Unix ms)")


class ClickUpCommentListData(BaseModel):
    """A list of ClickUp task comments."""

    comments: list[ClickUpCommentData] = Field(
        default_factory=list, description="List of comments"
    )
    total: int | None = Field(None, description="Total count of comments")


# =============================================================================
# Todoist-Specific Schemas
# =============================================================================


class TodoistTaskData(BaseModel):
    """A Todoist task."""

    id: str = Field(..., description="Todoist task ID")
    content: str = Field(..., description="Task content")
    description: str | None = Field(None, description="Task description")
    project_id: str | None = Field(None, description="Project ID")
    section_id: str | None = Field(None, description="Section ID")
    priority: int | None = Field(
        None, description="Priority level (1=normal, 4=urgent)"
    )
    url: str | None = Field(None, description="Task URL")
    due: str | None = Field(None, description="Due date string")
    is_completed: bool = Field(False, description="Whether the task is completed")
    labels: list[str] = Field(default_factory=list, description="Task label names")


class TodoistTaskListData(BaseModel):
    """A list of Todoist tasks."""

    tasks: list[TodoistTaskData] = Field(
        default_factory=list, description="List of tasks"
    )
    total: int | None = Field(None, description="Total count of tasks")


class TodoistProjectData(BaseModel):
    """A Todoist project."""

    id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    color: str | None = Field(None, description="Project color name")
    is_favorite: bool = Field(False, description="Whether the project is a favorite")
    url: str | None = Field(None, description="Project URL")


class TodoistProjectListData(BaseModel):
    """A list of Todoist projects."""

    projects: list[TodoistProjectData] = Field(
        default_factory=list, description="List of projects"
    )
    total: int | None = Field(None, description="Total count of projects")


class TodoistCommentData(BaseModel):
    """A Todoist comment."""

    id: str = Field(..., description="Comment ID")
    content: str = Field(..., description="Comment content")
    task_id: str | None = Field(None, description="Task ID the comment belongs to")
    posted_at: str | None = Field(None, description="Creation timestamp")


class TodoistCommentListData(BaseModel):
    """A list of Todoist comments."""

    comments: list[TodoistCommentData] = Field(
        default_factory=list, description="List of comments"
    )
    total: int | None = Field(None, description="Total count of comments")


# =============================================================================
# Trello-Specific Schemas
# =============================================================================


class TrelloCardData(BaseModel):
    """A Trello card."""

    id: str = Field(..., description="Trello card ID")
    name: str = Field(..., description="Card name")
    description: str | None = Field(None, description="Card description")
    url: str | None = Field(None, description="Card URL")
    list_name: str | None = Field(None, description="List name the card belongs to")
    labels: list[str] = Field(
        default_factory=list, description="Label names on the card"
    )
    due: str | None = Field(None, description="Due date (ISO 8601)")
    closed: bool = Field(False, description="Whether the card is archived")


class TrelloCardListData(BaseModel):
    """A list of Trello cards."""

    cards: list[TrelloCardData] = Field(
        default_factory=list, description="List of cards"
    )
    total: int | None = Field(None, description="Total number of cards")


class TrelloBoardData(BaseModel):
    """A Trello board."""

    id: str = Field(..., description="Board ID")
    name: str = Field(..., description="Board name")
    description: str | None = Field(None, description="Board description")
    url: str | None = Field(None, description="Board URL")
    closed: bool = Field(False, description="Whether the board is closed")


class TrelloBoardListData(BaseModel):
    """A list of Trello boards."""

    boards: list[TrelloBoardData] = Field(
        default_factory=list, description="List of boards"
    )
    total: int | None = Field(None, description="Total number of boards")


class TrelloListData(BaseModel):
    """A Trello list within a board."""

    id: str = Field(..., description="List ID")
    name: str = Field(..., description="List name")
    closed: bool = Field(False, description="Whether the list is archived")


class TrelloListListData(BaseModel):
    """A list of Trello lists."""

    lists: list[TrelloListData] = Field(
        default_factory=list, description="List of Trello lists"
    )
    total: int | None = Field(None, description="Total number of lists")


# =============================================================================
# Confluence-Specific Schemas
# =============================================================================


class ConfluencePageData(BaseModel):
    """A Confluence page."""

    id: str = Field(..., description="Page ID")
    title: str = Field(..., description="Page title")
    space_key: str | None = Field(None, description="Space key")
    body: str | None = Field(
        None, description="Page body content (storage format HTML)"
    )
    version: int | None = Field(None, description="Current version number")
    url: str | None = Field(None, description="Page URL")


class ConfluencePageListData(BaseModel):
    """A list of Confluence pages."""

    pages: list[ConfluencePageData] = Field(
        default_factory=list, description="List of pages"
    )
    total: int | None = Field(None, description="Total number of pages")


class ConfluenceSpaceData(BaseModel):
    """A Confluence space."""

    key: str = Field(..., description="Space key")
    name: str = Field(..., description="Space name")
    space_type: str | None = Field(None, description="Space type (global or personal)")
    url: str | None = Field(None, description="Space URL")


class ConfluenceSpaceListData(BaseModel):
    """A list of Confluence spaces."""

    spaces: list[ConfluenceSpaceData] = Field(
        default_factory=list, description="List of spaces"
    )
    total: int | None = Field(None, description="Total number of spaces")


class ConfluenceCommentData(BaseModel):
    """A Confluence page comment."""

    id: str = Field(..., description="Comment ID")
    body: str = Field(..., description="Comment body content")
    author: str | None = Field(None, description="Author display name")
    created: str | None = Field(None, description="Creation timestamp")


class ConfluenceCommentListData(BaseModel):
    """A list of Confluence comments."""

    comments: list[ConfluenceCommentData] = Field(
        default_factory=list, description="List of comments"
    )
    total: int | None = Field(None, description="Total number of comments")


# =============================================================================
# Notion-Specific Schemas
# =============================================================================


class NotionPageData(BaseModel):
    """A Notion page."""

    id: str = Field(..., description="Page ID")
    title: str = Field(..., description="Page title")
    url: str | None = Field(None, description="Page URL")
    parent_id: str | None = Field(None, description="Parent page or database ID")
    created_time: str | None = Field(None, description="Creation timestamp (ISO 8601)")
    last_edited_time: str | None = Field(
        None, description="Last edit timestamp (ISO 8601)"
    )


class NotionPageListData(BaseModel):
    """A list of Notion pages."""

    pages: list[NotionPageData] = Field(
        default_factory=list, description="List of pages"
    )
    total: int | None = Field(None, description="Total number of pages")
    has_more: bool = Field(False, description="Whether more results are available")
    next_cursor: str | None = Field(None, description="Cursor for next page of results")


class NotionDatabaseQueryData(BaseModel):
    """Results from a Notion database query."""

    pages: list[NotionPageData] = Field(
        default_factory=list, description="Pages matching the query"
    )
    total: int | None = Field(None, description="Number of results returned")
    has_more: bool = Field(False, description="Whether more results are available")
    next_cursor: str | None = Field(None, description="Cursor for next page of results")


class NotionBlockData(BaseModel):
    """A Notion block."""

    id: str = Field(..., description="Block ID")
    block_type: str = Field(..., description="Block type (paragraph, heading_1, etc.)")
    content: str | None = Field(None, description="Text content of the block")
    has_children: bool = Field(False, description="Whether the block has child blocks")


class NotionBlockListData(BaseModel):
    """A list of Notion blocks."""

    blocks: list[NotionBlockData] = Field(
        default_factory=list, description="List of blocks"
    )
    total: int | None = Field(None, description="Number of blocks returned")
    has_more: bool = Field(False, description="Whether more results are available")
    next_cursor: str | None = Field(None, description="Cursor for next page of results")


# =============================================================================
# Bitbucket-Specific Schemas
# =============================================================================


class BitbucketRepoData(BaseModel):
    """A Bitbucket repository."""

    slug: str = Field(..., description="Repository slug")
    name: str = Field(..., description="Repository name")
    full_name: str | None = Field(None, description="Full name (workspace/repo)")
    description: str | None = Field(None, description="Repository description")
    is_private: bool = Field(False, description="Whether the repository is private")
    language: str | None = Field(None, description="Primary programming language")
    url: str | None = Field(None, description="Repository URL")


class BitbucketRepoListData(BaseModel):
    """A list of Bitbucket repositories."""

    repos: list[BitbucketRepoData] = Field(
        default_factory=list, description="List of repositories"
    )
    total: int | None = Field(None, description="Total number of repositories")


class BitbucketPullRequestData(BaseModel):
    """A Bitbucket pull request."""

    id: int = Field(..., description="Pull request ID")
    title: str = Field(..., description="Pull request title")
    description: str | None = Field(None, description="Pull request description")
    state: str | None = Field(
        None, description="Pull request state (OPEN, MERGED, DECLINED, SUPERSEDED)"
    )
    author: str | None = Field(None, description="Author display name")
    source_branch: str | None = Field(None, description="Source branch name")
    dest_branch: str | None = Field(None, description="Destination branch name")
    url: str | None = Field(None, description="Pull request URL")
    created_on: str | None = Field(None, description="Creation timestamp")


class BitbucketPullRequestListData(BaseModel):
    """A list of Bitbucket pull requests."""

    pull_requests: list[BitbucketPullRequestData] = Field(
        default_factory=list, description="List of pull requests"
    )
    total: int | None = Field(None, description="Total number of pull requests")


class BitbucketCommitData(BaseModel):
    """A Bitbucket commit."""

    hash: str = Field(..., description="Full commit hash")
    message: str = Field(..., description="Commit message")
    author: str | None = Field(None, description="Author display name")
    date: str | None = Field(None, description="Commit date (ISO 8601)")
    url: str | None = Field(None, description="Commit URL")


class BitbucketCommitListData(BaseModel):
    """A list of Bitbucket commits."""

    commits: list[BitbucketCommitData] = Field(
        default_factory=list, description="List of commits"
    )
    total: int | None = Field(None, description="Total number of commits")


# =============================================================================
# GitHub-Specific Schemas
# =============================================================================


class GitHubRepoData(BaseModel):
    """A GitHub repository."""

    name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="Full name (owner/repo)")
    description: str | None = Field(None, description="Repository description")
    url: str | None = Field(None, description="Repository URL")
    stars: int | None = Field(None, description="Star count")
    forks: int | None = Field(None, description="Fork count")
    language: str | None = Field(None, description="Primary language")
    is_private: bool = Field(False, description="Whether the repository is private")
    default_branch: str | None = Field(None, description="Default branch name")
    open_issues_count: int | None = Field(None, description="Number of open issues")


class GitHubIssueData(BaseModel):
    """A GitHub issue."""

    number: int = Field(..., description="Issue number")
    title: str = Field(..., description="Issue title")
    body: str | None = Field(None, description="Issue body (Markdown)")
    state: str | None = Field(None, description="Issue state (open/closed)")
    assignee: str | None = Field(None, description="Assignee login")
    url: str | None = Field(None, description="Issue HTML URL")
    labels: list[str] = Field(default_factory=list, description="Issue label names")
    created_at: str | None = Field(None, description="Creation timestamp (ISO 8601)")
    updated_at: str | None = Field(None, description="Last update timestamp (ISO 8601)")


class GitHubIssueListData(BaseModel):
    """A list of GitHub issues."""

    issues: list[GitHubIssueData] = Field(
        default_factory=list, description="List of issues"
    )
    total: int | None = Field(None, description="Total number of issues")


class GitHubPullRequestData(BaseModel):
    """A GitHub pull request."""

    number: int = Field(..., description="Pull request number")
    title: str = Field(..., description="Pull request title")
    body: str | None = Field(None, description="Pull request body (Markdown)")
    state: str | None = Field(None, description="PR state (open/closed)")
    merged: bool = Field(False, description="Whether the PR has been merged")
    head_branch: str | None = Field(None, description="Head branch name")
    base_branch: str | None = Field(None, description="Base branch name")
    user: str | None = Field(None, description="Author login")
    url: str | None = Field(None, description="Pull request HTML URL")
    created_at: str | None = Field(None, description="Creation timestamp (ISO 8601)")


class GitHubPullRequestListData(BaseModel):
    """A list of GitHub pull requests."""

    pull_requests: list[GitHubPullRequestData] = Field(
        default_factory=list, description="List of pull requests"
    )
    total: int | None = Field(None, description="Total number of pull requests")


class GitHubCommitData(BaseModel):
    """A GitHub commit."""

    sha: str = Field(..., description="Commit SHA")
    message: str = Field(..., description="Commit message")
    author: str | None = Field(None, description="Author login or name")
    date: str | None = Field(None, description="Commit date (ISO 8601)")
    url: str | None = Field(None, description="Commit HTML URL")


class GitHubCommitListData(BaseModel):
    """A list of GitHub commits."""

    commits: list[GitHubCommitData] = Field(
        default_factory=list, description="List of commits"
    )
    total: int | None = Field(None, description="Total number of commits")


class GitHubReleaseData(BaseModel):
    """A GitHub release."""

    id: int = Field(..., description="Release ID")
    tag_name: str = Field(..., description="Git tag name")
    name: str | None = Field(None, description="Release name")
    body: str | None = Field(None, description="Release body (Markdown)")
    draft: bool = Field(False, description="Whether this is a draft release")
    prerelease: bool = Field(False, description="Whether this is a pre-release")
    published_at: str | None = Field(
        None, description="Publication timestamp (ISO 8601)"
    )
    url: str | None = Field(None, description="Release HTML URL")


class GitHubReleaseListData(BaseModel):
    """A list of GitHub releases."""

    releases: list[GitHubReleaseData] = Field(
        default_factory=list, description="List of releases"
    )
    total: int | None = Field(None, description="Total number of releases")


# =============================================================================
# Zendesk-Specific Schemas
# =============================================================================


class ZendeskTicketData(BaseModel):
    """A Zendesk ticket."""

    id: int = Field(..., description="Ticket ID")
    subject: str = Field(..., description="Ticket subject")
    description: str | None = Field(None, description="Ticket description")
    status: str | None = Field(
        None, description="Ticket status (new, open, pending, hold, solved, closed)"
    )
    priority: str | None = Field(
        None, description="Ticket priority (urgent, high, normal, low)"
    )
    ticket_type: str | None = Field(
        None, description="Ticket type (problem, incident, question, task)"
    )
    assignee_id: int | None = Field(None, description="Assignee user ID")
    requester_id: int | None = Field(None, description="Requester user ID")
    tags: list[str] = Field(default_factory=list, description="Ticket tags")
    url: str | None = Field(None, description="Ticket URL in agent interface")


class ZendeskTicketListData(BaseModel):
    """A list of Zendesk tickets."""

    tickets: list[ZendeskTicketData] = Field(
        default_factory=list, description="List of tickets"
    )
    total: int | None = Field(None, description="Total number of tickets")


class ZendeskCommentData(BaseModel):
    """A Zendesk ticket comment."""

    id: int = Field(..., description="Comment ID")
    body: str = Field(..., description="Comment body text")
    author_id: int | None = Field(None, description="Author user ID")
    public: bool = Field(True, description="Whether the comment is public")
    created_at: str | None = Field(None, description="Creation timestamp (ISO 8601)")


class ZendeskCommentListData(BaseModel):
    """A list of Zendesk ticket comments."""

    comments: list[ZendeskCommentData] = Field(
        default_factory=list, description="List of comments"
    )
    total: int | None = Field(None, description="Total number of comments")


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class IssueResponse(ToolResponse[IssueData]):
    """Generic issue response."""

    pass


class IssueListResponse(ToolResponse[IssueListData]):
    """Generic issue list response."""

    pass


# --- Jira ---


class JiraIssueResponse(ToolResponse[JiraIssueData]):
    """Response for Jira issue operations."""

    pass


class JiraIssueListResponse(ToolResponse[JiraIssueListData]):
    """Response for Jira issue search."""

    pass


class JiraProjectListResponse(ToolResponse[JiraProjectListData]):
    """Response for Jira project list."""

    pass


class JiraTransitionResponse(ToolResponse[JiraTransitionData]):
    """Response for Jira issue transition."""

    pass


class JiraTransitionListResponse(ToolResponse[JiraTransitionListData]):
    """Response for listing available Jira transitions."""

    pass


class JiraCommentResponse(ToolResponse[JiraCommentData]):
    """Response for Jira comment operations."""

    pass


# --- Linear ---


class LinearIssueResponse(ToolResponse[LinearIssueData]):
    """Response for Linear issue operations."""

    pass


class LinearIssueListResponse(ToolResponse[LinearIssueListData]):
    """Response for Linear issue list."""

    pass


class LinearTeamListResponse(ToolResponse[LinearTeamListData]):
    """Response for Linear team list."""

    pass


class LinearCycleListResponse(ToolResponse[LinearCycleListData]):
    """Response for Linear cycle list."""

    pass


# --- ClickUp ---


class ClickUpTaskResponse(ToolResponse[ClickUpTaskData]):
    """Response for ClickUp task operations."""

    pass


class ClickUpTaskListResponse(ToolResponse[ClickUpTaskListData]):
    """Response for ClickUp task list."""

    pass


class ClickUpSpaceListResponse(ToolResponse[ClickUpSpaceListData]):
    """Response for ClickUp space list."""

    pass


class ClickUpCommentListResponse(ToolResponse[ClickUpCommentListData]):
    """Response for ClickUp comment list."""

    pass


# --- Todoist ---


class TodoistTaskResponse(ToolResponse[TodoistTaskData]):
    """Response for Todoist task operations."""

    pass


class TodoistTaskListResponse(ToolResponse[TodoistTaskListData]):
    """Response for Todoist task list."""

    pass


class TodoistProjectListResponse(ToolResponse[TodoistProjectListData]):
    """Response for Todoist project list."""

    pass


class TodoistCommentResponse(ToolResponse[TodoistCommentData]):
    """Response for Todoist comment operations."""

    pass


class TodoistCommentListResponse(ToolResponse[TodoistCommentListData]):
    """Response for Todoist comment list."""

    pass


# --- Trello ---


class TrelloCardResponse(ToolResponse[TrelloCardData]):
    """Response for Trello card operations."""

    pass


class TrelloCardListResponse(ToolResponse[TrelloCardListData]):
    """Response for Trello card list."""

    pass


class TrelloBoardListResponse(ToolResponse[TrelloBoardListData]):
    """Response for Trello board list."""

    pass


class TrelloListListResponse(ToolResponse[TrelloListListData]):
    """Response for Trello list listing."""

    pass


# --- Confluence ---


class ConfluencePageResponse(ToolResponse[ConfluencePageData]):
    """Response for Confluence page operations."""

    pass


class ConfluencePageListResponse(ToolResponse[ConfluencePageListData]):
    """Response for Confluence page search."""

    pass


class ConfluenceSpaceListResponse(ToolResponse[ConfluenceSpaceListData]):
    """Response for Confluence space list."""

    pass


class ConfluenceCommentResponse(ToolResponse[ConfluenceCommentData]):
    """Response for Confluence comment operations."""

    pass


class ConfluenceCommentListResponse(ToolResponse[ConfluenceCommentListData]):
    """Response for Confluence comment list."""

    pass


# --- Notion ---


class NotionPageResponse(ToolResponse[NotionPageData]):
    """Response for Notion page operations."""

    pass


class NotionPageListResponse(ToolResponse[NotionPageListData]):
    """Response for Notion page search."""

    pass


class NotionDatabaseQueryResponse(ToolResponse[NotionDatabaseQueryData]):
    """Response for Notion database query."""

    pass


class NotionBlockListResponse(ToolResponse[NotionBlockListData]):
    """Response for Notion block list."""

    pass


# --- Bitbucket ---


class BitbucketRepoResponse(ToolResponse[BitbucketRepoData]):
    """Response for Bitbucket repository operations."""

    pass


class BitbucketRepoListResponse(ToolResponse[BitbucketRepoListData]):
    """Response for Bitbucket repository list."""

    pass


class BitbucketPullRequestResponse(ToolResponse[BitbucketPullRequestData]):
    """Response for Bitbucket pull request operations."""

    pass


class BitbucketPullRequestListResponse(ToolResponse[BitbucketPullRequestListData]):
    """Response for Bitbucket pull request list."""

    pass


class BitbucketCommitListResponse(ToolResponse[BitbucketCommitListData]):
    """Response for Bitbucket commit list."""

    pass


# --- GitHub ---


class GitHubRepoResponse(ToolResponse[GitHubRepoData]):
    """Response for GitHub repository operations."""

    pass


class GitHubIssueResponse(ToolResponse[GitHubIssueData]):
    """Response for GitHub issue operations."""

    pass


class GitHubIssueListResponse(ToolResponse[GitHubIssueListData]):
    """Response for GitHub issue list."""

    pass


class GitHubPullRequestResponse(ToolResponse[GitHubPullRequestData]):
    """Response for GitHub pull request operations."""

    pass


class GitHubPullRequestListResponse(ToolResponse[GitHubPullRequestListData]):
    """Response for GitHub pull request list."""

    pass


class GitHubCommitListResponse(ToolResponse[GitHubCommitListData]):
    """Response for GitHub commit list."""

    pass


class GitHubReleaseListResponse(ToolResponse[GitHubReleaseListData]):
    """Response for GitHub release list."""

    pass


# --- Zendesk ---


class ZendeskTicketResponse(ToolResponse[ZendeskTicketData]):
    """Response for Zendesk ticket operations."""

    pass


class ZendeskTicketListResponse(ToolResponse[ZendeskTicketListData]):
    """Response for Zendesk ticket search."""

    pass


class ZendeskCommentListResponse(ToolResponse[ZendeskCommentListData]):
    """Response for Zendesk comment list."""

    pass
