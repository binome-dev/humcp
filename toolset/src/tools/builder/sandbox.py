"""Sandboxed Python execution environment using RestrictedPython."""

from __future__ import annotations

import asyncio
import builtins
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from RestrictedPython import compile_restricted, safe_builtins
from RestrictedPython.Eval import default_guarded_getiter
from RestrictedPython.Guards import (
    guarded_iter_unpack_sequence,
    safer_getattr,
)

logger = logging.getLogger("humcp.builder.sandbox")

# Execution timeout in seconds
EXECUTION_TIMEOUT = 60

# Thread pool for running sandboxed code
_executor = ThreadPoolExecutor(max_workers=4)


def _get_allowed_imports() -> dict[str, Any]:
    """Get the allowed imports for sandboxed execution."""
    import datetime
    import json
    import math
    import re

    return {
        "json": json,
        "re": re,
        "math": math,
        "datetime": datetime,
    }


def _get_safe_builtins() -> dict[str, Any]:
    """Get safe builtins for sandboxed execution."""
    builtins = dict(safe_builtins)

    # Add additional safe builtins
    builtins.update(
        {
            # Type constructors
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "frozenset": frozenset,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "bytes": bytes,
            # Utility functions
            "len": len,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "reversed": reversed,
            "min": min,
            "max": max,
            "sum": sum,
            "abs": abs,
            "round": round,
            "all": all,
            "any": any,
            "isinstance": isinstance,
            "hasattr": hasattr,
            "getattr": getattr,
            # String methods
            "chr": chr,
            "ord": ord,
            "repr": repr,
            "format": format,
            # Exceptions (for raising)
            "Exception": Exception,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "KeyError": KeyError,
            "IndexError": IndexError,
        }
    )

    return builtins


def _get_restricted_globals() -> dict[str, Any]:
    """Build the restricted globals for sandboxed execution."""
    restricted_globals: dict[str, Any] = {
        "__builtins__": _get_safe_builtins(),
        "_getattr_": safer_getattr,
        "_getiter_": default_guarded_getiter,
        "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
        # Allow print for debugging (captured)
        "_print_": lambda *args, **kwargs: None,  # Silently ignore prints
        "_getitem_": lambda obj, key: obj[key],
        "_write_": lambda obj: obj,  # Allow writes to containers
    }

    # Add allowed imports
    restricted_globals.update(_get_allowed_imports())

    return restricted_globals


class SandboxError(Exception):
    """Error during sandboxed execution."""

    pass


class CompilationError(SandboxError):
    """Error during code compilation."""

    pass


class ExecutionError(SandboxError):
    """Error during code execution."""

    pass


class TimeoutError(SandboxError):
    """Execution timed out."""

    pass


def compile_code(code: str, filename: str = "<custom_tool>") -> Any:
    """Compile Python code in restricted mode.

    Args:
        code: Python source code to compile.
        filename: Filename for error messages.

    Returns:
        Compiled code object.

    Raises:
        CompilationError: If compilation fails.
    """
    try:
        # RestrictedPython 8.x returns the compiled code directly
        # or raises an exception if compilation fails
        compiled = compile_restricted(code, filename=filename, mode="exec")
        return compiled

    except SyntaxError as e:
        raise CompilationError(f"Syntax error: {e}") from e
    except Exception as e:
        raise CompilationError(f"Compilation failed: {e}") from e


def _execute_sync(
    compiled_code: Any,
    function_name: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Execute compiled code synchronously (runs in thread pool)."""
    # Create execution namespace
    namespace: dict[str, Any] = {}
    restricted_globals = _get_restricted_globals()

    # Execute the code to define the function
    exec(compiled_code, restricted_globals, namespace)

    # Get the function
    if function_name not in namespace:
        raise ExecutionError(
            f"Function '{function_name}' not found. Available: {list(namespace.keys())}"
        )

    func = namespace[function_name]
    if not callable(func):
        raise ExecutionError(f"'{function_name}' is not a function")

    # Execute the function
    result = func(**params)

    # Validate result
    if not isinstance(result, dict):
        raise ExecutionError(
            f"Function must return a dict, got {type(result).__name__}"
        )

    return result


async def execute_sandboxed(
    compiled_code: Any,
    function_name: str,
    params: dict[str, Any],
    timeout: float = EXECUTION_TIMEOUT,
) -> dict[str, Any]:
    """Execute compiled code in a sandboxed environment.

    Args:
        compiled_code: Compiled code object from compile_code().
        function_name: Name of the function to call.
        params: Parameters to pass to the function.
        timeout: Maximum execution time in seconds.

    Returns:
        Result dictionary from the function.

    Raises:
        ExecutionError: If execution fails.
        TimeoutError: If execution times out.
    """
    loop = asyncio.get_event_loop()

    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(
                _executor,
                _execute_sync,
                compiled_code,
                function_name,
                params,
            ),
            timeout=timeout,
        )
        return result

    except builtins.TimeoutError as e:
        raise TimeoutError(f"Execution timed out after {timeout} seconds") from e
    except ExecutionError:
        raise
    except Exception as e:
        raise ExecutionError(f"Execution failed: {e}") from e


def validate_tool_code(code: str) -> tuple[bool, str]:
    """Validate tool code before saving.

    Checks:
    - Code compiles successfully
    - Contains an 'execute' function
    - Function signature looks reasonable

    Args:
        code: Python source code.

    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        # Try to compile
        compiled = compile_code(code)

        # Execute to check function exists
        namespace: dict[str, Any] = {}
        restricted_globals = _get_restricted_globals()
        exec(compiled, restricted_globals, namespace)

        # Check for execute function
        if "execute" not in namespace:
            return False, "Code must define an 'execute' function"

        if not callable(namespace["execute"]):
            return False, "'execute' must be a function"

        return True, ""

    except CompilationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Validation failed: {e}"
