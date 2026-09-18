"""AEDP-4607 Ed A V1 Tables 4-1/4-2 software-verifiable tasking rules."""

from __future__ import annotations

from dataclasses import replace

from test_tasking import ACK_PAYLOAD, REQUEST_PAYLOAD

from stanag4607 import (
    Segment,
    decode_job_acknowledge_segment,
    decode_job_request_segment,
    validate_job_acknowledge,
    validate_job_request,
)


def test_normative_derived_tasking_vectors_are_valid() -> None:
    request = decode_job_request_segment(Segment(101, REQUEST_PAYLOAD))
    acknowledge = decode_job_acknowledge_segment(Segment(102, ACK_PAYLOAD))

    assert validate_job_request(request) == ()
    assert validate_job_acknowledge(acknowledge) == ()


def test_job_request_ranges_flags_and_characters_are_reported_together() -> None:
    request = decode_job_request_segment(Segment(101, REQUEST_PAYLOAD))
    invalid = replace(
        request,
        requestor_id=b"OPS\x00ALPHA ",
        priority=100,
        earliest_start_year=1999,
        earliest_start_month=13,
        earliest_start_day=0,
        earliest_start_hour=24,
        earliest_start_minute=60,
        earliest_start_second=61,
        request_type=2,
    )

    assert {issue.code for issue in validate_job_request(invalid)} == {
        "job_request.invalid_bcs",
        "job_request.priority_range",
        "job_request.start_date_range",
        "job_request.start_time_range",
        "job_request.request_type",
    }


def test_job_acknowledge_ranges_status_and_characters_are_reported_together() -> None:
    acknowledge = decode_job_acknowledge_segment(Segment(102, ACK_PAYLOAD))
    invalid = replace(
        acknowledge,
        job_id=0,
        sensor_model=b"BAD\x00  ",
        priority=0,
        request_status=11,
        start_year=2100,
        start_month=0,
        start_day=32,
        start_hour=24,
        start_minute=60,
        start_second=61,
    )

    assert {issue.code for issue in validate_job_acknowledge(invalid)} == {
        "job_acknowledge.invalid_bcs",
        "job_acknowledge.job_id_required",
        "job_acknowledge.priority_range",
        "job_acknowledge.request_status",
        "job_acknowledge.start_date_range",
        "job_acknowledge.start_time_range",
    }


def test_impossible_calendar_dates_are_reported() -> None:
    request = decode_job_request_segment(Segment(101, REQUEST_PAYLOAD))
    acknowledge = decode_job_acknowledge_segment(Segment(102, ACK_PAYLOAD))

    request = replace(request, earliest_start_month=2, earliest_start_day=30)
    acknowledge = replace(acknowledge, start_month=2, start_day=30)

    assert {issue.code for issue in validate_job_request(request)} == {
        "job_request.start_date_range"
    }
    assert {issue.code for issue in validate_job_acknowledge(acknowledge)} == {
        "job_acknowledge.start_date_range"
    }
