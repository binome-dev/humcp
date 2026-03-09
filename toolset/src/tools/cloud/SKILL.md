---
name: cloud-infrastructure
description: Manage cloud infrastructure, serverless functions, containers, and development sandboxes. Use when the user needs to invoke AWS Lambda functions, send emails via SES, manage Docker containers, create Daytona workspaces, run code in E2B sandboxes, or interact with Apache Airflow DAGs.
---

# Cloud Infrastructure Tools

Tools for interacting with cloud services, container runtimes, and development sandboxes.

## Available Tools

| Tool | Service | API Key Required | Best For |
|------|---------|-----------------|----------|
| `aws_lambda_invoke` | AWS Lambda | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Invoking serverless functions |
| `aws_lambda_list_functions` | AWS Lambda | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Listing available Lambda functions |
| `aws_ses_send_email` | AWS SES | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Sending transactional emails |
| `docker_list_containers` | Docker | None (local socket) | Listing Docker containers |
| `docker_run_container` | Docker | None (local socket) | Running a new container |
| `docker_stop_container` | Docker | None (local socket) | Stopping a running container |
| `daytona_create_workspace` | Daytona | `DAYTONA_API_KEY` | Creating cloud dev workspaces |
| `daytona_list_workspaces` | Daytona | `DAYTONA_API_KEY` | Listing Daytona workspaces |
| `daytona_run_command` | Daytona | `DAYTONA_API_KEY` | Executing commands in a workspace |
| `e2b_run_code` | E2B | `E2B_API_KEY` | Running code in a cloud sandbox |
| `e2b_run_command` | E2B | `E2B_API_KEY` | Running shell commands in a sandbox |
| `airflow_list_dags` | Airflow | `AIRFLOW_USERNAME`, `AIRFLOW_PASSWORD` | Listing Airflow DAGs |
| `airflow_trigger_dag` | Airflow | `AIRFLOW_USERNAME`, `AIRFLOW_PASSWORD` | Triggering a DAG run |
| `airflow_get_dag_run` | Airflow | `AIRFLOW_USERNAME`, `AIRFLOW_PASSWORD` | Checking DAG run status |

## Environment Variables

### AWS (Lambda & SES)
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_DEFAULT_REGION` - AWS region (default: `us-east-1`)
- `AWS_SES_FROM_EMAIL` - Default sender email for SES

### Docker
- No API key needed; uses the local Docker socket

### Daytona
- `DAYTONA_API_KEY` - Daytona API key
- `DAYTONA_SERVER_URL` - Daytona server URL (default: `https://api.daytona.io`)

### E2B
- `E2B_API_KEY` - E2B API key

### Airflow
- `AIRFLOW_BASE_URL` - Airflow REST API base URL (default: `http://localhost:8080`)
- `AIRFLOW_USERNAME` - Airflow username
- `AIRFLOW_PASSWORD` - Airflow password

## Quick Examples

### AWS Lambda

```python
# List functions
result = await aws_lambda_list_functions(region="us-west-2")

# Invoke a function
result = await aws_lambda_invoke(
    function_name="my-function",
    payload='{"key": "value"}',
    region="us-east-1"
)
```

### AWS SES

```python
result = await aws_ses_send_email(
    to="recipient@example.com",
    subject="Hello from SES",
    body="This is a test email.",
    from_addr="sender@example.com"
)
```

### Docker

```python
# List running containers
result = await docker_list_containers()

# List all containers (including stopped)
result = await docker_list_containers(all=True)

# Run a container
result = await docker_run_container(
    image="python:3.13-slim",
    command="python -c 'print(\"hello\")'",
    environment={"MY_VAR": "value"}
)

# Stop a container
result = await docker_stop_container(container_id="abc123")
```

### Daytona

```python
# Create a workspace
result = await daytona_create_workspace(
    repo_url="https://github.com/user/repo"
)

# List workspaces
result = await daytona_list_workspaces()

# Run a command
result = await daytona_run_command(
    workspace_id="ws-123",
    command="ls -la"
)
```

### E2B

```python
# Run Python code
result = await e2b_run_code(
    code="print('Hello from E2B!')",
    language="python",
    timeout=60
)

# Run a shell command
result = await e2b_run_command(
    command="pip install requests && python -c 'import requests; print(requests.__version__)'",
    timeout=120
)
```

### Airflow

```python
# List DAGs
result = await airflow_list_dags()

# Trigger a DAG
result = await airflow_trigger_dag(
    dag_id="my_etl_pipeline",
    conf={"param1": "value1"}
)

# Check DAG run status
result = await airflow_get_dag_run(
    dag_id="my_etl_pipeline",
    run_id="manual__2025-01-01T00:00:00+00:00"
)
```

## Response Format

All cloud tools return a consistent response structure:

```json
{
  "success": true,
  "data": {
    "...": "tool-specific fields"
  }
}
```

On failure:

```json
{
  "success": false,
  "error": "Description of what went wrong"
}
```

## When to Use

- **Run serverless functions**: Use `aws_lambda_invoke`
- **Send emails**: Use `aws_ses_send_email`
- **Manage containers**: Use `docker_list_containers`, `docker_run_container`, `docker_stop_container`
- **Cloud dev environments**: Use `daytona_create_workspace`, `daytona_run_command`
- **Execute code safely**: Use `e2b_run_code`, `e2b_run_command`
- **Orchestrate data pipelines**: Use `airflow_trigger_dag`, `airflow_get_dag_run`
