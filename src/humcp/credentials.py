"""Credential resolution utilities (env-var only)."""

import os


async def resolve_credential(env_var_name: str) -> str | None:
    """Resolve a credential from environment variables.

    Args:
        env_var_name: Name of the environment variable to read.

    Returns:
        Value of the environment variable, or None if not set.
    """
    return os.getenv(env_var_name)
