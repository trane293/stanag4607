"""Lossless Processing History Segment support."""

from __future__ import annotations

from dataclasses import dataclass
from struct import Struct

from .errors import DecodeError
from .packet import Segment

PROCESSING_HISTORY_SEGMENT_TYPE = 12
PROCESSING_HISTORY_PREFIX_SIZE = 21
PROCESSING_RECORD_SIZE = 23
_PREFIX = Struct(">B2s10sII")
_RECORD = Struct(">B2s10sIIH")


def _bytes(name: str, value: bytes, width: int) -> None:
    if not isinstance(value, bytes) or len(value) != width:
        raise ValueError(f"{name} must be exactly {width} bytes")


def _uint(name: str, value: int, bits: int) -> None:
    if not isinstance(value, int) or not 0 <= value < 2**bits:
        raise ValueError(f"{name} must be an unsigned {bits}-bit integer")


@dataclass(frozen=True, slots=True)
class ProcessingRecord:
    """One fixed C6.1-C6.6 modifying-system provenance record."""

    sequence_number: int
    modifying_nationality: bytes
    modifying_platform_id: bytes
    modifying_mission_id: int
    modifying_job_id: int
    processing_performed: int

    def __post_init__(self) -> None:
        _uint("sequence_number", self.sequence_number, 8)
        _bytes("modifying_nationality", self.modifying_nationality, 2)
        _bytes("modifying_platform_id", self.modifying_platform_id, 10)
        _uint("modifying_mission_id", self.modifying_mission_id, 32)
        _uint("modifying_job_id", self.modifying_job_id, 32)
        _uint("processing_performed", self.processing_performed, 16)

    def to_bytes(self) -> bytes:
        return _RECORD.pack(
            self.sequence_number,
            self.modifying_nationality,
            self.modifying_platform_id,
            self.modifying_mission_id,
            self.modifying_job_id,
            self.processing_performed,
        )


@dataclass(frozen=True, slots=True)
class ProcessingHistorySegment:
    """Original dataset identity plus one or more processing records."""

    based_on_nationality: bytes
    based_on_platform_id: bytes
    based_on_mission_id: int
    based_on_job_id: int
    records: tuple[ProcessingRecord, ...]

    def __post_init__(self) -> None:
        _bytes("based_on_nationality", self.based_on_nationality, 2)
        _bytes("based_on_platform_id", self.based_on_platform_id, 10)
        _uint("based_on_mission_id", self.based_on_mission_id, 32)
        _uint("based_on_job_id", self.based_on_job_id, 32)
        if not 1 <= len(self.records) <= 255:
            raise ValueError("records must contain between 1 and 255 entries")
        if not all(isinstance(record, ProcessingRecord) for record in self.records):
            raise ValueError("records must contain ProcessingRecord values")

    @property
    def processing_history_count(self) -> int:
        return len(self.records)

    def to_segment(self) -> Segment:
        """Encode C1-C6 without altering identifiers or processing flags."""

        payload = _PREFIX.pack(
            self.processing_history_count,
            self.based_on_nationality,
            self.based_on_platform_id,
            self.based_on_mission_id,
            self.based_on_job_id,
        )
        payload += b"".join(record.to_bytes() for record in self.records)
        return Segment(PROCESSING_HISTORY_SEGMENT_TYPE, payload)


def decode_processing_history_segment(segment: Segment) -> ProcessingHistorySegment:
    """Decode a complete type-12 Processing History Segment."""

    if segment.segment_type != PROCESSING_HISTORY_SEGMENT_TYPE:
        raise DecodeError(
            f"processing history decoder requires type {PROCESSING_HISTORY_SEGMENT_TYPE}, "
            f"received {segment.segment_type}"
        )
    if len(segment.payload) < PROCESSING_HISTORY_PREFIX_SIZE:
        raise DecodeError(
            f"processing history payload requires at least {PROCESSING_HISTORY_PREFIX_SIZE} bytes"
        )
    count, nationality, platform_id, mission_id, job_id = _PREFIX.unpack_from(segment.payload)
    if count == 0:
        raise DecodeError("processing history count must be between 1 and 255")
    expected = PROCESSING_HISTORY_PREFIX_SIZE + count * PROCESSING_RECORD_SIZE
    if len(segment.payload) != expected:
        raise DecodeError(
            f"processing history payload size must be {expected} bytes for {count} records, "
            f"received {len(segment.payload)}"
        )
    records = tuple(
        ProcessingRecord(*_RECORD.unpack_from(segment.payload, offset))
        for offset in range(PROCESSING_HISTORY_PREFIX_SIZE, expected, PROCESSING_RECORD_SIZE)
    )
    return ProcessingHistorySegment(nationality, platform_id, mission_id, job_id, records)
