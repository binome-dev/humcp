import pytest

from src.tools.local.calculator import (
    absolute_value,
    add,
    divide,
    exponentiate,
    factorial,
    greatest_common_divisor,
    is_prime,
    logarithm,
    modulo,
    multiply,
    square_root,
    subtract,
)


class TestAdd:
    @pytest.mark.asyncio
    async def test_add_positive_numbers(self):
        result = await add(2, 3)
        assert result["success"] is True
        assert result["data"]["result"] == 5

    @pytest.mark.asyncio
    async def test_add_negative_numbers(self):
        result = await add(-2, -3)
        assert result["success"] is True
        assert result["data"]["result"] == -5

    @pytest.mark.asyncio
    async def test_add_floats(self):
        result = await add(1.5, 2.5)
        assert result["success"] is True
        assert result["data"]["result"] == 4.0


class TestSubtract:
    @pytest.mark.asyncio
    async def test_subtract_positive(self):
        result = await subtract(10, 4)
        assert result["success"] is True
        assert result["data"]["result"] == 6

    @pytest.mark.asyncio
    async def test_subtract_negative_result(self):
        result = await subtract(4, 10)
        assert result["success"] is True
        assert result["data"]["result"] == -6


class TestMultiply:
    @pytest.mark.asyncio
    async def test_multiply_positive(self):
        result = await multiply(3, 4)
        assert result["success"] is True
        assert result["data"]["result"] == 12

    @pytest.mark.asyncio
    async def test_multiply_by_zero(self):
        result = await multiply(5, 0)
        assert result["success"] is True
        assert result["data"]["result"] == 0


class TestDivide:
    @pytest.mark.asyncio
    async def test_divide_positive(self):
        result = await divide(10, 2)
        assert result["success"] is True
        assert result["data"]["result"] == 5

    @pytest.mark.asyncio
    async def test_divide_by_zero(self):
        result = await divide(10, 0)
        assert result["success"] is False
        assert "zero" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_divide_float_result(self):
        result = await divide(7, 2)
        assert result["success"] is True
        assert result["data"]["result"] == 3.5


class TestExponentiate:
    @pytest.mark.asyncio
    async def test_exponentiate_positive(self):
        result = await exponentiate(2, 3)
        assert result["success"] is True
        assert result["data"]["result"] == 8

    @pytest.mark.asyncio
    async def test_exponentiate_zero_power(self):
        result = await exponentiate(5, 0)
        assert result["success"] is True
        assert result["data"]["result"] == 1


class TestFactorial:
    @pytest.mark.asyncio
    async def test_factorial_positive(self):
        result = await factorial(5)
        assert result["success"] is True
        assert result["data"]["result"] == 120

    @pytest.mark.asyncio
    async def test_factorial_zero(self):
        result = await factorial(0)
        assert result["success"] is True
        assert result["data"]["result"] == 1

    @pytest.mark.asyncio
    async def test_factorial_negative(self):
        result = await factorial(-1)
        assert result["success"] is False
        assert "negative" in result["error"].lower()


class TestIsPrime:
    @pytest.mark.asyncio
    async def test_is_prime_true(self):
        result = await is_prime(7)
        assert result["success"] is True
        assert result["data"]["is_prime"] is True

    @pytest.mark.asyncio
    async def test_is_prime_false(self):
        result = await is_prime(4)
        assert result["success"] is True
        assert result["data"]["is_prime"] is False

    @pytest.mark.asyncio
    async def test_is_prime_one(self):
        result = await is_prime(1)
        assert result["success"] is True
        assert result["data"]["is_prime"] is False


class TestSquareRoot:
    @pytest.mark.asyncio
    async def test_square_root_positive(self):
        result = await square_root(16)
        assert result["success"] is True
        assert result["data"]["result"] == 4

    @pytest.mark.asyncio
    async def test_square_root_negative(self):
        result = await square_root(-4)
        assert result["success"] is False
        assert "negative" in result["error"].lower()


class TestAbsoluteValue:
    @pytest.mark.asyncio
    async def test_absolute_value_positive(self):
        result = await absolute_value(5)
        assert result["success"] is True
        assert result["data"]["result"] == 5

    @pytest.mark.asyncio
    async def test_absolute_value_negative(self):
        result = await absolute_value(-5)
        assert result["success"] is True
        assert result["data"]["result"] == 5


class TestLogarithm:
    @pytest.mark.asyncio
    async def test_logarithm_natural(self):
        result = await logarithm(2.718281828)
        assert result["success"] is True
        assert abs(result["data"]["result"] - 1) < 0.001

    @pytest.mark.asyncio
    async def test_logarithm_base_10(self):
        result = await logarithm(100, base=10)
        assert result["success"] is True
        assert result["data"]["result"] == 2

    @pytest.mark.asyncio
    async def test_logarithm_negative(self):
        result = await logarithm(-1)
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_logarithm_invalid_base(self):
        result = await logarithm(10, base=1)
        assert result["success"] is False


class TestModulo:
    @pytest.mark.asyncio
    async def test_modulo_positive(self):
        result = await modulo(10, 3)
        assert result["success"] is True
        assert result["data"]["result"] == 1

    @pytest.mark.asyncio
    async def test_modulo_by_zero(self):
        result = await modulo(10, 0)
        assert result["success"] is False
        assert "zero" in result["error"].lower()


class TestGCD:
    @pytest.mark.asyncio
    async def test_gcd_positive(self):
        result = await greatest_common_divisor(12, 8)
        assert result["success"] is True
        assert result["data"]["result"] == 4

    @pytest.mark.asyncio
    async def test_gcd_coprime(self):
        result = await greatest_common_divisor(7, 11)
        assert result["success"] is True
        assert result["data"]["result"] == 1
