"""AEDP-4607 Ed A V1 sections 3.4.1 and 3.4.10-3.4.32.17."""

from pathlib import Path

import pytest

from stanag4607 import (
    DwellExistenceMask,
    DwellSegment,
    TargetReport,
    decode_dwell_segment,
    decode_packet,
    validate_dwell,
)

_MANDATORY_DWELL_FIELDS = {2, 3, 4, 5, 6, 7, 8, 9, 24, 25, 26, 27}
_DWELL_WIDTHS = {
    2: 2,
    3: 2,
    4: 1,
    5: 2,
    6: 4,
    7: 4,
    8: 4,
    9: 4,
    10: 4,
    11: 4,
    12: 4,
    13: 4,
    14: 2,
    15: 2,
    16: 4,
    17: 1,
    18: 1,
    19: 2,
    20: 2,
    21: 2,
    22: 2,
    23: 2,
    24: 4,
    25: 4,
    26: 2,
    27: 2,
    28: 2,
    29: 2,
    30: 2,
    31: 1,
}
_TARGET_WIDTHS = {
    1: 2,
    2: 4,
    3: 4,
    4: 2,
    5: 2,
    6: 2,
    7: 2,
    8: 2,
    9: 1,
    10: 1,
    11: 1,
    12: 2,
    13: 2,
    14: 1,
    15: 2,
    16: 1,
    17: 4,
    18: 1,
}


def _mask(
    *,
    dwell: frozenset[int] | set[int] = frozenset(),
    target: frozenset[int] | set[int] = frozenset(),
    spare: int = 0,
) -> DwellExistenceMask:
    raw = spare
    for field in _MANDATORY_DWELL_FIELDS | dwell:
        raw |= 1 << (65 - field)
    for field in target:
        raw |= 1 << (34 - field)
    return DwellExistenceMask(raw)


def _dwell(
    *,
    fields: frozenset[int] | set[int] = frozenset(),
    target_fields: frozenset[int] | set[int] = frozenset(),
    dwell_values: dict[int, bytes] | None = None,
    target_values: dict[int, int] | None = None,
    target_encoded_values: dict[int, bytes] | None = None,
    target_count: int | None = None,
    spare: int = 0,
) -> DwellSegment:
    mask = _mask(dwell=fields, target=target_fields, spare=spare)
    count = (1 if target_fields else 0) if target_count is None else target_count
    encoded_dwell_values = dwell_values or {}
    dwell_field_bytes = []
    for field in mask.present_dwell_fields:
        value = count if field == 5 else 0
        dwell_field_bytes.append(
            encoded_dwell_values.get(
                field, value.to_bytes(_DWELL_WIDTHS[field], "big")
            )
        )
    target_values = target_values or {}
    target_encoded_values = target_encoded_values or {}
    target = TargetReport(
        mask,
        tuple(
            target_encoded_values.get(
                field,
                target_values.get(field, 0).to_bytes(_TARGET_WIDTHS[field], "big"),
            )
            for field in mask.present_target_fields
        ),
    )
    return DwellSegment(mask, tuple(dwell_field_bytes), (target,) if count else ())


def test_valid_public_fixture_has_no_dwell_conformance_issues() -> None:
    fixture = Path(__file__).with_name("fixtures") / "full_mask_every_optional_group.gmti"
    packet = decode_packet(fixture.read_bytes())
    segment = next(item for item in packet.segments if item.segment_type == 2)

    assert validate_dwell(decode_dwell_segment(segment)) == ()


@pytest.mark.parametrize(
    ("dwell_fields", "target_fields", "expected_code"),
    [
        ({10}, {2, 3}, "dwell.coordinate_scale_pair"),
        (set(), {2}, "target.high_resolution_location_pair"),
        (set(), {4}, "target.reduced_location_pair"),
        ({10, 11}, {2, 3, 4, 5}, "target.location_encodings_exclusive"),
        ({12}, set(), "dwell.sensor_position_uncertainty_group"),
        ({15}, set(), "dwell.sensor_velocity_group"),
        ({18}, set(), "dwell.sensor_velocity_uncertainty_group"),
        ({21}, set(), "dwell.platform_orientation_group"),
        (set(), {7}, "target.velocity_wrap_pair"),
        (set(), {16}, "target.truth_tag_pair"),
    ],
)
def test_conditional_field_groups_are_reported(
    dwell_fields: set[int], target_fields: set[int], expected_code: str
) -> None:
    issues = validate_dwell(_dwell(fields=dwell_fields, target_fields=target_fields))

    assert expected_code in {issue.code for issue in issues}


def test_reduced_location_and_scale_factors_are_required_together() -> None:
    issues = validate_dwell(_dwell(fields={10, 11}, target_fields={2, 3}))

    assert "target.reduced_location_scale_factors" in {issue.code for issue in issues}


def test_spare_mask_bits_and_probability_above_100_are_reported() -> None:
    issues = validate_dwell(
        _dwell(target_fields={11}, target_values={11: 101}, spare=1)
    )

    assert {issue.code for issue in issues} == {
        "dwell.existence_mask_spare_bits",
        "target.classification_probability_range",
    }
    assert issues[1].fields == ("D32.11[0]",)


def test_zero_target_exception_ignores_target_presence_bits() -> None:
    dwell = _dwell(target_fields={2, 7, 16}, target_count=0)

    assert validate_dwell(dwell) == ()


@pytest.mark.parametrize(
    ("fields", "target_fields", "expected_code"),
    [
        (set(), {12}, "target.uncertainty_sensor_position_required"),
        ({12, 13, 14}, {14}, "target.height_uncertainty_height_required"),
        ({12, 13, 14}, {15}, "target.velocity_uncertainty_velocity_required"),
    ],
)
def test_target_uncertainty_preconditions_are_reported(
    fields: set[int], target_fields: set[int], expected_code: str
) -> None:
    issues = validate_dwell(_dwell(fields=fields, target_fields=target_fields))

    assert expected_code in {issue.code for issue in issues}


def test_numeric_ranges_are_reported_with_target_index() -> None:
    issues = validate_dwell(
        _dwell(
            fields={12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 29},
            target_fields={6, 7, 8, 12, 13, 14, 15},
            dwell_values={
                6: (4_000_000_001).to_bytes(4, "big"),
                9: (-50_001).to_bytes(4, "big", signed=True),
                12: (1_000_001).to_bytes(4, "big"),
                13: (1_000_001).to_bytes(4, "big"),
                16: (8_000_001).to_bytes(4, "big"),
                18: (46).to_bytes(1, "big"),
                22: (0x4000).to_bytes(2, "big"),
                23: (0x4000).to_bytes(2, "big"),
                29: (0x4000).to_bytes(2, "big"),
            },
            target_encoded_values={
                6: (-1001).to_bytes(2, "big", signed=True),
                15: (5001).to_bytes(2, "big"),
            },
        )
    )

    assert {issue.code for issue in issues} == {
        "dwell.time_range",
        "dwell.sensor_altitude_range",
        "dwell.sensor_position_uncertainty_range",
        "dwell.sensor_speed_range",
        "dwell.sensor_track_uncertainty_range",
        "dwell.platform_attitude_range",
        "dwell.sensor_attitude_range",
        "target.geodetic_height_range",
        "target.radial_velocity_uncertainty_range",
    }
    assert any(issue.fields == ("D32.6[0]",) for issue in issues)
