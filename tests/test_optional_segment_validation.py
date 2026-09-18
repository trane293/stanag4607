"""AEDP-4607 Ed A V1 sections 3.14-3.15 validation."""

from dataclasses import replace

from stanag4607 import (
    Segment,
    decode_platform_location_segment,
    decode_processing_history_segment,
    validate_platform_location,
    validate_processing_history,
)

PLATFORM_LOCATION_PAYLOAD = bytes.fromhex(
    "01 d2 eb 40 51 81 ef 29 11 94 23 80 00 0c f8 50 41 11 00 01 d4 c0 fe"
)
PROCESSING_PAYLOAD = bytes.fromhex(
    "02 43 41 52 41 44 41 52 2d 30 31 20 20 00 00 00 2a 00 00 00 4d"
    "01 55 53 41 49 2d 4e 4f 44 45 20 20 20 00 00 00 64 00 00 00 65 00 82"
    "02 47 42 41 49 2d 4e 4f 44 45 20 20 20 00 00 00 66 00 00 00 67 02 01"
)


def test_valid_optional_segment_vectors_have_no_issues() -> None:
    location = decode_platform_location_segment(Segment(13, PLATFORM_LOCATION_PAYLOAD))
    history = decode_processing_history_segment(Segment(12, PROCESSING_PAYLOAD))

    assert validate_platform_location(location) == ()
    assert validate_processing_history(history) == ()


def test_platform_location_numeric_ranges_are_reported() -> None:
    location = decode_platform_location_segment(Segment(13, PLATFORM_LOCATION_PAYLOAD))
    location = replace(
        location,
        location_time_milliseconds=4_000_000_001,
        altitude_centimeters=-50_001,
        speed_millimeters_per_second=8_000_001,
    )

    assert {issue.code for issue in validate_platform_location(location)} == {
        "platform_location.time_range",
        "platform_location.altitude_range",
        "platform_location.speed_range",
    }


def test_processing_history_identity_sequence_and_reserved_bits_are_reported() -> None:
    history = decode_processing_history_segment(Segment(12, PROCESSING_PAYLOAD))
    first = replace(
        history.records[0],
        sequence_number=2,
        modifying_job_id=0,
        processing_performed=0xC000,
    )
    history = replace(history, based_on_job_id=0, records=(first, history.records[1]))

    assert {issue.code for issue in validate_processing_history(history)} == {
        "processing_history.based_on_job_id_range",
        "processing_history.sequence",
        "processing_history.modifying_job_id_range",
        "processing_history.reserved_bits",
    }
