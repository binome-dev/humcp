from __future__ import annotations

import math

from src.humcp.decorator import tool
from src.tools.local.schemas import (
    BinaryOperationData,
    CalculatorResponse,
    FactorialData,
    IsPrimeData,
    LogarithmData,
    UnaryOperationData,
)


@tool()
async def add(a: float, b: float) -> CalculatorResponse:
    """Add two numbers."""
    return CalculatorResponse(
        success=True,
        data=BinaryOperationData(operation="add", a=a, b=b, result=a + b),
    )


@tool()
async def subtract(a: float, b: float) -> CalculatorResponse:
    """Subtract b from a."""
    return CalculatorResponse(
        success=True,
        data=BinaryOperationData(operation="subtract", a=a, b=b, result=a - b),
    )


@tool()
async def multiply(a: float, b: float) -> CalculatorResponse:
    """Multiply two numbers."""
    return CalculatorResponse(
        success=True,
        data=BinaryOperationData(operation="multiply", a=a, b=b, result=a * b),
    )


@tool()
async def divide(a: float, b: float) -> CalculatorResponse:
    """Divide a by b."""
    if b == 0:
        return CalculatorResponse(success=False, error="Division by zero")
    return CalculatorResponse(
        success=True,
        data=BinaryOperationData(operation="divide", a=a, b=b, result=a / b),
    )


@tool()
async def exponentiate(a: float, b: float) -> CalculatorResponse:
    """Raise a to the power of b."""
    try:
        result = math.pow(a, b)
    except (OverflowError, ValueError) as exc:
        return CalculatorResponse(success=False, error=f"Error computing power: {exc}")
    return CalculatorResponse(
        success=True,
        data=BinaryOperationData(operation="power", a=a, b=b, result=result),
    )


@tool()
async def factorial(n: int) -> CalculatorResponse:
    """Calculate factorial of n (must be non-negative)."""
    if n < 0:
        return CalculatorResponse(
            success=False, error="Factorial undefined for negative numbers"
        )
    try:
        result = math.factorial(n)
    except (OverflowError, MemoryError):
        return CalculatorResponse(
            success=False, error="Factorial result too large to compute"
        )
    return CalculatorResponse(
        success=True, data=FactorialData(operation="factorial", n=n, result=result)
    )


@tool()
async def is_prime(n: int) -> CalculatorResponse:
    """Check if n is prime."""
    if n <= 1:
        return CalculatorResponse(success=True, data=IsPrimeData(n=n, is_prime=False))
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return CalculatorResponse(
                success=True, data=IsPrimeData(n=n, is_prime=False, divisible_by=i)
            )
    return CalculatorResponse(success=True, data=IsPrimeData(n=n, is_prime=True))


@tool()
async def square_root(n: float) -> CalculatorResponse:
    """Calculate square root of n (must be non-negative)."""
    if n < 0:
        return CalculatorResponse(
            success=False, error="Square root undefined for negative numbers"
        )
    return CalculatorResponse(
        success=True,
        data=UnaryOperationData(operation="sqrt", n=n, result=math.sqrt(n)),
    )


@tool()
async def absolute_value(n: float) -> CalculatorResponse:
    """Calculate absolute value of n."""
    return CalculatorResponse(
        success=True, data=UnaryOperationData(operation="abs", n=n, result=abs(n))
    )


@tool()
async def logarithm(n: float, base: float = 0) -> CalculatorResponse:
    """Calculate logarithm of n. Base defaults to e (natural log) if 0."""
    if n <= 0:
        return CalculatorResponse(
            success=False, error="Logarithm undefined for non-positive numbers"
        )
    if base == 0:
        return CalculatorResponse(
            success=True,
            data=LogarithmData(operation="ln", n=n, result=math.log(n)),
        )
    if base <= 0 or base == 1:
        return CalculatorResponse(
            success=False, error="Base must be positive and not 1"
        )
    return CalculatorResponse(
        success=True,
        data=LogarithmData(operation="log", n=n, base=base, result=math.log(n, base)),
    )


@tool()
async def modulo(a: float, b: float) -> CalculatorResponse:
    """Calculate a modulo b."""
    if b == 0:
        return CalculatorResponse(success=False, error="Modulo by zero")
    return CalculatorResponse(
        success=True,
        data=BinaryOperationData(operation="mod", a=a, b=b, result=a % b),
    )


@tool()
async def greatest_common_divisor(a: int, b: int) -> CalculatorResponse:
    """Calculate GCD of a and b."""
    try:
        result = math.gcd(a, b)
    except Exception as e:
        return CalculatorResponse(success=False, error=f"GCD error: {e}")
    return CalculatorResponse(
        success=True,
        data=BinaryOperationData(operation="gcd", a=a, b=b, result=result),
    )
