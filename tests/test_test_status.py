"""AEDP-4607 Ed A V1 section 3.12 and Table 3-20 tests."""

import pytest

from stanag4607 import (
    DecodeError,
    Segment,
    decode_test_status_segment,
    decode_typed_segment,
    validate_test_status,
)
from stanag4607 import TestStatusSegment as StatusSegment


def _segment(*, hardware_status: int = 0xA8, mode_status: int = 0x50) -> Segment:
    payload = (
        (0x01020304).to_bytes(4, "big")
        + (7).to_bytes(2, "big")
        + (8).to_bytes(2, "big")
        + (123_456).to_bytes(4, "big")
        + bytes((hardware_status, mode_status))
    )
    return Segment(10, payload)


def test_decode_exposes_named_health_failures_and_round_trips() -> None:
    segment = _segment()

    status = decode_test_status_segment(segment)

    assert status.job_id == 0x01020304
    assert status.revisit_index == 7
    assert status.dwell_index == 8
    assert status.dwell_time_milliseconds == 123_456
    assert status.failed_hardware == (
        "antenna",
        "processor",
        "calibration_mode",
    )
    assert status.exceeded_mode_limits == ("azimuth", "temperature")
    assert status.to_segment() == segment
    assert decode_typed_segment(segment) == status


@pytest.mark.parametrize("size", [13, 15])
def test_decode_rejects_wrong_payload_size(size: int) -> None:
    with pytest.raises(DecodeError, match="exactly 14 bytes"):
        decode_test_status_segment(Segment(10, bytes(size)))


def test_decode_rejects_wrong_segment_type() -> None:
    with pytest.raises(DecodeError, match="requires type 10"):
        decode_test_status_segment(Segment(11, bytes(14)))


def test_constructor_rejects_values_outside_wire_widths() -> None:
    with pytest.raises(ValueError, match="hardware_status"):
        StatusSegment(1, 0, 0, 0, 256, 0)


def test_validation_reports_time_and_reserved_status_bits() -> None:
    status = StatusSegment(
        job_id=1,
        revisit_index=0,
        dwell_index=0,
        dwell_time_milliseconds=4_000_000_001,
        hardware_status=0x07,
        mode_status=0x0F,
    )

    assert {issue.code for issue in validate_test_status(status)} == {
        "test_status.hardware_reserved_bits",
        "test_status.mode_reserved_bits",
        "test_status.time_range",
    }


def test_zero_indexes_are_not_rejected_due_to_normative_guide_conflict() -> None:
    status = StatusSegment(0, 0, 0, 0, 0, 0)

    assert validate_test_status(status) == ()
