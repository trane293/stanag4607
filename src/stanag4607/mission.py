"""Typed Mission Segment support."""

from __future__ import annotations

from dataclasses import dataclass
from struct import Struct

from .errors import DecodeError
from .packet import Segment

MISSION_SEGMENT_TYPE = 1
MISSION_PAYLOAD_SIZE = 39
_MISSION = Struct(">12s12sB10sHBB")


def _fixed_bytes(name: str, value: bytes, width: int) -> None:
    if not isinstance(value, bytes) or len(value) != width:
        raise ValueError(f"{name} must be exactly {width} bytes")


def _uint(name: str, value: int, bits: int) -> None:
    if not isinstance(value, int) or not 0 <= value < 2**bits:
        raise ValueError(f"{name} must be an unsigned {bits}-bit integer")


@dataclass(frozen=True, slots=True)
class MissionSegment:
    """Mission fields M1-M7, including the date basis for later observations."""

    mission_plan: bytes
    flight_plan: bytes
    platform_type: int
    platform_configuration: bytes
    reference_year: int
    reference_month: int
    reference_day: int

    def __post_init__(self) -> None:
        _fixed_bytes("mission_plan", self.mission_plan, 12)
        _fixed_bytes("flight_plan", self.flight_plan, 12)
        _uint("platform_type", self.platform_type, 8)
        _fixed_bytes("platform_configuration", self.platform_configuration, 10)
        _uint("reference_year", self.reference_year, 16)
        if not 1 <= self.reference_month <= 12:
            raise ValueError("reference_month must be in the range 1 through 12")
        if not 1 <= self.reference_day <= 31:
            raise ValueError("reference_day must be in the range 1 through 31")

    def to_segment(self) -> Segment:
        """Encode M1-M7 as a type-1 segment with exact character bytes."""

        payload = _MISSION.pack(
            self.mission_plan,
            self.flight_plan,
            self.platform_type,
            self.platform_configuration,
            self.reference_year,
            self.reference_month,
            self.reference_day,
        )
        return Segment(MISSION_SEGMENT_TYPE, payload)


def decode_mission_segment(segment: Segment) -> MissionSegment:
    """Decode a complete type-1 Mission Segment payload."""

    if segment.segment_type != MISSION_SEGMENT_TYPE:
        raise DecodeError(
            f"mission decoder requires segment type {MISSION_SEGMENT_TYPE}, "
            f"received {segment.segment_type}"
        )
    if len(segment.payload) != MISSION_PAYLOAD_SIZE:
        raise DecodeError(
            f"mission payload must be exactly {MISSION_PAYLOAD_SIZE} bytes, "
            f"received {len(segment.payload)}"
        )
    try:
        return MissionSegment(*_MISSION.unpack(segment.payload))
    except ValueError as error:
        raise DecodeError(f"invalid mission segment: {error}") from error

