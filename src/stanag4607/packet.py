"""STANAG 4607 packet framing values."""

from __future__ import annotations

from dataclasses import dataclass
from struct import Struct

from .errors import DecodeError

PACKET_HEADER_SIZE = 32
SEGMENT_HEADER_SIZE = 5
DEFAULT_MAX_PACKET_SIZE = 65_535
DEFAULT_MAX_SEGMENTS = 4_096
_PACKET_HEADER = Struct(">2sI2sB2sHB10sII")
_SEGMENT_HEADER = Struct(">BI")


def _require_bytes(name: str, value: bytes, width: int) -> None:
    if not isinstance(value, bytes) or len(value) != width:
        raise ValueError(f"{name} must be exactly {width} bytes")


def _require_uint(name: str, value: int, bits: int) -> None:
    if not isinstance(value, int) or not 0 <= value < 2**bits:
        raise ValueError(f"{name} must be an unsigned {bits}-bit integer")


@dataclass(frozen=True, slots=True)
class DecodeLimits:
    """Explicit resource bounds for complete-packet decoding."""

    max_packet_size: int = DEFAULT_MAX_PACKET_SIZE
    max_segments: int = DEFAULT_MAX_SEGMENTS

    def __post_init__(self) -> None:
        if self.max_packet_size < PACKET_HEADER_SIZE:
            raise ValueError(f"max_packet_size must be at least {PACKET_HEADER_SIZE}")
        if self.max_packet_size >= 2**32:
            raise ValueError("max_packet_size must fit an unsigned 32-bit integer")
        if self.max_segments < 0:
            raise ValueError("max_segments must not be negative")


_DEFAULT_DECODE_LIMITS = DecodeLimits()


@dataclass(frozen=True, slots=True)
class PacketHeader:
    """The fixed-width P1-P10 packet header from AEDP-4607 Table 3-1.

    Character fields retain their exact wire bytes. This keeps decoding lossless
    and leaves character-repertoire policy to a later explicit validation layer.
    """

    version_id: bytes
    packet_size: int
    nationality: bytes
    security_classification: int
    classification_system: bytes
    security_codes: int
    exercise_indicator: int
    platform_id: bytes
    mission_id: int
    job_id: int

    def __post_init__(self) -> None:
        _require_bytes("version_id", self.version_id, 2)
        _require_uint("packet_size", self.packet_size, 32)
        if self.packet_size < PACKET_HEADER_SIZE:
            raise ValueError(f"packet_size must be at least {PACKET_HEADER_SIZE}")
        _require_bytes("nationality", self.nationality, 2)
        _require_uint("security_classification", self.security_classification, 8)
        _require_bytes("classification_system", self.classification_system, 2)
        _require_uint("security_codes", self.security_codes, 16)
        _require_uint("exercise_indicator", self.exercise_indicator, 8)
        _require_bytes("platform_id", self.platform_id, 10)
        _require_uint("mission_id", self.mission_id, 32)
        _require_uint("job_id", self.job_id, 32)

    def to_bytes(self) -> bytes:
        """Encode the header in standard-defined big-endian field order."""

        return _PACKET_HEADER.pack(
            self.version_id,
            self.packet_size,
            self.nationality,
            self.security_classification,
            self.classification_system,
            self.security_codes,
            self.exercise_indicator,
            self.platform_id,
            self.mission_id,
            self.job_id,
        )


@dataclass(frozen=True, slots=True)
class SegmentHeader:
    """The fixed-width S1-S2 segment header from AEDP-4607 Table 3-6."""

    segment_type: int
    segment_size: int

    def __post_init__(self) -> None:
        _require_uint("segment_type", self.segment_type, 8)
        _require_uint("segment_size", self.segment_size, 32)
        if self.segment_size < SEGMENT_HEADER_SIZE:
            raise ValueError(f"segment_size must be at least {SEGMENT_HEADER_SIZE}")

    def to_bytes(self) -> bytes:
        """Encode the segment header in standard-defined field order."""

        return _SEGMENT_HEADER.pack(self.segment_type, self.segment_size)


@dataclass(frozen=True, slots=True)
class Segment:
    """A losslessly framed segment whose payload may be decoded elsewhere."""

    segment_type: int
    payload: bytes

    def __post_init__(self) -> None:
        _require_uint("segment_type", self.segment_type, 8)
        if not isinstance(self.payload, bytes):
            raise ValueError("payload must be bytes")
        if len(self.payload) > 2**32 - 1 - SEGMENT_HEADER_SIZE:
            raise ValueError("payload is too large for the segment size field")

    @property
    def header(self) -> SegmentHeader:
        """Return the header implied by this segment's payload."""

        return SegmentHeader(self.segment_type, SEGMENT_HEADER_SIZE + len(self.payload))

    def to_bytes(self) -> bytes:
        """Encode the segment header and unchanged payload."""

        return self.header.to_bytes() + self.payload


@dataclass(frozen=True, slots=True)
class Packet:
    """One complete packet with losslessly framed segment payloads."""

    header: PacketHeader
    segments: tuple[Segment, ...]

    def to_bytes(self) -> bytes:
        """Encode the packet, requiring P2 to agree with its actual size."""

        body = b"".join(segment.to_bytes() for segment in self.segments)
        actual_size = PACKET_HEADER_SIZE + len(body)
        if self.header.packet_size != actual_size:
            raise ValueError(
                f"packet_size is {self.header.packet_size}, but encoded size is {actual_size}"
            )
        return self.header.to_bytes() + body


def decode_packet_header(data: bytes | bytearray | memoryview) -> PacketHeader:
    """Decode one complete 32-byte packet header without consuming payload bytes."""

    raw = bytes(data)
    if len(raw) != PACKET_HEADER_SIZE:
        raise DecodeError(f"packet header must be exactly {PACKET_HEADER_SIZE} bytes")

    values = _PACKET_HEADER.unpack(raw)
    try:
        return PacketHeader(*values)
    except ValueError as error:
        raise DecodeError(f"invalid packet header: {error}") from error


def decode_segment_header(data: bytes | bytearray | memoryview) -> SegmentHeader:
    """Decode one complete 5-byte segment header."""

    raw = bytes(data)
    if len(raw) != SEGMENT_HEADER_SIZE:
        raise DecodeError(f"segment header must be exactly {SEGMENT_HEADER_SIZE} bytes")
    try:
        return SegmentHeader(*_SEGMENT_HEADER.unpack(raw))
    except ValueError as error:
        raise DecodeError(f"invalid segment header: {error}") from error


def decode_packet(
    data: bytes | bytearray | memoryview,
    *,
    limits: DecodeLimits = _DEFAULT_DECODE_LIMITS,
) -> Packet:
    """Decode one complete packet and retain every segment payload unchanged."""

    source = memoryview(data)
    if source.nbytes > limits.max_packet_size:
        raise DecodeError(
            f"input size {source.nbytes} exceeds maximum packet size {limits.max_packet_size}"
        )
    if source.nbytes < PACKET_HEADER_SIZE:
        raise DecodeError(f"packet is shorter than its {PACKET_HEADER_SIZE}-byte header")
    raw = bytes(source)

    header = decode_packet_header(raw[:PACKET_HEADER_SIZE])
    if header.packet_size > limits.max_packet_size:
        raise DecodeError(
            f"declared packet size {header.packet_size} exceeds maximum packet size "
            f"{limits.max_packet_size}"
        )
    if header.packet_size != len(raw):
        raise DecodeError(
            f"declared packet size {header.packet_size} does not match input size {len(raw)}"
        )

    segments: list[Segment] = []
    offset = PACKET_HEADER_SIZE
    while offset < len(raw):
        if len(segments) >= limits.max_segments:
            raise DecodeError(f"segment count exceeds configured limit {limits.max_segments}")
        remaining = len(raw) - offset
        if remaining < SEGMENT_HEADER_SIZE:
            raise DecodeError(f"truncated segment header at byte offset {offset}")

        segment_header = decode_segment_header(raw[offset : offset + SEGMENT_HEADER_SIZE])
        if segment_header.segment_size > remaining:
            raise DecodeError(
                f"segment size {segment_header.segment_size} at byte offset {offset} "
                f"exceeds {remaining} remaining packet bytes"
            )
        end = offset + segment_header.segment_size
        segments.append(
            Segment(segment_header.segment_type, raw[offset + SEGMENT_HEADER_SIZE : end])
        )
        offset = end

    return Packet(header=header, segments=tuple(segments))
