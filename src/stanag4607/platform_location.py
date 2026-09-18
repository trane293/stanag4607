"""Typed Platform Location Segment support."""

from __future__ import annotations

from dataclasses import dataclass
from struct import Struct

from .angles import BinaryAngle, SignedBinaryAngle
from .errors import DecodeError
from .packet import Segment

PLATFORM_LOCATION_SEGMENT_TYPE = 13
PLATFORM_LOCATION_PAYLOAD_SIZE = 23
_PLATFORM_LOCATION = Struct(">IiIiHIb")


def _uint(name: str, value: int, bits: int) -> None:
    if not isinstance(value, int) or not 0 <= value < 2**bits:
        raise ValueError(f"{name} must be an unsigned {bits}-bit integer")


@dataclass(frozen=True, slots=True)
class PlatformLocationSegment:
    """Platform position and motion fields L1-L7."""

    location_time_milliseconds: int
    latitude: SignedBinaryAngle
    longitude: BinaryAngle
    altitude_centimeters: int
    track: BinaryAngle
    speed_millimeters_per_second: int
    vertical_velocity_decimeters_per_second: int

    def __post_init__(self) -> None:
        _uint("location_time_milliseconds", self.location_time_milliseconds, 32)
        if self.latitude.bits != 32:
            raise ValueError("latitude must be an SA32 value")
        if self.longitude.bits != 32:
            raise ValueError("longitude must be a BA32 value")
        if not -(2**31) <= self.altitude_centimeters < 2**31:
            raise ValueError("altitude_centimeters must be a signed 32-bit integer")
        if self.track.bits != 16:
            raise ValueError("track must be a BA16 value")
        _uint("speed_millimeters_per_second", self.speed_millimeters_per_second, 32)
        if not -128 <= self.vertical_velocity_decimeters_per_second <= 127:
            raise ValueError(
                "vertical_velocity_decimeters_per_second must be a signed 8-bit integer"
            )

    def to_segment(self) -> Segment:
        """Encode L1-L7 as an exact type-13 segment."""

        payload = _PLATFORM_LOCATION.pack(
            self.location_time_milliseconds,
            self.latitude.raw,
            self.longitude.raw,
            self.altitude_centimeters,
            self.track.raw,
            self.speed_millimeters_per_second,
            self.vertical_velocity_decimeters_per_second,
        )
        return Segment(PLATFORM_LOCATION_SEGMENT_TYPE, payload)


def decode_platform_location_segment(segment: Segment) -> PlatformLocationSegment:
    """Decode a complete type-13 Platform Location Segment."""

    if segment.segment_type != PLATFORM_LOCATION_SEGMENT_TYPE:
        raise DecodeError(
            f"platform location decoder requires type {PLATFORM_LOCATION_SEGMENT_TYPE}, "
            f"received {segment.segment_type}"
        )
    if len(segment.payload) != PLATFORM_LOCATION_PAYLOAD_SIZE:
        raise DecodeError(
            f"platform location payload must be exactly {PLATFORM_LOCATION_PAYLOAD_SIZE} bytes, "
            f"received {len(segment.payload)}"
        )
    time, latitude, longitude, altitude, track, speed, vertical_velocity = (
        _PLATFORM_LOCATION.unpack(segment.payload)
    )
    return PlatformLocationSegment(
        location_time_milliseconds=time,
        latitude=SignedBinaryAngle(latitude, 32),
        longitude=BinaryAngle(longitude, 32),
        altitude_centimeters=altitude,
        track=BinaryAngle(track, 16),
        speed_millimeters_per_second=speed,
        vertical_velocity_decimeters_per_second=vertical_velocity,
    )
