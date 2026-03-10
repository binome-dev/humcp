"""Pydantic output schemas for cloud tools."""

from typing import Any

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# AWS Lambda Schemas
# =============================================================================


class LambdaFunctionSummary(BaseModel):
    """Summary of an AWS Lambda function."""

    function_name: str = Field(..., description="Name of the Lambda function")
    function_arn: str | None = Field(None, description="ARN of the Lambda function")
    runtime: str | None = Field(
        None, description="Runtime environment (e.g. python3.13, nodejs20.x)"
    )
    handler: str | None = Field(
        None, description="Function entry point (e.g. index.handler)"
    )
    last_modified: str | None = Field(
        None, description="Last modified timestamp in ISO 8601 format"
    )
    memory_size: int | None = Field(None, description="Memory allocated in MB")
    timeout: int | None = Field(None, description="Execution timeout in seconds")
    code_size: int | None = Field(
        None, description="Size of the deployment package in bytes"
    )
    description: str | None = Field(None, description="Function description")


class LambdaListFunctionsData(BaseModel):
    """Output data for aws_lambda_list_functions tool."""

    functions: list[LambdaFunctionSummary] = Field(
        default_factory=list, description="List of Lambda functions"
    )
    count: int = Field(..., description="Total number of functions returned")


class LambdaInvokeData(BaseModel):
    """Output data for aws_lambda_invoke tool."""

    function_name: str = Field(..., description="Name of the invoked function")
    status_code: int = Field(..., description="HTTP status code of the invocation")
    payload: str = Field(..., description="Response payload from the function")
    executed_version: str | None = Field(
        default=None, description="Version or alias of the executed function"
    )
    function_error: str | None = Field(
        default=None,
        description="Error type if the function returned an error (Handled or Unhandled)",
    )
    log_result: str | None = Field(
        default=None,
        description="Last 4KB of base64-encoded execution log (when LogType=Tail)",
    )


class LambdaGetFunctionData(BaseModel):
    """Output data for aws_lambda_get_function tool."""

    function_name: str = Field(..., description="Name of the Lambda function")
    function_arn: str = Field(..., description="ARN of the Lambda function")
    runtime: str | None = Field(None, description="Runtime environment")
    handler: str | None = Field(None, description="Function entry point")
    role: str | None = Field(None, description="Execution role ARN")
    code_size: int | None = Field(
        None, description="Size of the deployment package in bytes"
    )
    description: str | None = Field(None, description="Function description")
    timeout: int | None = Field(None, description="Execution timeout in seconds")
    memory_size: int | None = Field(None, description="Memory allocated in MB")
    last_modified: str | None = Field(None, description="Last modified timestamp")
    state: str | None = Field(
        None,
        description="Current state of the function (Active, Pending, Inactive, Failed)",
    )
    last_update_status: str | None = Field(
        None, description="Status of the last update (Successful, Failed, InProgress)"
    )
    environment_variables: dict[str, str] | None = Field(
        None, description="Environment variables configured for the function"
    )
    layers: list[str] | None = Field(
        None, description="List of layer ARNs attached to the function"
    )


class LambdaUpdateCodeData(BaseModel):
    """Output data for aws_lambda_update_function_code tool."""

    function_name: str = Field(..., description="Name of the updated function")
    function_arn: str = Field(..., description="ARN of the updated function")
    runtime: str | None = Field(None, description="Runtime environment")
    code_size: int | None = Field(
        None, description="Size of the new deployment package in bytes"
    )
    last_modified: str | None = Field(None, description="Last modified timestamp")
    last_update_status: str | None = Field(
        None, description="Status of the update (Successful, Failed, InProgress)"
    )


class LambdaAliasInfo(BaseModel):
    """Information about an AWS Lambda function alias."""

    alias_arn: str = Field(..., description="ARN of the alias")
    name: str = Field(..., description="Alias name")
    function_version: str = Field(
        ..., description="Function version the alias points to"
    )
    description: str | None = Field(None, description="Alias description")
    routing_config: dict[str, float] | None = Field(
        None, description="Traffic-shifting routing configuration (version weights)"
    )


class LambdaListAliasesData(BaseModel):
    """Output data for aws_lambda_list_aliases tool."""

    function_name: str = Field(..., description="Name of the Lambda function")
    aliases: list[LambdaAliasInfo] = Field(
        default_factory=list, description="List of aliases"
    )
    count: int = Field(..., description="Total number of aliases returned")


class LambdaEventSourceMapping(BaseModel):
    """An event source mapping for a Lambda function."""

    uuid: str = Field(..., description="Unique identifier of the event source mapping")
    function_arn: str | None = Field(None, description="ARN of the Lambda function")
    event_source_arn: str | None = Field(None, description="ARN of the event source")
    state: str | None = Field(
        None, description="Current state (Enabled, Disabled, Creating, etc.)"
    )
    batch_size: int | None = Field(
        None, description="Maximum number of records per batch"
    )
    last_modified: str | None = Field(None, description="Last modified timestamp")


class LambdaListEventSourceMappingsData(BaseModel):
    """Output data for aws_lambda_list_event_source_mappings tool."""

    event_source_mappings: list[LambdaEventSourceMapping] = Field(
        default_factory=list, description="List of event source mappings"
    )
    count: int = Field(..., description="Total number of mappings returned")


# =============================================================================
# AWS SES Schemas
# =============================================================================


class SesSendEmailData(BaseModel):
    """Output data for aws_ses_send_email tool."""

    message_id: str = Field(..., description="SES message ID")
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")


class SesIdentityInfo(BaseModel):
    """Information about an SES verified identity."""

    identity: str = Field(..., description="Email address or domain")
    identity_type: str | None = Field(
        None, description="Type of identity (EmailAddress or Domain)"
    )


class SesListIdentitiesData(BaseModel):
    """Output data for aws_ses_list_identities tool."""

    identities: list[SesIdentityInfo] = Field(
        default_factory=list, description="List of verified identities"
    )
    count: int = Field(..., description="Total number of identities returned")


class SesSendStatisticsEntry(BaseModel):
    """A single send statistics data point."""

    timestamp: str | None = Field(None, description="Timestamp of the data point")
    delivery_attempts: int = Field(0, description="Number of delivery attempts")
    bounces: int = Field(0, description="Number of bounces")
    complaints: int = Field(0, description="Number of complaints")
    rejects: int = Field(0, description="Number of rejects")


class SesSendStatisticsData(BaseModel):
    """Output data for aws_ses_get_send_statistics tool."""

    statistics: list[SesSendStatisticsEntry] = Field(
        default_factory=list, description="Send statistics data points"
    )
    count: int = Field(..., description="Number of data points returned")


class SesSendTemplatedEmailData(BaseModel):
    """Output data for aws_ses_send_templated_email tool."""

    message_id: str = Field(..., description="SES message ID")
    to: str = Field(..., description="Recipient email address")
    template_name: str = Field(..., description="Name of the SES template used")


class SesVerifyEmailData(BaseModel):
    """Output data for aws_ses_verify_email tool."""

    email: str = Field(..., description="Email address that verification was sent to")
    message: str = Field(..., description="Confirmation message")


# =============================================================================
# Docker Schemas
# =============================================================================


class DockerContainerInfo(BaseModel):
    """Information about a Docker container."""

    id: str = Field(..., description="Container ID")
    name: str = Field(..., description="Container name")
    image: str = Field(..., description="Image used by the container")
    status: str = Field(
        ..., description="Current container status (e.g. running, exited)"
    )
    created: str | None = Field(None, description="Creation timestamp")
    ports: dict[str, Any] | None = Field(None, description="Port mappings")


class DockerListContainersData(BaseModel):
    """Output data for docker_list_containers tool."""

    containers: list[DockerContainerInfo] = Field(
        default_factory=list, description="List of containers"
    )
    count: int = Field(..., description="Total number of containers returned")


class DockerRunContainerData(BaseModel):
    """Output data for docker_run_container tool."""

    container_id: str = Field(..., description="ID of the started container")
    image: str = Field(..., description="Image used")


class DockerStopContainerData(BaseModel):
    """Output data for docker_stop_container tool."""

    container_id: str = Field(..., description="ID of the stopped container")
    message: str = Field(..., description="Status message")


class DockerContainerLogsData(BaseModel):
    """Output data for docker_get_container_logs tool."""

    container_id: str = Field(..., description="Container ID")
    logs: str = Field(..., description="Container log output")
    tail: int | None = Field(None, description="Number of tail lines requested")


class DockerRemoveContainerData(BaseModel):
    """Output data for docker_remove_container tool."""

    container_id: str = Field(..., description="ID of the removed container")
    message: str = Field(..., description="Status message")


class DockerInspectContainerData(BaseModel):
    """Output data for docker_inspect_container tool."""

    id: str = Field(..., description="Container ID")
    name: str = Field(..., description="Container name")
    image: str = Field(..., description="Image used by the container")
    status: str = Field(..., description="Current container status")
    created: str | None = Field(None, description="Creation timestamp")
    started_at: str | None = Field(None, description="Container start timestamp")
    finished_at: str | None = Field(None, description="Container stop timestamp")
    platform: str | None = Field(None, description="Platform (e.g. linux/amd64)")
    restart_count: int | None = Field(
        None, description="Number of times the container has restarted"
    )
    ports: dict[str, Any] | None = Field(None, description="Port mappings")
    environment: list[str] | None = Field(
        None, description="Environment variables (KEY=VALUE)"
    )
    mounts: list[dict[str, Any]] | None = Field(None, description="Volume mounts")
    network_mode: str | None = Field(
        None, description="Network mode (bridge, host, etc.)"
    )
    ip_address: str | None = Field(None, description="Container IP address")


class DockerImageInfo(BaseModel):
    """Information about a Docker image."""

    id: str = Field(..., description="Image ID")
    tags: list[str] = Field(default_factory=list, description="Image tags")
    size: int | None = Field(None, description="Image size in bytes")
    created: str | None = Field(None, description="Creation timestamp")


class DockerListImagesData(BaseModel):
    """Output data for docker_list_images tool."""

    images: list[DockerImageInfo] = Field(
        default_factory=list, description="List of Docker images"
    )
    count: int = Field(..., description="Total number of images returned")


# =============================================================================
# Daytona Schemas
# =============================================================================


class DaytonaWorkspaceInfo(BaseModel):
    """Information about a Daytona workspace."""

    id: str = Field(..., description="Workspace ID")
    name: str | None = Field(None, description="Workspace name")
    state: str | None = Field(None, description="Current workspace state")
    repo_url: str | None = Field(None, description="Repository URL")


class DaytonaListWorkspacesData(BaseModel):
    """Output data for daytona_list_workspaces tool."""

    workspaces: list[DaytonaWorkspaceInfo] = Field(
        default_factory=list, description="List of workspaces"
    )
    count: int = Field(..., description="Total number of workspaces returned")


class DaytonaCreateWorkspaceData(BaseModel):
    """Output data for daytona_create_workspace tool."""

    workspace_id: str = Field(..., description="ID of the created workspace")
    repo_url: str = Field(..., description="Repository URL used")


class DaytonaRunCommandData(BaseModel):
    """Output data for daytona_run_command tool."""

    workspace_id: str = Field(..., description="Workspace ID")
    output: str = Field(..., description="Command output")
    exit_code: int | None = Field(None, description="Exit code of the command")


class DaytonaStartStopWorkspaceData(BaseModel):
    """Output data for daytona_start_workspace and daytona_stop_workspace tools."""

    workspace_id: str = Field(..., description="Workspace ID")
    message: str = Field(..., description="Status message")


class DaytonaDeleteWorkspaceData(BaseModel):
    """Output data for daytona_delete_workspace tool."""

    workspace_id: str = Field(..., description="ID of the deleted workspace")
    message: str = Field(..., description="Confirmation message")


# =============================================================================
# E2B Schemas
# =============================================================================


class E2BRunCodeData(BaseModel):
    """Output data for e2b_run_code tool."""

    output: str = Field(..., description="Code execution output")
    language: str = Field(..., description="Programming language used")
    error: str | None = Field(None, description="Error message if execution failed")


class E2BRunCommandData(BaseModel):
    """Output data for e2b_run_command tool."""

    stdout: str = Field("", description="Standard output")
    stderr: str = Field("", description="Standard error")
    exit_code: int | None = Field(None, description="Exit code of the command")


class E2BUploadFileData(BaseModel):
    """Output data for e2b_upload_file tool."""

    path: str = Field(..., description="Path of the uploaded file in the sandbox")
    message: str = Field(..., description="Status message")


class E2BDownloadFileData(BaseModel):
    """Output data for e2b_download_file tool."""

    path: str = Field(..., description="Path of the downloaded file in the sandbox")
    content: str = Field(..., description="File content (text files only)")
    size: int | None = Field(None, description="File size in bytes")


class E2BListFilesData(BaseModel):
    """Output data for e2b_list_files tool."""

    path: str = Field(..., description="Directory path listed")
    files: list[str] = Field(
        default_factory=list, description="List of file/directory names"
    )
    count: int = Field(..., description="Number of entries returned")


# =============================================================================
# Airflow Schemas
# =============================================================================


class AirflowDagInfo(BaseModel):
    """Information about an Airflow DAG."""

    dag_id: str = Field(..., description="DAG identifier")
    description: str | None = Field(None, description="DAG description")
    is_paused: bool | None = Field(None, description="Whether the DAG is paused")
    is_active: bool | None = Field(None, description="Whether the DAG is active")
    file_token: str | None = Field(None, description="File token for the DAG file")
    owners: list[str] | None = Field(None, description="List of DAG owners")
    schedule_interval: str | None = Field(
        None, description="Schedule interval expression (e.g. '@daily', '0 * * * *')"
    )
    tags: list[str] | None = Field(None, description="DAG tags")


class AirflowListDagsData(BaseModel):
    """Output data for airflow_list_dags tool."""

    dags: list[AirflowDagInfo] = Field(default_factory=list, description="List of DAGs")
    count: int = Field(..., description="Total number of DAGs returned")


class AirflowTriggerDagData(BaseModel):
    """Output data for airflow_trigger_dag tool."""

    dag_id: str = Field(..., description="DAG identifier")
    dag_run_id: str = Field(..., description="DAG run identifier")
    state: str | None = Field(None, description="Initial state of the DAG run")
    execution_date: str | None = Field(None, description="Logical date of the DAG run")


class AirflowDagRunData(BaseModel):
    """Output data for airflow_get_dag_run tool."""

    dag_id: str = Field(..., description="DAG identifier")
    dag_run_id: str = Field(..., description="DAG run identifier")
    state: str = Field(
        ..., description="Current state of the DAG run (running, success, failed)"
    )
    execution_date: str | None = Field(None, description="Logical date")
    start_date: str | None = Field(None, description="Actual start date")
    end_date: str | None = Field(None, description="Actual end date")


class AirflowTaskInstanceInfo(BaseModel):
    """Information about an Airflow task instance within a DAG run."""

    task_id: str = Field(..., description="Task identifier")
    state: str | None = Field(
        None, description="Task state (success, running, failed, etc.)"
    )
    start_date: str | None = Field(None, description="Task start date")
    end_date: str | None = Field(None, description="Task end date")
    duration: float | None = Field(None, description="Task duration in seconds")
    try_number: int | None = Field(None, description="Current try number")
    operator: str | None = Field(None, description="Operator class name")


class AirflowListTaskInstancesData(BaseModel):
    """Output data for airflow_list_task_instances tool."""

    dag_id: str = Field(..., description="DAG identifier")
    dag_run_id: str = Field(..., description="DAG run identifier")
    task_instances: list[AirflowTaskInstanceInfo] = Field(
        default_factory=list, description="List of task instances"
    )
    count: int = Field(..., description="Total number of task instances returned")


class AirflowPauseDagData(BaseModel):
    """Output data for airflow_pause_dag and airflow_unpause_dag tools."""

    dag_id: str = Field(..., description="DAG identifier")
    is_paused: bool = Field(..., description="Whether the DAG is now paused")


# =============================================================================
# Zoom Schemas
# =============================================================================


class ZoomRecordingFile(BaseModel):
    """A single recording file from a Zoom meeting."""

    id: str | None = Field(None, description="Recording file ID")
    file_type: str | None = Field(
        None, description="File type (MP4, M4A, CHAT, TRANSCRIPT, etc.)"
    )
    file_size: int | None = Field(None, description="File size in bytes")
    download_url: str | None = Field(None, description="URL to download the recording")
    play_url: str | None = Field(None, description="URL to play the recording")
    status: str | None = Field(None, description="Processing status of the recording")
    recording_start: str | None = Field(None, description="Recording start time")
    recording_end: str | None = Field(None, description="Recording end time")


class ZoomRecordingMeeting(BaseModel):
    """A Zoom meeting with its recordings."""

    meeting_id: str = Field(..., description="Meeting ID")
    topic: str | None = Field(None, description="Meeting topic/title")
    start_time: str | None = Field(None, description="Meeting start time")
    duration: int | None = Field(None, description="Meeting duration in minutes")
    total_size: int | None = Field(
        None, description="Total size of all recording files in bytes"
    )
    recording_count: int = Field(0, description="Number of recording files")
    recording_files: list[ZoomRecordingFile] = Field(
        default_factory=list, description="List of recording files"
    )


class ZoomListRecordingsData(BaseModel):
    """Output data for zoom_list_recordings tool."""

    user_id: str = Field(..., description="Zoom user ID or email queried")
    from_date: str | None = Field(None, description="Start date of the query range")
    to_date: str | None = Field(None, description="End date of the query range")
    meetings: list[ZoomRecordingMeeting] = Field(
        default_factory=list, description="List of meetings with recordings"
    )
    total_records: int = Field(
        0, description="Total number of meetings with recordings"
    )


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class LambdaListFunctionsResponse(ToolResponse[LambdaListFunctionsData]):
    """Response schema for aws_lambda_list_functions tool."""

    pass


class LambdaInvokeResponse(ToolResponse[LambdaInvokeData]):
    """Response schema for aws_lambda_invoke tool."""

    pass


class LambdaGetFunctionResponse(ToolResponse[LambdaGetFunctionData]):
    """Response schema for aws_lambda_get_function tool."""

    pass


class LambdaUpdateCodeResponse(ToolResponse[LambdaUpdateCodeData]):
    """Response schema for aws_lambda_update_function_code tool."""

    pass


class LambdaListEventSourceMappingsResponse(
    ToolResponse[LambdaListEventSourceMappingsData]
):
    """Response schema for aws_lambda_list_event_source_mappings tool."""

    pass


class LambdaListAliasesResponse(ToolResponse[LambdaListAliasesData]):
    """Response schema for aws_lambda_list_aliases tool."""

    pass


class SesSendEmailResponse(ToolResponse[SesSendEmailData]):
    """Response schema for aws_ses_send_email tool."""

    pass


class SesListIdentitiesResponse(ToolResponse[SesListIdentitiesData]):
    """Response schema for aws_ses_list_identities tool."""

    pass


class SesSendStatisticsResponse(ToolResponse[SesSendStatisticsData]):
    """Response schema for aws_ses_get_send_statistics tool."""

    pass


class SesSendTemplatedEmailResponse(ToolResponse[SesSendTemplatedEmailData]):
    """Response schema for aws_ses_send_templated_email tool."""

    pass


class SesVerifyEmailResponse(ToolResponse[SesVerifyEmailData]):
    """Response schema for aws_ses_verify_email tool."""

    pass


class DockerListContainersResponse(ToolResponse[DockerListContainersData]):
    """Response schema for docker_list_containers tool."""

    pass


class DockerRunContainerResponse(ToolResponse[DockerRunContainerData]):
    """Response schema for docker_run_container tool."""

    pass


class DockerStopContainerResponse(ToolResponse[DockerStopContainerData]):
    """Response schema for docker_stop_container tool."""

    pass


class DockerContainerLogsResponse(ToolResponse[DockerContainerLogsData]):
    """Response schema for docker_get_container_logs tool."""

    pass


class DockerRemoveContainerResponse(ToolResponse[DockerRemoveContainerData]):
    """Response schema for docker_remove_container tool."""

    pass


class DockerInspectContainerResponse(ToolResponse[DockerInspectContainerData]):
    """Response schema for docker_inspect_container tool."""

    pass


class DockerListImagesResponse(ToolResponse[DockerListImagesData]):
    """Response schema for docker_list_images tool."""

    pass


class DaytonaListWorkspacesResponse(ToolResponse[DaytonaListWorkspacesData]):
    """Response schema for daytona_list_workspaces tool."""

    pass


class DaytonaCreateWorkspaceResponse(ToolResponse[DaytonaCreateWorkspaceData]):
    """Response schema for daytona_create_workspace tool."""

    pass


class DaytonaRunCommandResponse(ToolResponse[DaytonaRunCommandData]):
    """Response schema for daytona_run_command tool."""

    pass


class DaytonaStartStopWorkspaceResponse(ToolResponse[DaytonaStartStopWorkspaceData]):
    """Response schema for daytona_start_workspace and daytona_stop_workspace tools."""

    pass


class DaytonaDeleteWorkspaceResponse(ToolResponse[DaytonaDeleteWorkspaceData]):
    """Response schema for daytona_delete_workspace tool."""

    pass


class E2BRunCodeResponse(ToolResponse[E2BRunCodeData]):
    """Response schema for e2b_run_code tool."""

    pass


class E2BRunCommandResponse(ToolResponse[E2BRunCommandData]):
    """Response schema for e2b_run_command tool."""

    pass


class E2BUploadFileResponse(ToolResponse[E2BUploadFileData]):
    """Response schema for e2b_upload_file tool."""

    pass


class E2BDownloadFileResponse(ToolResponse[E2BDownloadFileData]):
    """Response schema for e2b_download_file tool."""

    pass


class E2BListFilesResponse(ToolResponse[E2BListFilesData]):
    """Response schema for e2b_list_files tool."""

    pass


class AirflowListDagsResponse(ToolResponse[AirflowListDagsData]):
    """Response schema for airflow_list_dags tool."""

    pass


class AirflowTriggerDagResponse(ToolResponse[AirflowTriggerDagData]):
    """Response schema for airflow_trigger_dag tool."""

    pass


class AirflowDagRunResponse(ToolResponse[AirflowDagRunData]):
    """Response schema for airflow_get_dag_run tool."""

    pass


class AirflowListTaskInstancesResponse(ToolResponse[AirflowListTaskInstancesData]):
    """Response schema for airflow_list_task_instances tool."""

    pass


class AirflowPauseDagResponse(ToolResponse[AirflowPauseDagData]):
    """Response schema for airflow_pause_dag and airflow_unpause_dag tools."""

    pass
