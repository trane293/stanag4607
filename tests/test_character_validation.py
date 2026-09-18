"""AEDP-4607 Ed A V1 section 2.3 and Annex A BCS validation."""

from dataclasses import replace
from pathlib import Path

from stanag4607 import (
    JobDefinitionSegment,
    MissionSegment,
    ProcessingHistorySegment,
    ProcessingRecord,
    decode_packet,
    iter_packet_events,
    validate_job_definition,
    validate_mission,
    validate_packet_header,
    validate_processing_history,
)


def _typed_values() -> tuple[MissionSegment, JobDefinitionSegment]:
    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    values = tuple(event.value for event in iter_packet_events(decode_packet(fixture.read_bytes())))
    mission = next(value for value in values if isinstance(value, MissionSegment))
    job = next(value for value in values if isinstance(value, JobDefinitionSegment))
    return mission, job


def test_packet_header_reports_every_non_bcs_character_field() -> None:
    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    header = decode_packet(fixture.read_bytes()).header
    invalid = replace(
        header,
        version_id=b"4\x00",
        nationality=b"\xffA",
        classification_system=b"U\t",
        platform_id=b"PLATFORM \x1f",
    )

    issues = validate_packet_header(invalid)

    assert len(issues) == 1
    assert issues[0].code == "packet.invalid_bcs"
    assert issues[0].fields == ("P1", "P3", "P5", "P8")


def test_mission_and_job_character_validation_is_non_destructive() -> None:
    mission, job = _typed_values()
    mission = replace(mission, flight_plan=b"FLIGHT-1   \x00")
    job = replace(job, sensor_model=b"SENS\xff ")

    mission_issues = validate_mission(mission)
    job_issues = validate_job_definition(job)

    assert mission_issues[0].code == "mission.invalid_bcs"
    assert mission_issues[0].fields == ("M2",)
    assert job_issues[-1].code == "job.invalid_bcs"
    assert job_issues[-1].fields == ("J3",)
    assert mission.to_segment().payload[12:24] == b"FLIGHT-1   \x00"
    assert job.to_segment().payload[5:11] == b"SENS\xff "


def test_processing_history_validates_source_and_record_character_fields() -> None:
    history = ProcessingHistorySegment(
        based_on_nationality=b"\x00A",
        based_on_platform_id=b"PLATFORM \x7f",
        based_on_mission_id=1,
        based_on_job_id=1,
        records=(ProcessingRecord(1, b"CA", b"SOURCE   \xff", 2, 2, 0),),
    )

    issues = validate_processing_history(history)

    assert issues[-1].code == "processing_history.invalid_bcs"
    assert issues[-1].fields == ("C2", "C3", "C6.3[0]")
