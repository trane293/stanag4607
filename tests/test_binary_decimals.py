"""AEDP-4607 Ed A V1 Annex C section C-4.5 and Table C-5."""

from collections.abc import Callable
from fractions import Fraction

import pytest

from stanag4607 import SignedBinaryDecimal, SignedHertzDecimal


@pytest.mark.parametrize(
    ("raw", "bits", "value"),
    [
        (0x0F00, 16, Fraction(30)),
        (0x8F00, 16, Fraction(-30)),
        (0x7FFF, 16, Fraction(32_767, 128)),
        (0x04C00000, 32, Fraction(19, 2)),
        (0x84C00000, 32, Fraction(-19, 2)),
    ],
)
def test_signed_binary_decimal_uses_exact_sign_magnitude(
    raw: int, bits: int, value: Fraction
) -> None:
    decimal = SignedBinaryDecimal(raw, bits)

    assert decimal.value == value
    assert SignedBinaryDecimal.from_bytes(decimal.to_bytes()) == decimal


def test_binary_decimal_preserves_negative_zero() -> None:
    decimal = SignedBinaryDecimal(0x8000, 16)

    assert decimal.value == 0
    assert decimal.is_negative_zero
    assert decimal.to_bytes() == b"\x80\x00"


@pytest.mark.parametrize(
    ("raw", "value"),
    [
        (0x00788000, Fraction(241, 2)),
        (0x80788000, Fraction(-241, 2)),
        (0x7FFFFFFF, Fraction(2**31 - 1, 2**16)),
    ],
)
def test_signed_hertz_decimal_uses_sixteen_fraction_bits(
    raw: int, value: Fraction
) -> None:
    decimal = SignedHertzDecimal(raw)

    assert decimal.hertz == value
    assert SignedHertzDecimal.from_bytes(decimal.to_bytes()) == decimal


def test_hertz_decimal_preserves_negative_zero() -> None:
    decimal = SignedHertzDecimal(0x80000000)

    assert decimal.hertz == 0
    assert decimal.is_negative_zero
    assert decimal.to_bytes() == b"\x80\x00\x00\x00"


@pytest.mark.parametrize("bits", [8, 24, 64])
def test_binary_decimal_rejects_unsupported_width(bits: int) -> None:
    with pytest.raises(ValueError, match="16 or 32"):
        SignedBinaryDecimal(0, bits)


@pytest.mark.parametrize(
    "constructor",
    [
        lambda: SignedBinaryDecimal(-1, 16),
        lambda: SignedBinaryDecimal(2**16, 16),
        lambda: SignedHertzDecimal(-1),
        lambda: SignedHertzDecimal(2**32),
    ],
)
def test_decimal_rejects_values_outside_wire_width(constructor: Callable[[], object]) -> None:
    with pytest.raises(ValueError, match="unsigned"):
        constructor()


@pytest.mark.parametrize("encoded", [b"", b"x", b"x" * 3, b"x" * 5])
def test_decimal_from_bytes_requires_supported_width(encoded: bytes) -> None:
    with pytest.raises(ValueError, match="2 or 4 bytes"):
        SignedBinaryDecimal.from_bytes(encoded)


@pytest.mark.parametrize("encoded", [b"", b"x" * 3, b"x" * 5])
def test_hertz_decimal_requires_exactly_four_bytes(encoded: bytes) -> None:
    with pytest.raises(ValueError, match="4 bytes"):
        SignedHertzDecimal.from_bytes(encoded)
