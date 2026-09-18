"""AEDP-4607 Ed A V1 section 3.4 and Tables 3-9/3-10."""

from fractions import Fraction
from pathlib import Path

import pytest

from stanag4607 import (
    DecodeError,
    DwellExistenceMask,
    DwellSegment,
    Segment,
    TargetReport,
    decode_dwell_segment,
    decode_packet,
)

SPARSE_DWELL_PAYLOAD = bytes.fromhex(
    "ff 00 03 c1 80 00 00 00"
    "00 03 00 0b 01 00 01 01 d2 eb 40"
    "51 81 ef 29 11 94 23 80 00 0c f8 50"
    "51 23 45 68 11 59 e2 6b 06 40 01 11"
    "51 18 59 34 11 5b b4 74"
)


def test_decode_sparse_dwell_and_target_with_exact_geospatial_values() -> None:
    dwell = decode_dwell_segment(Segment(2, SPARSE_DWELL_PAYLOAD))

    assert dwell.revisit_index == 3
    assert dwell.dwell_index == 11
    assert dwell.last_dwell == 1
    assert dwell.target_report_count == 1
    assert dwell.dwell_time_milliseconds == 30_600_000
    assert dwell.sensor_latitude.raw == int.from_bytes(
        bytes.fromhex("51 81 ef 29"), "big", signed=True
    )
    assert dwell.sensor_longitude.raw == 0x11942380
    assert dwell.sensor_altitude_centimeters == 850_000
    assert dwell.center_latitude.raw == int.from_bytes(
        bytes.fromhex("51 23 45 68"), "big", signed=True
    )
    assert dwell.center_longitude.raw == 0x1159E26B
    assert dwell.range_half_extent_kilometers == Fraction(1600, 128)
    assert dwell.angle_half_extent.raw == 0x0111
    assert dwell.targets[0].high_resolution_latitude is not None
    assert dwell.targets[0].high_resolution_latitude.raw == int.from_bytes(
        bytes.fromhex("51 18 59 34"), "big", signed=True
    )
    assert dwell.targets[0].high_resolution_longitude is not None
    assert dwell.targets[0].high_resolution_longitude.raw == 0x115BB474
    location = dwell.target_location(0)
    assert location is not None
    assert location.encoding == "high_resolution"
    assert location.latitude.raw == int.from_bytes(
        bytes.fromhex("51 18 59 34"), "big", signed=True
    )
    assert location.longitude.raw == 0x115BB474
    assert dwell.to_segment() == Segment(2, SPARSE_DWELL_PAYLOAD)


def test_zero_target_count_ignores_target_mask_bits() -> None:
    payload = SPARSE_DWELL_PAYLOAD[:13] + b"\x00\x00" + SPARSE_DWELL_PAYLOAD[15:-8]
    dwell = decode_dwell_segment(Segment(2, payload))

    assert dwell.target_report_count == 0
    assert dwell.targets == ()
    assert dwell.to_segment().payload == payload


def test_wrong_segment_type_is_rejected() -> None:
    with pytest.raises(DecodeError, match="type 2"):
        decode_dwell_segment(Segment(1, SPARSE_DWELL_PAYLOAD))


def test_missing_mandatory_mask_field_is_rejected() -> None:
    payload = bytes([SPARSE_DWELL_PAYLOAD[0] & 0x7F]) + SPARSE_DWELL_PAYLOAD[1:]

    with pytest.raises(DecodeError, match=r"mandatory.*D2"):
        decode_dwell_segment(Segment(2, payload))


@pytest.mark.parametrize("amount", [1, 7, 8, 20, 50])
def test_truncated_dwell_is_rejected(amount: int) -> None:
    with pytest.raises(DecodeError, match="truncated"):
        decode_dwell_segment(Segment(2, SPARSE_DWELL_PAYLOAD[:amount]))


def test_trailing_dwell_bytes_are_rejected() -> None:
    with pytest.raises(DecodeError, match="trailing"):
        decode_dwell_segment(Segment(2, SPARSE_DWELL_PAYLOAD + b"x"))


def test_positive_target_count_requires_at_least_one_target_field() -> None:
    no_target_fields_mask = bytes.fromhex("ff 00 03 c0 00 00 00 00")
    payload = no_target_fields_mask + SPARSE_DWELL_PAYLOAD[8:-8]

    with pytest.raises(DecodeError, match="no Target Report fields"):
        decode_dwell_segment(Segment(2, payload))


def test_target_count_limit_is_enforced_before_target_allocation() -> None:
    payload = SPARSE_DWELL_PAYLOAD[:13] + b"\x00\x02" + SPARSE_DWELL_PAYLOAD[15:]

    with pytest.raises(DecodeError, match="target report count"):
        decode_dwell_segment(Segment(2, payload), max_target_reports=1)


def test_independent_full_optional_group_fixture_round_trips() -> None:
    fixture = Path(__file__).with_name("fixtures") / "full_mask_every_optional_group.gmti"
    packet = decode_packet(fixture.read_bytes())
    segment = next(item for item in packet.segments if item.segment_type == 2)

    dwell = decode_dwell_segment(segment)

    assert dwell.mask.raw == 0xFF3FFFFF9FF90000
    assert dwell.target_report_count == 2
    assert len(dwell.targets) == 2
    assert dwell.to_segment() == segment


def test_absent_optional_fields_are_explicit() -> None:
    dwell = decode_dwell_segment(Segment(2, SPARSE_DWELL_PAYLOAD))

    assert dwell.field_bytes(10) is None
    assert dwell.sensor_track is None
    assert dwell.sensor_vertical_velocity_decimeters_per_second is None
    assert dwell.sensor_heading is None
    assert dwell.targets[0].field_bytes(1) is None


def test_field_access_rejects_wrong_number_spaces() -> None:
    dwell = decode_dwell_segment(Segment(2, SPARSE_DWELL_PAYLOAD))

    with pytest.raises(ValueError, match="D2 through D31"):
        dwell.field_bytes(32)
    with pytest.raises(ValueError, match=r"D32\.1 through D32\.18"):
        dwell.targets[0].field_bytes(19)


def test_negative_target_limit_is_rejected() -> None:
    with pytest.raises(ValueError, match="negative"):
        decode_dwell_segment(Segment(2, SPARSE_DWELL_PAYLOAD), max_target_reports=-1)


def test_invalid_last_dwell_flag_is_rejected_during_decode() -> None:
    payload = SPARSE_DWELL_PAYLOAD[:12] + b"\x02" + SPARSE_DWELL_PAYLOAD[13:]

    with pytest.raises(DecodeError, match="last dwell flag"):
        decode_dwell_segment(Segment(2, payload))


def test_model_rejects_field_shape_and_target_count_disagreements() -> None:
    dwell = decode_dwell_segment(Segment(2, SPARSE_DWELL_PAYLOAD))

    with pytest.raises(ValueError, match="field count"):
        DwellSegment(dwell.mask, dwell.fields[:-1], dwell.targets)
    with pytest.raises(ValueError, match="exactly"):
        DwellSegment(dwell.mask, (b"", *dwell.fields[1:]), dwell.targets)
    with pytest.raises(ValueError, match="target report count"):
        DwellSegment(dwell.mask, dwell.fields, ())
    with pytest.raises(ValueError, match="target field count"):
        TargetReport(dwell.mask, dwell.targets[0].fields[:-1])


def test_model_rejects_target_using_different_mask() -> None:
    dwell = decode_dwell_segment(Segment(2, SPARSE_DWELL_PAYLOAD))
    other_mask = DwellExistenceMask(dwell.mask.raw | (1 << 33))
    other_target = TargetReport(other_mask, (b"\x00\x01", *dwell.targets[0].fields))

    with pytest.raises(ValueError, match="mask does not match"):
        DwellSegment(dwell.mask, dwell.fields, (other_target,))


def test_model_rejects_missing_mandatory_fields() -> None:
    with pytest.raises(ValueError, match=r"mandatory.*D2"):
        DwellSegment(DwellExistenceMask(0), (), ())


def test_target_semantic_accessors_retain_units_and_absence() -> None:
    fixture = Path(__file__).with_name("fixtures") / "full_mask_every_optional_group.gmti"
    packet = decode_packet(fixture.read_bytes())
    segment = next(item for item in packet.segments if item.segment_type == 2)
    target = decode_dwell_segment(segment).targets[0]

    assert target.report_index == 0
    assert target.delta_latitude is None
    assert target.delta_longitude is None
    assert target.geodetic_height_meters == 40
    assert target.radial_velocity_centimeters_per_second == -450
    assert target.wrap_velocity_centimeters_per_second == 3000
    assert target.signal_to_noise_ratio_decibels == 17
    assert target.classification == 2
    assert target.classification_probability_percent == 70
    assert target.slant_range_uncertainty_centimeters == 800
    assert target.cross_range_uncertainty_decimeters == 140
    assert target.height_uncertainty_meters == 12
    assert target.radial_velocity_uncertainty_centimeters_per_second == 90
    assert target.truth_tag_application is None
    assert target.truth_tag_entity is None
    assert target.radar_cross_section_decibels == Fraction(-14, 2)


def test_dwell_sensor_semantic_accessors_retain_units_and_angles() -> None:
    fixture = Path(__file__).with_name("fixtures") / "full_mask_every_optional_group.gmti"
    packet = decode_packet(fixture.read_bytes())
    segment = next(item for item in packet.segments if item.segment_type == 2)
    dwell = decode_dwell_segment(segment)

    assert dwell.latitude_scale is None
    assert dwell.longitude_scale is None
    assert dwell.sensor_position_along_track_uncertainty_centimeters == 250
    assert dwell.sensor_position_cross_track_uncertainty_centimeters == 310
    assert dwell.sensor_position_altitude_uncertainty_centimeters == 190
    assert dwell.sensor_track.raw == 0x4111
    assert dwell.sensor_speed_millimeters_per_second == 120_000
    assert dwell.sensor_vertical_velocity_decimeters_per_second == -2
    assert dwell.sensor_track_uncertainty_degrees == 3
    assert dwell.sensor_speed_uncertainty_millimeters_per_second == 900
    assert dwell.sensor_vertical_velocity_uncertainty_centimeters_per_second == 400
    assert dwell.platform_heading.raw == 0x416C
    assert dwell.platform_pitch.raw == 0x0222
    assert dwell.platform_roll.raw == -1456
    assert dwell.sensor_heading.raw == 0xC000
    assert dwell.sensor_pitch.raw == -4369
    assert dwell.sensor_roll.raw == 0x00B6
    assert dwell.minimum_detectable_velocity_decimeters_per_second == 30


def test_target_truth_identity_and_delta_values_are_signed_and_exact() -> None:
    mask = DwellExistenceMask((1 << 30) | (1 << 29) | (1 << 18) | (1 << 17))
    target = TargetReport(
        mask,
        (
            (-12).to_bytes(2, "big", signed=True),
            (34).to_bytes(2, "big", signed=True),
            b"\x07",
            (4_000_000_001).to_bytes(4, "big"),
        ),
    )

    assert target.delta_latitude == -12
    assert target.delta_longitude == 34
    assert target.truth_tag_application == 7
    assert target.truth_tag_entity == 4_000_000_001
    assert target.high_resolution_latitude is None
    assert target.high_resolution_longitude is None


def _reduced_location_dwell(*, center_latitude_raw: int = 1000) -> DwellSegment:
    mask = DwellExistenceMask(
        sum(1 << (65 - field) for field in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 24, 25, 26, 27))
        | (1 << (34 - 4))
        | (1 << (34 - 5))
    )
    return DwellSegment(
        mask,
        (
            b"\x00\x00",
            b"\x00\x00",
            b"\x00",
            b"\x00\x01",
            b"\x00" * 4,
            b"\x00" * 4,
            b"\x00" * 4,
            b"\x00" * 4,
            (2).to_bytes(4, "big", signed=True),
            (4).to_bytes(4, "big"),
            center_latitude_raw.to_bytes(4, "big", signed=True),
            (0xFFFFFFF0).to_bytes(4, "big"),
            b"\x00\x00",
            b"\x00\x00",
        ),
        (
            TargetReport(
                mask,
                (
                    (3).to_bytes(2, "big", signed=True),
                    (8).to_bytes(2, "big", signed=True),
                ),
            ),
        ),
    )


def test_reduced_target_location_uses_exact_scale_and_longitude_wrap() -> None:
    dwell = _reduced_location_dwell()

    location = dwell.target_location(0)

    assert location is not None
    assert location.encoding == "reduced"
    assert location.latitude.raw == 1006
    assert location.longitude.raw == 0x10
    assert location.latitude.degrees == Fraction(1006 * 180, 2**32)
    assert location.longitude.degrees == Fraction(0x10 * 360, 2**32)


def test_reduced_target_latitude_cannot_overflow_sa32() -> None:
    dwell = _reduced_location_dwell(center_latitude_raw=2**31 - 2)

    with pytest.raises(ValueError, match="latitude exceeds SA32"):
        dwell.target_location(0)


def test_target_without_complete_location_returns_none() -> None:
    mask = DwellExistenceMask(
        sum(1 << (65 - field) for field in (2, 3, 4, 5, 6, 7, 8, 9, 24, 25, 26, 27))
        | (1 << (34 - 11))
    )
    fields = (
        b"\x00\x00",
        b"\x00\x00",
        b"\x00",
        b"\x00\x01",
        b"\x00" * 4,
        b"\x00" * 4,
        b"\x00" * 4,
        b"\x00" * 4,
        b"\x00" * 4,
        b"\x00" * 4,
        b"\x00\x00",
        b"\x00\x00",
    )
    dwell = DwellSegment(mask, fields, (TargetReport(mask, (b"\x00",)),))

    assert dwell.target_location(0) is None
