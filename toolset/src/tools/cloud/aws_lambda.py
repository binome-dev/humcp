"""AWS Lambda tools for managing Lambda functions via boto3.

Supports invoking functions, listing functions, retrieving function details,
updating function code, listing event source mappings, and listing aliases.

Environment variables:
    AWS_ACCESS_KEY_ID: AWS access key.
    AWS_SECRET_ACCESS_KEY: AWS secret key.
    AWS_DEFAULT_REGION: Default region (fallback: us-east-1).
"""

from __future__ import annotations

import logging
import os

from src.humcp.decorator import tool
from src.tools.cloud.schemas import (
    LambdaEventSourceMapping,
    LambdaFunctionSummary,
    LambdaGetFunctionData,
    LambdaGetFunctionResponse,
    LambdaInvokeData,
    LambdaInvokeResponse,
    LambdaListEventSourceMappingsData,
    LambdaListEventSourceMappingsResponse,
    LambdaListFunctionsData,
    LambdaListFunctionsResponse,
    LambdaUpdateCodeData,
    LambdaUpdateCodeResponse,
)

try:
    import boto3
except ImportError as err:
    raise ImportError(
        "boto3 is required for AWS Lambda tools. Install with: pip install boto3"
    ) from err

logger = logging.getLogger("humcp.tools.aws_lambda")


def _get_lambda_client(region: str | None = None):
    """Create a boto3 Lambda client with credentials from environment."""
    resolved_region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    return boto3.client("lambda", region_name=resolved_region)


def _check_aws_creds() -> str | None:
    """Return an error message if AWS credentials are missing, else None."""
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    if not aws_key or not aws_secret:
        return "AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
    return None


@tool()
async def aws_lambda_invoke(
    function_name: str,
    payload: str = "{}",
    invocation_type: str = "RequestResponse",
    region: str | None = None,
) -> LambdaInvokeResponse:
    """Invoke an AWS Lambda function with an optional JSON payload.

    Calls the function synchronously (RequestResponse) or asynchronously (Event).
    The response includes the function output, status code, and any error information.

    Args:
        function_name: The name, ARN, or partial ARN of the Lambda function to invoke.
        payload: JSON string payload to send to the function. Defaults to "{}".
        invocation_type: How to invoke the function. One of 'RequestResponse' (synchronous,
            default), 'Event' (asynchronous), or 'DryRun' (validate without executing).
        region: AWS region. Falls back to AWS_DEFAULT_REGION env var or us-east-1.

    Returns:
        Invocation result including status code, response payload, and error info.
    """
    try:
        err = _check_aws_creds()
        if err:
            return LambdaInvokeResponse(success=False, error=err)

        logger.info(
            "Invoking Lambda function=%s type=%s", function_name, invocation_type
        )
        client = _get_lambda_client(region)
        response = client.invoke(
            FunctionName=function_name,
            Payload=payload,
            InvocationType=invocation_type,
        )

        response_payload = response["Payload"].read().decode("utf-8")
        executed_version = response.get("ExecutedVersion")
        function_error = response.get("FunctionError")

        data = LambdaInvokeData(
            function_name=function_name,
            status_code=response["StatusCode"],
            payload=response_payload,
            executed_version=executed_version,
            function_error=function_error,
        )

        logger.info(
            "Lambda invocation complete function=%s status=%d",
            function_name,
            response["StatusCode"],
        )
        return LambdaInvokeResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to invoke Lambda function")
        return LambdaInvokeResponse(
            success=False, error=f"Lambda invocation failed: {str(e)}"
        )


@tool()
async def aws_lambda_list_functions(
    region: str | None = None,
) -> LambdaListFunctionsResponse:
    """List all AWS Lambda functions in the configured account and region.

    Returns function metadata including name, ARN, runtime, handler, memory,
    timeout, code size, and description.

    Args:
        region: AWS region. Falls back to AWS_DEFAULT_REGION env var or us-east-1.

    Returns:
        List of Lambda function summaries.
    """
    try:
        err = _check_aws_creds()
        if err:
            return LambdaListFunctionsResponse(success=False, error=err)

        logger.info("Listing Lambda functions")
        client = _get_lambda_client(region)
        response = client.list_functions()

        functions = [
            LambdaFunctionSummary(
                function_name=func["FunctionName"],
                function_arn=func.get("FunctionArn"),
                runtime=func.get("Runtime"),
                handler=func.get("Handler"),
                last_modified=func.get("LastModified"),
                memory_size=func.get("MemorySize"),
                timeout=func.get("Timeout"),
                code_size=func.get("CodeSize"),
                description=func.get("Description"),
            )
            for func in response.get("Functions", [])
        ]

        data = LambdaListFunctionsData(
            functions=functions,
            count=len(functions),
        )

        logger.info("Listed %d Lambda functions", len(functions))
        return LambdaListFunctionsResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to list Lambda functions")
        return LambdaListFunctionsResponse(
            success=False, error=f"Failed to list Lambda functions: {str(e)}"
        )


@tool()
async def aws_lambda_get_function(
    function_name: str,
    region: str | None = None,
) -> LambdaGetFunctionResponse:
    """Get detailed information about an AWS Lambda function.

    Retrieves the function configuration, code location, tags, and
    concurrency settings. Includes environment variables, layers, state,
    and last update status.

    Args:
        function_name: The name, ARN, or partial ARN of the Lambda function.
        region: AWS region. Falls back to AWS_DEFAULT_REGION env var or us-east-1.

    Returns:
        Detailed function configuration including runtime, role, layers,
        environment variables, and state.
    """
    try:
        err = _check_aws_creds()
        if err:
            return LambdaGetFunctionResponse(success=False, error=err)

        logger.info("Getting Lambda function details function=%s", function_name)
        client = _get_lambda_client(region)
        response = client.get_function(FunctionName=function_name)

        config = response.get("Configuration", {})
        env_vars = config.get("Environment", {}).get("Variables")
        layers_list = config.get("Layers", [])
        layer_arns = [layer["Arn"] for layer in layers_list] if layers_list else None

        data = LambdaGetFunctionData(
            function_name=config.get("FunctionName", function_name),
            function_arn=config.get("FunctionArn", ""),
            runtime=config.get("Runtime"),
            handler=config.get("Handler"),
            role=config.get("Role"),
            code_size=config.get("CodeSize"),
            description=config.get("Description"),
            timeout=config.get("Timeout"),
            memory_size=config.get("MemorySize"),
            last_modified=config.get("LastModified"),
            state=config.get("State"),
            last_update_status=config.get("LastUpdateStatus"),
            environment_variables=env_vars,
            layers=layer_arns,
        )

        logger.info("Got Lambda function details function=%s", function_name)
        return LambdaGetFunctionResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to get Lambda function details")
        return LambdaGetFunctionResponse(
            success=False, error=f"Failed to get function details: {str(e)}"
        )


@tool()
async def aws_lambda_update_function_code(
    function_name: str,
    s3_bucket: str,
    s3_key: str,
    region: str | None = None,
) -> LambdaUpdateCodeResponse:
    """Update the deployment package of an AWS Lambda function from S3.

    Deploys new code from a ZIP archive stored in Amazon S3 to the
    specified Lambda function.

    Args:
        function_name: The name or ARN of the Lambda function to update.
        s3_bucket: S3 bucket containing the deployment package (.zip).
        s3_key: S3 object key of the deployment package (.zip).
        region: AWS region. Falls back to AWS_DEFAULT_REGION env var or us-east-1.

    Returns:
        Updated function metadata including new code size and update status.
    """
    try:
        err = _check_aws_creds()
        if err:
            return LambdaUpdateCodeResponse(success=False, error=err)

        logger.info(
            "Updating Lambda function code function=%s s3=%s/%s",
            function_name,
            s3_bucket,
            s3_key,
        )
        client = _get_lambda_client(region)
        response = client.update_function_code(
            FunctionName=function_name,
            S3Bucket=s3_bucket,
            S3Key=s3_key,
        )

        data = LambdaUpdateCodeData(
            function_name=response.get("FunctionName", function_name),
            function_arn=response.get("FunctionArn", ""),
            runtime=response.get("Runtime"),
            code_size=response.get("CodeSize"),
            last_modified=response.get("LastModified"),
            last_update_status=response.get("LastUpdateStatus"),
        )

        logger.info(
            "Lambda function code updated function=%s status=%s",
            function_name,
            data.last_update_status,
        )
        return LambdaUpdateCodeResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to update Lambda function code")
        return LambdaUpdateCodeResponse(
            success=False, error=f"Failed to update function code: {str(e)}"
        )


@tool()
async def aws_lambda_list_event_source_mappings(
    function_name: str | None = None,
    region: str | None = None,
) -> LambdaListEventSourceMappingsResponse:
    """List event source mappings for AWS Lambda functions.

    Returns mappings that connect event sources (SQS, Kinesis, DynamoDB Streams,
    etc.) to Lambda functions. Can be filtered to a specific function.

    Args:
        function_name: Optional function name or ARN to filter mappings.
            If omitted, lists all event source mappings in the account.
        region: AWS region. Falls back to AWS_DEFAULT_REGION env var or us-east-1.

    Returns:
        List of event source mappings with UUID, ARNs, state, and batch size.
    """
    try:
        err = _check_aws_creds()
        if err:
            return LambdaListEventSourceMappingsResponse(success=False, error=err)

        logger.info("Listing event source mappings function=%s", function_name)
        client = _get_lambda_client(region)

        kwargs = {}
        if function_name:
            kwargs["FunctionName"] = function_name

        response = client.list_event_source_mappings(**kwargs)

        mappings = [
            LambdaEventSourceMapping(
                uuid=m["UUID"],
                function_arn=m.get("FunctionArn"),
                event_source_arn=m.get("EventSourceArn"),
                state=m.get("State"),
                batch_size=m.get("BatchSize"),
                last_modified=str(m["LastModified"]) if m.get("LastModified") else None,
            )
            for m in response.get("EventSourceMappings", [])
        ]

        data = LambdaListEventSourceMappingsData(
            event_source_mappings=mappings,
            count=len(mappings),
        )

        logger.info("Listed %d event source mappings", len(mappings))
        return LambdaListEventSourceMappingsResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to list event source mappings")
        return LambdaListEventSourceMappingsResponse(
            success=False, error=f"Failed to list event source mappings: {str(e)}"
        )
