"""Exact STANAG 4607 signed binary-decimal values."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True, slots=True)
class SignedBinaryDecimal:
    """A sign-magnitude B16 or B32 value with exact rational conversion."""

    raw: int
    bits: int

    def __post_init__(self) -> None:
        if self.bits not in (16, 32):
            raise ValueError("signed binary decimal width must be 16 or 32 bits")
        if not isinstance(self.raw, int) or not 0 <= self.raw < 2**self.bits:
            raise ValueError(f"raw must be an unsigned {self.bits}-bit integer")

    @classmethod
    def from_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> SignedBinaryDecimal:
        """Decode a two- or four-byte big-endian B16/B32 value."""

        encoded = bytes(data)
        if len(encoded) not in (2, 4):
            raise ValueError("signed binary decimal must be exactly 2 or 4 bytes")
        return cls(int.from_bytes(encoded, "big"), len(encoded) * 8)

    @property
    def value(self) -> Fraction:
        """Return the exact represented value."""

        sign_bit = 1 << (self.bits - 1)
        magnitude = self.raw & (sign_bit - 1)
        fraction_bits = 7 if self.bits == 16 else 23
        value = Fraction(magnitude, 2**fraction_bits)
        return -value if self.raw & sign_bit else value

    @property
    def is_negative_zero(self) -> bool:
        """Whether the sign bit is set while every magnitude bit is clear."""

        return self.raw == 1 << (self.bits - 1)

    def to_bytes(self) -> bytes:
        """Encode the exact original sign and magnitude bits."""

        return self.raw.to_bytes(self.bits // 8, "big")


@dataclass(frozen=True, slots=True)
class SignedHertzDecimal:
    """An H32 sign-magnitude value with 15 integer and 16 fraction bits."""

    raw: int

    def __post_init__(self) -> None:
        if not isinstance(self.raw, int) or not 0 <= self.raw < 2**32:
            raise ValueError("raw must be an unsigned 32-bit integer")

    @classmethod
    def from_bytes(cls, data: bytes | bytearray | memoryview) -> SignedHertzDecimal:
        """Decode one four-byte big-endian H32 value."""

        encoded = bytes(data)
        if len(encoded) != 4:
            raise ValueError("signed Hertz decimal must be exactly 4 bytes")
        return cls(int.from_bytes(encoded, "big"))

    @property
    def hertz(self) -> Fraction:
        """Return the exact represented frequency in Hertz."""

        magnitude = self.raw & 0x7FFFFFFF
        value = Fraction(magnitude, 2**16)
        return -value if self.raw & 0x80000000 else value

    @property
    def is_negative_zero(self) -> bool:
        """Whether the sign bit is set while every magnitude bit is clear."""

        return self.raw == 0x80000000

    def to_bytes(self) -> bytes:
        """Encode the exact original sign and magnitude bits."""

        return self.raw.to_bytes(4, "big")
