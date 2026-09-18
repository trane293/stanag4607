"""AEDP-4607 Ed A V1 section 3.3 and Tables 3-7 through 3-8."""

from __future__ import annotations

import pytest

from stanag4607 import DecodeError, MissionSegment, Segment, decode_mission_segment

MISSION_PAYLOAD = bytes.fromhex(
    "53 59 4e 4d 53 4e 30 30 30 31 20 20"
    "53 59 4e 46 4c 54 30 30 30 31 20 20"
    "c8"
    "53 59 4e 2d 43 46 47 2d 31 20"
    "07 ea 04 1d"
)


def test_decode_mission_segment_preserves_reference_date_and_wire_values() -> None:
    mission = decode_mission_segment(Segment(1, MISSION_PAYLOAD))

    assert mission == MissionSegment(
        mission_plan=b"SYNMSN0001  ",
        flight_plan=b"SYNFLT0001  ",
        platform_type=200,
        platform_configuration=b"SYN-CFG-1 ",
        reference_year=2026,
        reference_month=4,
        reference_day=29,
    )
    assert mission.to_segment() == Segment(1, MISSION_PAYLOAD)


@pytest.mark.parametrize("length", [0, 1, 38, 40])
def test_mission_segment_requires_exactly_39_payload_bytes(length: int) -> None:
    with pytest.raises(DecodeError, match="39 bytes"):
        decode_mission_segment(Segment(1, (MISSION_PAYLOAD + b"x")[:length]))


def test_mission_decoder_rejects_wrong_segment_type() -> None:
    with pytest.raises(DecodeError, match="type 1"):
        decode_mission_segment(Segment(2, MISSION_PAYLOAD))


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"mission_plan": b"short"}, "mission_plan"),
        ({"flight_plan": b"short"}, "flight_plan"),
        ({"platform_type": 256}, "platform_type"),
        ({"platform_configuration": b"short"}, "platform_configuration"),
        ({"reference_year": 2**16}, "reference_year"),
        ({"reference_month": 0}, "reference_month"),
        ({"reference_month": 13}, "reference_month"),
        ({"reference_day": 0}, "reference_day"),
        ({"reference_day": 32}, "reference_day"),
    ],
)
def test_mission_segment_rejects_values_outside_wire_or_table_ranges(
    changes: dict[str, object], message: str
) -> None:
    values: dict[str, object] = {
        "mission_plan": b"MISSION-001 ",
        "flight_plan": b"FLIGHT-001  ",
        "platform_type": 15,
        "platform_configuration": b"CONFIG-01 ",
        "reference_year": 2026,
        "reference_month": 9,
        "reference_day": 12,
    }
    values.update(changes)

    with pytest.raises(ValueError, match=message):
        MissionSegment(**values)  # type: ignore[arg-type]


def test_reserved_platform_type_is_preserved() -> None:
    mission = decode_mission_segment(Segment(1, MISSION_PAYLOAD))

    assert mission.platform_type == 200
    assert mission.to_segment().payload == MISSION_PAYLOAD


def test_decoder_reports_invalid_reference_date_fields() -> None:
    invalid_day = MISSION_PAYLOAD[:-1] + b"\x20"

    with pytest.raises(DecodeError, match="reference_day"):
        decode_mission_segment(Segment(1, invalid_day))
