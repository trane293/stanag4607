"""Lossless Free Text Segment support."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import DecodeError
from .packet import Segment

FREE_TEXT_SEGMENT_TYPE = 6
FREE_TEXT_PREFIX_SIZE = 20
FREE_TEXT_MIN_PAYLOAD_SIZE = 21
FREE_TEXT_MAX_PAYLOAD_SIZE = 65_535


def _fixed_bytes(name: str, value: bytes, width: int) -> None:
    if not isinstance(value, bytes) or len(value) != width:
        raise ValueError(f"{name} must be exactly {width} bytes")


@dataclass(frozen=True, slots=True)
class FreeTextSegment:
    """Exact F1-F3 Basic Character Set bytes."""

    originator_id: bytes
    recipient_id: bytes
    free_text: bytes

    def __post_init__(self) -> None:
        _fixed_bytes("originator_id", self.originator_id, 10)
        _fixed_bytes("recipient_id", self.recipient_id, 10)
        if not isinstance(self.free_text, bytes) or not 1 <= len(self.free_text) <= 65_515:
            raise ValueError("free_text must contain between 1 and 65515 bytes")

    def to_segment(self) -> Segment:
        """Encode F1-F3 as an exact type-6 segment."""

        return Segment(
            FREE_TEXT_SEGMENT_TYPE,
            self.originator_id + self.recipient_id + self.free_text,
        )


def decode_free_text_segment(segment: Segment) -> FreeTextSegment:
    """Decode a complete variable-length type-6 Free Text Segment."""

    if segment.segment_type != FREE_TEXT_SEGMENT_TYPE:
        raise DecodeError(
            f"free text decoder requires type {FREE_TEXT_SEGMENT_TYPE}, "
            f"received {segment.segment_type}"
        )
    size = len(segment.payload)
    if not FREE_TEXT_MIN_PAYLOAD_SIZE <= size <= FREE_TEXT_MAX_PAYLOAD_SIZE:
        raise DecodeError("free text payload must be between 21 and 65535 bytes")
    return FreeTextSegment(
        segment.payload[:10],
        segment.payload[10:FREE_TEXT_PREFIX_SIZE],
        segment.payload[FREE_TEXT_PREFIX_SIZE:],
    )
