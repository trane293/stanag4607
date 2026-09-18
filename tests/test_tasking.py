"""AEDP-4607 Ed A V1 Chapter 4 and Tables 4-1/4-2 tasking segments."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone

import pytest
from hypothesis import given
from hypothesis import strategies as st

from stanag4607 import (
    BinaryAngle,
    DecodeError,
    JobAcknowledgeSegment,
    JobRequestSegment,
    Segment,
    SignedBinaryAngle,
    decode_job_acknowledge_segment,
    decode_job_request_segment,
    decode_typed_segment,
)

AREA = bytes.fromhex(
    "20 00 00 00 10 00 00 00"
    "20 00 00 00 20 00 00 00"
    "10 00 00 00 20 00 00 00"
    "10 00 00 00 10 00 00 00"
)
REQUEST_PAYLOAD = (
    b"OPS-ALPHA "
    b"TASK-0001 "
    b"\x05"
    + AREA
    + bytes.fromhex(
        "03 00 64 00 14 07 ea 09 0c 0e 1e 2d 00 78 01 2c 00 32 2a 52 44 52 2d 31 20 00"
    )
)
ACK_PAYLOAD = (
    bytes.fromhex("00 00 00 4d")
    + b"OPS-ALPHA "
    + b"TASK-0001 "
    + b"\x2aRDR-1 \x07"
    + AREA
    + bytes.fromhex("03 01 2c 00 32 02 07 ea 09 0c 0e 20 0f")
    + b"CA"
)


def test_job_request_decodes_all_fields_and_round_trips() -> None:
    request = decode_job_request_segment(Segment(101, REQUEST_PAYLOAD))

    assert isinstance(request, JobRequestSegment)
    assert request.requestor_id == b"OPS-ALPHA "
    assert request.requestor_task_id == b"TASK-0001 "
    assert request.priority == 5
    assert request.bounding_area[0] == (
        SignedBinaryAngle(0x20000000, 32),
        BinaryAngle(0x10000000, 32),
    )
    assert request.radar_mode == 3
    assert request.range_resolution_centimeters == 100
    assert request.cross_range_resolution_decimeters == 20
    assert request.earliest_start_fields == (2026, 9, 12, 14, 30, 45)
    assert request.earliest_start_utc == datetime(
        2026, 9, 12, 14, 30, 45, tzinfo=timezone.utc
    )
    assert request.allowed_delay_seconds == 120
    assert request.duration_seconds == 300
    assert request.revisit_interval_deciseconds == 50
    assert request.sensor_type == 42
    assert request.sensor_model == b"RDR-1 "
    assert request.request_type == 0
    assert request.to_segment() == Segment(101, REQUEST_PAYLOAD)
    assert decode_typed_segment(request.to_segment()) == request


def test_job_acknowledge_decodes_all_fields_and_round_trips() -> None:
    acknowledge = decode_job_acknowledge_segment(Segment(102, ACK_PAYLOAD))

    assert isinstance(acknowledge, JobAcknowledgeSegment)
    assert acknowledge.job_id == 77
    assert acknowledge.requestor_id == b"OPS-ALPHA "
    assert acknowledge.requestor_task_id == b"TASK-0001 "
    assert acknowledge.sensor_type == 42
    assert acknowledge.sensor_model == b"RDR-1 "
    assert acknowledge.priority == 7
    assert acknowledge.bounding_area[-1] == (
        SignedBinaryAngle(0x10000000, 32),
        BinaryAngle(0x10000000, 32),
    )
    assert acknowledge.radar_mode == 3
    assert acknowledge.duration_seconds == 300
    assert acknowledge.revisit_interval_deciseconds == 50
    assert acknowledge.request_status == 2
    assert acknowledge.start_time_fields == (2026, 9, 12, 14, 32, 15)
    assert acknowledge.start_time_utc == datetime(
        2026, 9, 12, 14, 32, 15, tzinfo=timezone.utc
    )
    assert acknowledge.requestor_nationality == b"CA"
    assert acknowledge.to_segment() == Segment(102, ACK_PAYLOAD)
    assert decode_typed_segment(acknowledge.to_segment()) == acknowledge


@pytest.mark.parametrize(
    ("decoder", "segment_type", "payload"),
    [
        (decode_job_request_segment, 101, REQUEST_PAYLOAD),
        (decode_job_acknowledge_segment, 102, ACK_PAYLOAD),
    ],
)
def test_tasking_segments_require_exact_type_and_79_byte_payload(
    decoder: Callable[[Segment], object], segment_type: int, payload: bytes
) -> None:
    with pytest.raises(DecodeError, match="79 bytes"):
        decoder(Segment(segment_type, payload[:-1]))
    with pytest.raises(DecodeError, match=f"type {segment_type}"):
        decoder(Segment(1, payload))


def test_tasking_models_reject_invalid_wire_shapes() -> None:
    request = decode_job_request_segment(Segment(101, REQUEST_PAYLOAD))
    acknowledge = decode_job_acknowledge_segment(Segment(102, ACK_PAYLOAD))

    with pytest.raises(ValueError, match="requestor_id"):
        replace(request, requestor_id=b"short")
    with pytest.raises(ValueError, match="four points"):
        replace(request, bounding_area=request.bounding_area[:3])
    with pytest.raises(ValueError, match="request_type"):
        replace(request, request_type=256)
    with pytest.raises(ValueError, match="nationality"):
        replace(acknowledge, requestor_nationality=b"C")


def test_leap_second_components_remain_exact_without_invalid_datetime() -> None:
    request = decode_job_request_segment(Segment(101, REQUEST_PAYLOAD))
    acknowledge = decode_job_acknowledge_segment(Segment(102, ACK_PAYLOAD))

    request = replace(request, earliest_start_second=60)
    acknowledge = replace(acknowledge, start_second=60)

    assert request.earliest_start_fields[-1] == 60
    assert request.earliest_start_utc is None
    assert acknowledge.start_time_fields[-1] == 60
    assert acknowledge.start_time_utc is None


@given(st.binary(min_size=79, max_size=79))
def test_every_fixed_width_job_request_payload_round_trips_losslessly(
    payload: bytes,
) -> None:
    # Tables 4-1 and 4-2 define only fixed-width wire fields. Semantic invalidity is
    # reported separately and must not prevent exact preservation.
    segment = Segment(101, payload)

    assert decode_job_request_segment(segment).to_segment() == segment


@given(st.binary(min_size=79, max_size=79))
def test_every_fixed_width_job_acknowledge_payload_round_trips_losslessly(
    payload: bytes,
) -> None:
    segment = Segment(102, payload)

    assert decode_job_acknowledge_segment(segment).to_segment() == segment
