"""AEDP-4607 Ed A V1 section 3.7 and Tables 3-14 through 3-18."""

from dataclasses import replace
from pathlib import Path

import pytest

from stanag4607 import (
    DecodeError,
    JobDefinitionSegment,
    Segment,
    SignedBinaryAngle,
    decode_job_definition_segment,
    decode_packet,
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


def test_decode_public_job_definition_fixture_with_exact_context() -> None:
    packet = decode_packet(
        (Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti").read_bytes()
    )
    segment = next(item for item in packet.segments if item.segment_type == 5)

    job = decode_job_definition_segment(segment)

    assert job.job_id == 77
    assert job.sensor_type == 200
    assert job.sensor_model == b"SYNRDR"
    assert job.target_filtering == 1
    assert job.priority == 20
    assert tuple((lat.raw, lon.raw) for lat, lon in job.bounding_area) == (
        (0x51EB851F, 0x11234568),
        (0x51EB851F, 0x11D950C8),
        (0x507F6E5D, 0x11D950C8),
        (0x507F6E5D, 0x11234568),
    )
    assert job.radar_mode == 1
    assert job.nominal_revisit_interval_deciseconds == 300
    assert job.nominal_sensor_position_along_track_uncertainty_decimeters is None
    assert job.nominal_sensor_position_cross_track_uncertainty_decimeters is None
    assert job.nominal_sensor_position_altitude_uncertainty_decimeters is None
    assert job.nominal_sensor_track_uncertainty_degrees is None
    assert job.nominal_sensor_speed_uncertainty_millimeters_per_second is None
    assert job.nominal_slant_range_standard_deviation_centimeters is None
    assert job.nominal_cross_range_standard_deviation is None
    assert job.nominal_radial_velocity_standard_deviation_centimeters_per_second is None
    assert job.nominal_minimum_detectable_velocity_decimeters_per_second is None
    assert job.nominal_detection_probability_percent is None
    assert job.nominal_false_alarm_density_negative_decibels is None
    assert job.terrain_elevation_model == 1
    assert job.geoid_model == 1
    assert job.to_segment() == segment


def test_job_definition_independent_payload_round_trips() -> None:
    job = decode_job_definition_segment(Segment(5, JOB_PAYLOAD))

    assert isinstance(job, JobDefinitionSegment)
    assert job.to_segment().payload == JOB_PAYLOAD


@pytest.mark.parametrize("length", [0, 1, 67, 69])
def test_job_definition_requires_exactly_68_payload_bytes(length: int) -> None:
    with pytest.raises(DecodeError, match="68 bytes"):
        decode_job_definition_segment(Segment(5, (JOB_PAYLOAD + b"x")[:length]))


def test_job_definition_rejects_wrong_segment_type() -> None:
    with pytest.raises(DecodeError, match="type 5"):
        decode_job_definition_segment(Segment(2, JOB_PAYLOAD))


def test_job_nominal_values_distinguish_measurements_from_no_statement() -> None:
    job = decode_job_definition_segment(Segment(5, JOB_PAYLOAD))
    measured = replace(
        job,
        nominal_sensor_position_along_track_uncertainty_raw=10,
        nominal_sensor_position_cross_track_uncertainty_raw=20,
        nominal_sensor_position_altitude_uncertainty_raw=30,
        nominal_sensor_track_uncertainty_raw=4,
        nominal_sensor_speed_uncertainty_raw=50,
        nominal_slant_range_standard_deviation_raw=60,
        nominal_cross_range_standard_deviation_raw=0x1234,
        nominal_radial_velocity_standard_deviation_raw=70,
        nominal_minimum_detectable_velocity_raw=8,
        nominal_detection_probability_raw=90,
        nominal_false_alarm_density_raw=100,
    )

    assert measured.nominal_sensor_position_along_track_uncertainty_decimeters == 10
    assert measured.nominal_sensor_position_cross_track_uncertainty_decimeters == 20
    assert measured.nominal_sensor_position_altitude_uncertainty_decimeters == 30
    assert measured.nominal_sensor_track_uncertainty_degrees == 4
    assert measured.nominal_sensor_speed_uncertainty_millimeters_per_second == 50
    assert measured.nominal_slant_range_standard_deviation_centimeters == 60
    assert measured.nominal_cross_range_standard_deviation is not None
    assert measured.nominal_cross_range_standard_deviation.raw == 0x1234
    assert measured.nominal_radial_velocity_standard_deviation_centimeters_per_second == 70
    assert measured.nominal_minimum_detectable_velocity_decimeters_per_second == 8
    assert measured.nominal_detection_probability_percent == 90
    assert measured.nominal_false_alarm_density_negative_decibels == 100


def test_job_model_rejects_invalid_wire_shapes() -> None:
    job = decode_job_definition_segment(Segment(5, JOB_PAYLOAD))

    with pytest.raises(ValueError, match="job_id"):
        replace(job, job_id=-1)
    with pytest.raises(ValueError, match="sensor_model"):
        replace(job, sensor_model=b"short")
    with pytest.raises(ValueError, match="four points"):
        replace(job, bounding_area=job.bounding_area[:3])
    with pytest.raises(ValueError, match="SA32/BA32"):
        replace(
            job,
            bounding_area=(
                (SignedBinaryAngle(0, 16), job.bounding_area[0][1]),
                *job.bounding_area[1:],
            ),
        )
