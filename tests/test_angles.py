"""AEDP-4607 Ed A V1 Annex C sections C-4.6 through C-4.7."""

from fractions import Fraction

import pytest

from stanag4607 import BinaryAngle, SignedBinaryAngle


def test_ba16_official_worked_example_is_exact() -> None:
    angle = BinaryAngle.from_bytes(bytes.fromhex("59 1c"))

    assert angle.raw == 0x591C
    assert angle.bits == 16
    assert angle.degrees == Fraction(22_812 * 360, 2**16)
    assert float(angle.degrees) == 125.31005859375
    assert angle.to_bytes() == bytes.fromhex("59 1c")


def test_sa16_official_worked_example_is_exact() -> None:
    angle = SignedBinaryAngle.from_bytes(bytes.fromhex("ce 66"))

    assert angle.raw == -12_698
    assert angle.bits == 16
    assert angle.degrees == Fraction(-12_698 * 180, 2**16)
    assert float(angle.degrees) == -34.8760986328125
    assert angle.to_bytes() == bytes.fromhex("ce 66")


@pytest.mark.parametrize("width", [2, 4])
def test_binary_angles_round_trip_all_zero_and_one_bits(width: int) -> None:
    for encoded in (b"\x00" * width, b"\xff" * width):
        assert BinaryAngle.from_bytes(encoded).to_bytes() == encoded
        assert SignedBinaryAngle.from_bytes(encoded).to_bytes() == encoded


@pytest.mark.parametrize("encoded", [b"", b"x", b"xxx", b"xxxxx"])
def test_binary_angle_requires_16_or_32_bits(encoded: bytes) -> None:
    with pytest.raises(ValueError, match="2 or 4 bytes"):
        BinaryAngle.from_bytes(encoded)
    with pytest.raises(ValueError, match="2 or 4 bytes"):
        SignedBinaryAngle.from_bytes(encoded)


@pytest.mark.parametrize(
    "angle",
    [
        lambda: BinaryAngle(raw=-1, bits=16),
        lambda: BinaryAngle(raw=2**16, bits=16),
        lambda: BinaryAngle(raw=0, bits=8),
        lambda: SignedBinaryAngle(raw=-(2**15) - 1, bits=16),
        lambda: SignedBinaryAngle(raw=2**15, bits=16),
        lambda: SignedBinaryAngle(raw=0, bits=64),
    ],
)
def test_binary_angle_constructor_enforces_wire_range(angle: object) -> None:
    with pytest.raises(ValueError):
        angle()  # type: ignore[operator]
