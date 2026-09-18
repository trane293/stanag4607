"""Recommended Chapter 4 Job Request and Job Acknowledge segments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from struct import Struct

from .angles import BinaryAngle, SignedBinaryAngle
from .errors import DecodeError
from .packet import Segment

JOB_REQUEST_SEGMENT_TYPE = 101
JOB_ACKNOWLEDGE_SEGMENT_TYPE = 102
TASKING_PAYLOAD_SIZE = 79
_REQUEST_PREFIX = Struct(">10s10sB")
_REQUEST_TAIL = Struct(">BHHHBBBBBHHHB6sB")
_ACK_PREFIX = Struct(">I10s10sB6sB")
_ACK_TAIL = Struct(">BHHBHBBBBB2s")


def _uint(name: str, value: int, bits: int) -> None:
    if not isinstance(value, int) or not 0 <= value < 2**bits:
        raise ValueError(f"{name} must be an unsigned {bits}-bit integer")


def _validate_bytes(name: str, value: bytes, width: int) -> None:
    if not isinstance(value, bytes) or len(value) != width:
        raise ValueError(f"{name} must be exactly {width} bytes")


def _validate_area(
    bounding_area: tuple[tuple[SignedBinaryAngle, BinaryAngle], ...],
) -> None:
    if len(bounding_area) != 4:
        raise ValueError("bounding_area must contain exactly four points")
    for latitude, longitude in bounding_area:
        if latitude.bits != 32 or longitude.bits != 32:
            raise ValueError("bounding_area coordinates must be SA32/BA32 values")


def _area_bytes(
    bounding_area: tuple[tuple[SignedBinaryAngle, BinaryAngle], ...],
) -> bytes:
    return b"".join(
        latitude.to_bytes() + longitude.to_bytes()
        for latitude, longitude in bounding_area
    )


def _decode_area(
    payload: bytes, offset: int
) -> tuple[tuple[tuple[SignedBinaryAngle, BinaryAngle], ...], int]:
    points: list[tuple[SignedBinaryAngle, BinaryAngle]] = []
    for _ in range(4):
        points.append(
            (
                SignedBinaryAngle.from_bytes(payload[offset : offset + 4]),
                BinaryAngle.from_bytes(payload[offset + 4 : offset + 8]),
            )
        )
        offset += 8
    return tuple(points), offset


def _utc_datetime(fields: tuple[int, int, int, int, int, int]) -> datetime | None:
    year, month, day, hour, minute, second = fields
    if second == 60:
        return None
    try:
        return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class JobRequestSegment:
    """All mandatory R1-R26 values from the recommended type-101 segment."""

    requestor_id: bytes
    requestor_task_id: bytes
    priority: int
    bounding_area: tuple[tuple[SignedBinaryAngle, BinaryAngle], ...]
    radar_mode: int
    range_resolution_centimeters: int
    cross_range_resolution_decimeters: int
    earliest_start_year: int
    earliest_start_month: int
    earliest_start_day: int
    earliest_start_hour: int
    earliest_start_minute: int
    earliest_start_second: int
    allowed_delay_seconds: int
    duration_seconds: int
    revisit_interval_deciseconds: int
    sensor_type: int
    sensor_model: bytes
    request_type: int

    def __post_init__(self) -> None:
        _validate_bytes("requestor_id", self.requestor_id, 10)
        _validate_bytes("requestor_task_id", self.requestor_task_id, 10)
        _validate_bytes("sensor_model", self.sensor_model, 6)
        _validate_area(self.bounding_area)
        for name, value, bits in (
            ("priority", self.priority, 8),
            ("radar_mode", self.radar_mode, 8),
            ("range_resolution_centimeters", self.range_resolution_centimeters, 16),
            (
                "cross_range_resolution_decimeters",
                self.cross_range_resolution_decimeters,
                16,
            ),
            ("earliest_start_year", self.earliest_start_year, 16),
            ("earliest_start_month", self.earliest_start_month, 8),
            ("earliest_start_day", self.earliest_start_day, 8),
            ("earliest_start_hour", self.earliest_start_hour, 8),
            ("earliest_start_minute", self.earliest_start_minute, 8),
            ("earliest_start_second", self.earliest_start_second, 8),
            ("allowed_delay_seconds", self.allowed_delay_seconds, 16),
            ("duration_seconds", self.duration_seconds, 16),
            ("revisit_interval_deciseconds", self.revisit_interval_deciseconds, 16),
            ("sensor_type", self.sensor_type, 8),
            ("request_type", self.request_type, 8),
        ):
            _uint(name, value, bits)

    @property
    def earliest_start_fields(self) -> tuple[int, int, int, int, int, int]:
        return (
            self.earliest_start_year,
            self.earliest_start_month,
            self.earliest_start_day,
            self.earliest_start_hour,
            self.earliest_start_minute,
            self.earliest_start_second,
        )

    @property
    def earliest_start_utc(self) -> datetime | None:
        """Return an ordinary UTC datetime, or ``None`` for leap/invalid components."""

        return _utc_datetime(self.earliest_start_fields)

    def to_segment(self) -> Segment:
        payload = _REQUEST_PREFIX.pack(
            self.requestor_id, self.requestor_task_id, self.priority
        )
        payload += _area_bytes(self.bounding_area)
        payload += _REQUEST_TAIL.pack(
            self.radar_mode,
            self.range_resolution_centimeters,
            self.cross_range_resolution_decimeters,
            self.earliest_start_year,
            self.earliest_start_month,
            self.earliest_start_day,
            self.earliest_start_hour,
            self.earliest_start_minute,
            self.earliest_start_second,
            self.allowed_delay_seconds,
            self.duration_seconds,
            self.revisit_interval_deciseconds,
            self.sensor_type,
            self.sensor_model,
            self.request_type,
        )
        return Segment(JOB_REQUEST_SEGMENT_TYPE, payload)


@dataclass(frozen=True, slots=True)
class JobAcknowledgeSegment:
    """All mandatory A1-A25 values from the recommended type-102 segment."""

    job_id: int
    requestor_id: bytes
    requestor_task_id: bytes
    sensor_type: int
    sensor_model: bytes
    priority: int
    bounding_area: tuple[tuple[SignedBinaryAngle, BinaryAngle], ...]
    radar_mode: int
    duration_seconds: int
    revisit_interval_deciseconds: int
    request_status: int
    start_year: int
    start_month: int
    start_day: int
    start_hour: int
    start_minute: int
    start_second: int
    requestor_nationality: bytes

    def __post_init__(self) -> None:
        _validate_bytes("requestor_id", self.requestor_id, 10)
        _validate_bytes("requestor_task_id", self.requestor_task_id, 10)
        _validate_bytes("sensor_model", self.sensor_model, 6)
        _validate_bytes("requestor_nationality", self.requestor_nationality, 2)
        _validate_area(self.bounding_area)
        for name, value, bits in (
            ("job_id", self.job_id, 32),
            ("sensor_type", self.sensor_type, 8),
            ("priority", self.priority, 8),
            ("radar_mode", self.radar_mode, 8),
            ("duration_seconds", self.duration_seconds, 16),
            ("revisit_interval_deciseconds", self.revisit_interval_deciseconds, 16),
            ("request_status", self.request_status, 8),
            ("start_year", self.start_year, 16),
            ("start_month", self.start_month, 8),
            ("start_day", self.start_day, 8),
            ("start_hour", self.start_hour, 8),
            ("start_minute", self.start_minute, 8),
            ("start_second", self.start_second, 8),
        ):
            _uint(name, value, bits)

    @property
    def start_time_fields(self) -> tuple[int, int, int, int, int, int]:
        return (
            self.start_year,
            self.start_month,
            self.start_day,
            self.start_hour,
            self.start_minute,
            self.start_second,
        )

    @property
    def start_time_utc(self) -> datetime | None:
        """Return an ordinary UTC datetime, or ``None`` for leap/invalid components."""

        return _utc_datetime(self.start_time_fields)

    def to_segment(self) -> Segment:
        payload = _ACK_PREFIX.pack(
            self.job_id,
            self.requestor_id,
            self.requestor_task_id,
            self.sensor_type,
            self.sensor_model,
            self.priority,
        )
        payload += _area_bytes(self.bounding_area)
        payload += _ACK_TAIL.pack(
            self.radar_mode,
            self.duration_seconds,
            self.revisit_interval_deciseconds,
            self.request_status,
            self.start_year,
            self.start_month,
            self.start_day,
            self.start_hour,
            self.start_minute,
            self.start_second,
            self.requestor_nationality,
        )
        return Segment(JOB_ACKNOWLEDGE_SEGMENT_TYPE, payload)


def _require_payload(segment: Segment, segment_type: int, name: str) -> None:
    if segment.segment_type != segment_type:
        raise DecodeError(
            f"{name} decoder requires segment type {segment_type}, "
            f"received {segment.segment_type}"
        )
    if len(segment.payload) != TASKING_PAYLOAD_SIZE:
        raise DecodeError(
            f"{name} payload must be exactly {TASKING_PAYLOAD_SIZE} bytes, "
            f"received {len(segment.payload)}"
        )


def decode_job_request_segment(segment: Segment) -> JobRequestSegment:
    """Decode one complete type-101 Job Request payload."""

    _require_payload(segment, JOB_REQUEST_SEGMENT_TYPE, "job request")
    prefix = _REQUEST_PREFIX.unpack_from(segment.payload)
    area, offset = _decode_area(segment.payload, _REQUEST_PREFIX.size)
    tail = _REQUEST_TAIL.unpack_from(segment.payload, offset)
    return JobRequestSegment(
        prefix[0], prefix[1], prefix[2], area, *tail
    )


def decode_job_acknowledge_segment(segment: Segment) -> JobAcknowledgeSegment:
    """Decode one complete type-102 Job Acknowledge payload."""

    _require_payload(segment, JOB_ACKNOWLEDGE_SEGMENT_TYPE, "job acknowledge")
    prefix = _ACK_PREFIX.unpack_from(segment.payload)
    area, offset = _decode_area(segment.payload, _ACK_PREFIX.size)
    tail = _ACK_TAIL.unpack_from(segment.payload, offset)
    return JobAcknowledgeSegment(
        job_id=prefix[0],
        requestor_id=prefix[1],
        requestor_task_id=prefix[2],
        sensor_type=prefix[3],
        sensor_model=prefix[4],
        priority=prefix[5],
        bounding_area=area,
        radar_mode=tail[0],
        duration_seconds=tail[1],
        revisit_interval_deciseconds=tail[2],
        request_status=tail[3],
        start_year=tail[4],
        start_month=tail[5],
        start_day=tail[6],
        start_hour=tail[7],
        start_minute=tail[8],
        start_second=tail[9],
        requestor_nationality=tail[10],
    )
