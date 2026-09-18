"""AEDP-4607 Ed A V1 section 3.15 and Table 3-24."""

from dataclasses import replace

import pytest

from stanag4607 import (
    BinaryAngle,
    DecodeError,
    PlatformLocationSegment,
    Segment,
    SignedBinaryAngle,
    decode_platform_location_segment,
    decode_typed_segment,
)

PLATFORM_LOCATION_PAYLOAD = bytes.fromhex(
    "01 d2 eb 40 51 81 ef 29 11 94 23 80 00 0c f8 50 41 11 00 01 d4 c0 fe"
)


def test_platform_location_decodes_exact_motion_and_round_trips() -> None:
    location = decode_platform_location_segment(Segment(13, PLATFORM_LOCATION_PAYLOAD))

    assert location == PlatformLocationSegment(
        location_time_milliseconds=30_600_000,
        latitude=SignedBinaryAngle(
            int.from_bytes(bytes.fromhex("51 81 ef 29"), "big", signed=True), 32
        ),
        longitude=BinaryAngle(0x11942380, 32),
        altitude_centimeters=850_000,
        track=BinaryAngle(0x4111, 16),
        speed_millimeters_per_second=120_000,
        vertical_velocity_decimeters_per_second=-2,
    )
    assert location.to_segment() == Segment(13, PLATFORM_LOCATION_PAYLOAD)
    assert isinstance(
        decode_typed_segment(Segment(13, PLATFORM_LOCATION_PAYLOAD)),
        PlatformLocationSegment,
    )


@pytest.mark.parametrize("length", [0, 1, 22, 24])
def test_platform_location_requires_exactly_23_bytes(length: int) -> None:
    with pytest.raises(DecodeError, match="23 bytes"):
        decode_platform_location_segment(
            Segment(13, (PLATFORM_LOCATION_PAYLOAD + b"x")[:length])
        )


def test_platform_location_rejects_wrong_type() -> None:
    with pytest.raises(DecodeError, match="type 13"):
        decode_platform_location_segment(Segment(2, PLATFORM_LOCATION_PAYLOAD))


def test_platform_location_model_rejects_wrong_angle_widths_and_wire_values() -> None:
    location = decode_platform_location_segment(Segment(13, PLATFORM_LOCATION_PAYLOAD))

    with pytest.raises(ValueError, match="latitude"):
        replace(location, latitude=SignedBinaryAngle(0, 16))
    with pytest.raises(ValueError, match="longitude"):
        replace(location, longitude=BinaryAngle(0, 16))
    with pytest.raises(ValueError, match="altitude"):
        replace(location, altitude_centimeters=2**31)
    with pytest.raises(ValueError, match="track"):
        replace(location, track=BinaryAngle(0, 32))
    with pytest.raises(ValueError, match="speed"):
        replace(location, speed_millimeters_per_second=2**32)
    with pytest.raises(ValueError, match="vertical_velocity"):
        replace(location, vertical_velocity_decimeters_per_second=128)
