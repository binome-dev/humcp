---
name: project-management
description: Tools for interacting with project management, issue tracking, wiki, and code hosting services. Use when the user needs to create, read, or search issues, tasks, tickets, pages, or repositories across services like Jira, Linear, ClickUp, Todoist, Trello, Confluence, Notion, Bitbucket, GitHub, or Zendesk.
---

# Project Management Tools

Tools for managing issues, tasks, tickets, wiki pages, repositories, and pull requests across popular project management and developer services.

## Supported Services

| Service | Tools | Env Variables |
|---------|-------|---------------|
| Jira | `jira_get_issue`, `jira_create_issue`, `jira_search_issues` | `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN` |
| Linear | `linear_create_issue`, `linear_get_issue`, `linear_list_issues` | `LINEAR_API_KEY` |
| ClickUp | `clickup_create_task`, `clickup_get_task` | `CLICKUP_API_KEY` |
| Todoist | `todoist_create_task`, `todoist_get_tasks` | `TODOIST_API_KEY` |
| Trello | `trello_create_card`, `trello_get_boards` | `TRELLO_API_KEY`, `TRELLO_TOKEN` |
| Confluence | `confluence_get_page`, `confluence_create_page`, `confluence_search` | `CONFLUENCE_URL`, `CONFLUENCE_USERNAME`, `CONFLUENCE_API_TOKEN` |
| Notion | `notion_get_page`, `notion_create_page`, `notion_search` | `NOTION_API_KEY` |
| Bitbucket | `bitbucket_list_repos`, `bitbucket_get_repo`, `bitbucket_create_pr` | `BITBUCKET_USERNAME`, `BITBUCKET_APP_PASSWORD` |
| GitHub | `github_get_repo`, `github_list_issues`, `github_create_issue` | `GITHUB_TOKEN` |
| Zendesk | `zendesk_create_ticket`, `zendesk_get_ticket`, `zendesk_search_tickets` | `ZENDESK_SUBDOMAIN`, `ZENDESK_EMAIL`, `ZENDESK_API_TOKEN` |

## Usage Examples

### Jira - Search Issues

```python
result = await jira_search_issues(
    jql="project = PROJ AND status = 'In Progress'",
    max_results=10
)
```

### Linear - Create Issue

```python
result = await linear_create_issue(
    title="Fix login bug",
    description="Users cannot log in with SSO",
    team_id="team-uuid-here"
)
```

### GitHub - List Issues

```python
result = await github_list_issues(
    owner="myorg",
    repo="myrepo",
    state="open"
)
```

### Zendesk - Create Ticket

```python
result = await zendesk_create_ticket(
    subject="Cannot access dashboard",
    description="User reports 500 error on dashboard page",
    priority="high"
)
```

## Response Format

All tools return a consistent response format:

```json
{
  "success": true,
  "data": {
    "id": "PROJ-123",
    "title": "Issue title",
    "status": "In Progress",
    "url": "https://..."
  }
}
```

On error:

```json
{
  "success": false,
  "error": "Descriptive error message"
}
```

## When to Use

- Creating, retrieving, or searching issues and tasks
- Managing wiki pages and documentation
- Listing repositories and creating pull requests
- Creating and searching support tickets
- Cross-service project management workflows
