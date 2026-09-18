"""AEDP-4607 Ed A V1 section 3.7 and Table 3-14 validation."""

from dataclasses import replace

import pytest

from stanag4607 import (
    JobDefinitionSegment,
    Segment,
    decode_job_definition_segment,
    validate_job_definition,
)

JOB_PAYLOAD = bytes.fromhex(
    "00 00 00 4d c8 53 59 4e 52 44 52 01 14"
    "51 eb 85 1f 11 23 45 68"
    "51 eb 85 1f 11 d9 50 c8"
    "50 7f 6e 5d 11 d9 50 c8"
    "50 7f 6e 5d 11 23 45 68"
    "01 01 2c ff ff ff ff ff ff ff ff ff ff ff"
    "80 00 ff ff ff ff ff 01 01"
)


def _job() -> JobDefinitionSegment:
    return decode_job_definition_segment(Segment(5, JOB_PAYLOAD))


def test_public_job_fixture_has_no_conformance_issues() -> None:
    assert validate_job_definition(_job()) == ()


@pytest.mark.parametrize(
    ("changes", "expected_code"),
    [
        ({"job_id": 0}, "job.id_range"),
        ({"target_filtering": 0x08}, "job.target_filtering_reserved_bits"),
        ({"priority": 0}, "job.priority_range"),
        ({"priority": 100}, "job.priority_range"),
        (
            {"nominal_sensor_position_along_track_uncertainty_raw": 10_001},
            "job.sensor_position_uncertainty_range",
        ),
        (
            {"nominal_sensor_position_cross_track_uncertainty_raw": 10_001},
            "job.sensor_position_uncertainty_range",
        ),
        (
            {"nominal_sensor_position_altitude_uncertainty_raw": 20_001},
            "job.sensor_altitude_uncertainty_range",
        ),
        ({"nominal_sensor_track_uncertainty_raw": 46}, "job.sensor_track_uncertainty_range"),
        (
            {"nominal_radial_velocity_standard_deviation_raw": 5_001},
            "job.radial_velocity_uncertainty_range",
        ),
        ({"nominal_detection_probability_raw": 101}, "job.detection_probability_range"),
    ],
)
def test_invalid_job_values_are_reported_without_mutating_wire_data(
    changes: dict[str, int], expected_code: str
) -> None:
    job = replace(_job(), **changes)
    encoded = job.to_segment().payload

    issues = validate_job_definition(job)

    assert expected_code in {issue.code for issue in issues}
    assert job.to_segment().payload == encoded


def test_no_statement_sentinels_are_not_range_errors() -> None:
    job = replace(
        _job(),
        nominal_sensor_position_along_track_uncertainty_raw=0xFFFF,
        nominal_sensor_position_cross_track_uncertainty_raw=0xFFFF,
        nominal_sensor_position_altitude_uncertainty_raw=0xFFFF,
        nominal_sensor_track_uncertainty_raw=0xFF,
        nominal_radial_velocity_standard_deviation_raw=0xFFFF,
        nominal_detection_probability_raw=0xFF,
    )

    assert validate_job_definition(job) == ()
