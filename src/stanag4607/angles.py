"""Exact STANAG 4607 binary-angle wire values."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import TypeVar

_Angle = TypeVar("_Angle", bound="BinaryAngle")
_SignedAngle = TypeVar("_SignedAngle", bound="SignedBinaryAngle")


def _bits_for(data: bytes | bytearray | memoryview) -> tuple[bytes, int]:
    encoded = bytes(data)
    if len(encoded) not in (2, 4):
        raise ValueError("binary angle must be exactly 2 or 4 bytes")
    return encoded, len(encoded) * 8


@dataclass(frozen=True, slots=True)
class BinaryAngle:
    """An exact BA16 or BA32 unsigned wire value."""

    raw: int
    bits: int

    def __post_init__(self) -> None:
        if self.bits not in (16, 32):
            raise ValueError("bits must be 16 or 32")
        if not isinstance(self.raw, int) or not 0 <= self.raw < 2**self.bits:
            raise ValueError(f"raw must be an unsigned {self.bits}-bit integer")

    @classmethod
    def from_bytes(cls: type[_Angle], data: bytes | bytearray | memoryview) -> _Angle:
        """Decode a BA16 or BA32 from big-endian bytes."""

        encoded, bits = _bits_for(data)
        return cls(int.from_bytes(encoded, "big"), bits)

    @property
    def degrees(self) -> Fraction:
        """Return the represented angle in exact rational degrees."""

        return Fraction(self.raw * 360, 2**self.bits)

    def to_bytes(self) -> bytes:
        """Return the original-width big-endian encoding."""

        return self.raw.to_bytes(self.bits // 8, "big")


@dataclass(frozen=True, slots=True)
class SignedBinaryAngle:
    """An exact SA16 or SA32 signed two's-complement wire value."""

    raw: int
    bits: int

    def __post_init__(self) -> None:
        if self.bits not in (16, 32):
            raise ValueError("bits must be 16 or 32")
        minimum = -(2 ** (self.bits - 1))
        maximum = 2 ** (self.bits - 1) - 1
        if not isinstance(self.raw, int) or not minimum <= self.raw <= maximum:
            raise ValueError(f"raw must be a signed {self.bits}-bit integer")

    @classmethod
    def from_bytes(
        cls: type[_SignedAngle], data: bytes | bytearray | memoryview
    ) -> _SignedAngle:
        """Decode an SA16 or SA32 from big-endian two's-complement bytes."""

        encoded, bits = _bits_for(data)
        return cls(int.from_bytes(encoded, "big", signed=True), bits)

    @property
    def degrees(self) -> Fraction:
        """Return the represented angle in exact rational degrees."""

        return Fraction(self.raw * 180, 2**self.bits)

    def to_bytes(self) -> bytes:
        """Return the original-width big-endian two's-complement encoding."""

        return self.raw.to_bytes(self.bits // 8, "big", signed=True)

