from __future__ import annotations

import logging
import math
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastmcp import FastMCP

logger = logging.getLogger("humcp.tools.calculator")


async def add(a: float, b: float) -> dict:
    """
    Add two numbers and return the result.

    Args:
        a: First number
        b: Second number

    Returns:
        Result of adding a and b
    """
    try:
        result = a + b
        logger.info("calculator_add a=%s b=%s", a, b)
        return {
            "success": True,
            "data": {"operation": "addition", "a": a, "b": b, "result": result},
        }
    except Exception as e:
        logger.exception("calculator_add failed")
        return {"success": False, "error": str(e)}


async def subtract(a: float, b: float) -> dict:
    """
    Subtract second number from first and return the result.

    Args:
        a: First number (minuend)
        b: Second number (subtrahend)

    Returns:
        Result of subtracting b from a
    """
    try:
        result = a - b
        logger.info("calculator_subtract a=%s b=%s", a, b)
        return {
            "success": True,
            "data": {"operation": "subtraction", "a": a, "b": b, "result": result},
        }
    except Exception as e:
        logger.exception("calculator_subtract failed")
        return {"success": False, "error": str(e)}


async def multiply(a: float, b: float) -> dict:
    """
    Multiply two numbers and return the result.

    Args:
        a: First number
        b: Second number

    Returns:
        Result of multiplying a and b
    """
    try:
        result = a * b
        logger.info("calculator_multiply a=%s b=%s", a, b)
        return {
            "success": True,
            "data": {"operation": "multiplication", "a": a, "b": b, "result": result},
        }
    except Exception as e:
        logger.exception("calculator_multiply failed")
        return {"success": False, "error": str(e)}


async def divide(a: float, b: float) -> dict:
    """
    Divide first number by second and return the result.

    Args:
        a: Numerator
        b: Denominator

    Returns:
        Result of dividing a by b
    """
    try:
        if b == 0:
            return {"success": False, "error": "Division by zero is undefined"}

        result = a / b
        logger.info("calculator_divide a=%s b=%s", a, b)
        return {
            "success": True,
            "data": {"operation": "division", "a": a, "b": b, "result": result},
        }
    except Exception as e:
        logger.exception("calculator_divide failed")
        return {"success": False, "error": str(e)}


async def exponentiate(a: float, b: float) -> dict:
    """
    Raise first number to the power of the second number and return the result.

    Args:
        a: Base
        b: Exponent

    Returns:
        Result of raising a to the power of b
    """
    try:
        result = math.pow(a, b)
        logger.info("calculator_exponentiate a=%s b=%s", a, b)
        return {
            "success": True,
            "data": {"operation": "exponentiation", "a": a, "b": b, "result": result},
        }
    except Exception as e:
        logger.exception("calculator_exponentiate failed")
        return {"success": False, "error": str(e)}


async def factorial(n: int) -> dict:
    """
    Calculate the factorial of a number and return the result.

    Args:
        n: Number to calculate the factorial of (must be non-negative)

    Returns:
        Factorial of n
    """
    try:
        if n < 0:
            return {
                "success": False,
                "error": "Factorial of a negative number is undefined",
            }

        result = math.factorial(n)
        logger.info("calculator_factorial n=%s", n)
        return {
            "success": True,
            "data": {"operation": "factorial", "n": n, "result": result},
        }
    except Exception as e:
        logger.exception("calculator_factorial failed")
        return {"success": False, "error": str(e)}


async def is_prime(n: int) -> dict:
    """
    Check if a number is prime and return the result.

    Args:
        n: Number to check if prime

    Returns:
        Boolean indicating whether n is prime
    """
    try:
        if n <= 1:
            return {
                "success": True,
                "data": {
                    "operation": "prime_check",
                    "n": n,
                    "is_prime": False,
                    "reason": "Numbers less than or equal to 1 are not prime",
                },
            }

        # Check divisibility from 2 to sqrt(n)
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                return {
                    "success": True,
                    "data": {
                        "operation": "prime_check",
                        "n": n,
                        "is_prime": False,
                        "divisible_by": i,
                    },
                }

        logger.info("calculator_is_prime n=%s", n)
        return {
            "success": True,
            "data": {"operation": "prime_check", "n": n, "is_prime": True},
        }
    except Exception as e:
        logger.exception("calculator_is_prime failed")
        return {"success": False, "error": str(e)}


async def square_root(n: float) -> dict:
    """
    Calculate the square root of a number and return the result.

    Args:
        n: Number to calculate the square root of (must be non-negative)

    Returns:
        Square root of n
    """
    try:
        if n < 0:
            return {
                "success": False,
                "error": "Square root of a negative number is undefined (use complex numbers)",
            }

        result = math.sqrt(n)
        logger.info("calculator_square_root n=%s", n)
        return {
            "success": True,
            "data": {"operation": "square_root", "n": n, "result": result},
        }
    except Exception as e:
        logger.exception("calculator_square_root failed")
        return {"success": False, "error": str(e)}


async def absolute_value(n: float) -> dict:
    """
    Calculate the absolute value of a number.

    Args:
        n: Number to calculate the absolute value of

    Returns:
        Absolute value of n
    """
    try:
        result = abs(n)
        logger.info("calculator_absolute_value n=%s", n)
        return {
            "success": True,
            "data": {"operation": "absolute_value", "n": n, "result": result},
        }
    except Exception as e:
        logger.exception("calculator_absolute_value failed")
        return {"success": False, "error": str(e)}


async def logarithm(n: float, base: float = 0) -> dict:
    """
    Calculate the logarithm of a number with an optional base.

    Args:
        n: Number to calculate the logarithm of (must be positive)
        base: Optional base for the logarithm (defaults to e for natural log)

    Returns:
        Logarithm of n with the specified base
    """
    try:
        if n <= 0:
            return {
                "success": False,
                "error": "Logarithm is only defined for positive numbers",
            }

        if base == 0:
            result = math.log(n)
            base_str = "e (natural logarithm)"
        else:
            if base < 0 or base == 1:
                return {
                    "success": False,
                    "error": "Logarithm base must be positive and not equal to 1",
                }
            result = math.log(n, base)
            base_str = str(base)

        logger.info("calculator_logarithm n=%s base=%s", n, base_str)
        return {
            "success": True,
            "data": {
                "operation": "logarithm",
                "n": n,
                "base": base_str,
                "result": result,
            },
        }
    except Exception as e:
        logger.exception("calculator_logarithm failed")
        return {"success": False, "error": str(e)}


async def modulo(a: float, b: float) -> dict:
    """
    Calculate the remainder when dividing the first number by the second.

    Args:
        a: Dividend
        b: Divisor

    Returns:
        Remainder of a divided by b
    """
    try:
        if b == 0:
            return {"success": False, "error": "Modulo by zero is undefined"}

        result = a % b
        logger.info("calculator_modulo a=%s b=%s", a, b)
        return {
            "success": True,
            "data": {"operation": "modulo", "a": a, "b": b, "result": result},
        }
    except Exception as e:
        logger.exception("calculator_modulo failed")
        return {"success": False, "error": str(e)}


async def greatest_common_divisor(a: int, b: int) -> dict:
    """
    Calculate the greatest common divisor (GCD) of two integers.

    Args:
        a: First integer
        b: Second integer

    Returns:
        Greatest common divisor of a and b
    """
    try:
        result = math.gcd(a, b)
        logger.info("calculator_greatest_common_divisor a=%s b=%s", a, b)
        return {
            "success": True,
            "data": {"operation": "gcd", "a": a, "b": b, "result": result},
        }
    except Exception as e:
        logger.exception("calculator_greatest_common_divisor failed")
        return {"success": False, "error": str(e)}


def register_tools(mcp: FastMCP) -> None:
    """Register all Calculator tools with the MCP server."""
    logger.info("Registering calculator tools")

    # Basic arithmetic operations
    mcp.tool(name="calculator_add")(add)
    mcp.tool(name="calculator_subtract")(subtract)
    mcp.tool(name="calculator_multiply")(multiply)
    mcp.tool(name="calculator_divide")(divide)
    mcp.tool(name="calculator_modulo")(modulo)
    # Power and root operations
    mcp.tool(name="calculator_exponentiate")(exponentiate)
    mcp.tool(name="calculator_square_root")(square_root)

    # Mathematical functions
    mcp.tool(name="calculator_factorial")(factorial)
    mcp.tool(name="calculator_absolute_value")(absolute_value)
    mcp.tool(name="calculator_logarithm")(logarithm)

    # Number theory
    mcp.tool(name="calculator_is_prime")(is_prime)
    mcp.tool(name="calculator_greatest_common_divisor")(greatest_common_divisor)
