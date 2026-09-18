"""Bounded contextual events using AEDP-4607 Ed A V1 sections 3.3 and 3.4.6."""

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from stanag4607 import (
    PACKET_HEADER_SIZE,
    ContextualStreamDecoder,
    DwellSegment,
    JobDefinitionSegment,
    MissionSegment,
    Packet,
    Segment,
    decode_dwell_segment,
    decode_packet,
)
from stanag4607 import TestStatusSegment as StatusSegment

PLATFORM_LOCATION_PAYLOAD = bytes.fromhex(
    "01 d2 eb 40 51 81 ef 29 11 94 23 80 00 0c f8 50 41 11 00 01 d4 c0 fe"
)


def _packet_like(
    source: Packet,
    segments: tuple[Segment, ...],
    *,
    mission_id: int,
    job_id: int,
) -> Packet:
    size = PACKET_HEADER_SIZE + sum(len(segment.to_bytes()) for segment in segments)
    header = replace(source.header, packet_size=size, mission_id=mission_id, job_id=job_id)
    return Packet(header, segments)


def test_context_stream_resolves_mission_job_and_exact_dwell_utc_across_packets() -> None:
    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    source = decode_packet(fixture.read_bytes())
    context_packet = _packet_like(source, source.segments[:2], mission_id=4242, job_id=0)
    dwell_packet = _packet_like(source, source.segments[2:], mission_id=4242, job_id=77)
    wire = context_packet.to_bytes() + dwell_packet.to_bytes()
    decoder = ContextualStreamDecoder()
    events = []

    for offset in range(0, len(wire), 7):
        events.extend(decoder.feed(wire[offset : offset + 7]))
    decoder.finish()

    assert len(events) == 3
    dwell_event = events[-1]
    assert isinstance(dwell_event.event.value, DwellSegment)
    assert dwell_event.packet_index == 1
    assert dwell_event.mission is events[0].event.value
    assert dwell_event.job_definition is events[1].event.value
    assert dwell_event.dwell_time_utc == datetime(2026, 4, 29, 8, 30, tzinfo=timezone.utc)


def test_context_caches_are_bounded_and_resettable() -> None:
    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    source = decode_packet(fixture.read_bytes())
    context = source.segments[:2]
    first = _packet_like(source, context, mission_id=1, job_id=0)
    second = _packet_like(source, context, mission_id=2, job_id=0)
    first_dwell = _packet_like(source, source.segments[2:], mission_id=1, job_id=77)
    decoder = ContextualStreamDecoder(max_mission_contexts=1, max_job_contexts=1)

    decoder.feed(first.to_bytes())
    decoder.feed(second.to_bytes())
    events = decoder.feed(first_dwell.to_bytes())

    assert decoder.mission_context_count == 1
    assert decoder.job_context_count == 1
    assert events[0].mission is None
    assert events[0].job_definition is None
    assert events[0].dwell_time_utc is None

    decoder.reset()
    assert decoder.mission_context_count == 0
    assert decoder.job_context_count == 0


@pytest.mark.parametrize("argument", ["max_mission_contexts", "max_job_contexts"])
def test_context_bounds_must_be_positive(argument: str) -> None:
    kwargs = {argument: 0}

    with pytest.raises(ValueError, match=argument):
        ContextualStreamDecoder(**kwargs)


def test_invalid_calendar_date_never_produces_a_false_absolute_time() -> None:
    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    source = decode_packet(fixture.read_bytes())
    mission_payload = source.segments[0].payload[:-4] + (2026).to_bytes(2, "big") + b"\x02\x1f"
    segments = (Segment(1, mission_payload), source.segments[2])
    packet = _packet_like(source, segments, mission_id=4242, job_id=77)

    events = ContextualStreamDecoder().feed(packet.to_bytes())

    assert events[-1].mission is not None
    assert events[-1].dwell_time_utc is None
    assert events[-1].event_time_issue is not None
    assert events[-1].event_time_issue.code == "context.invalid_mission_date"


def test_out_of_range_event_time_is_diagnostic_and_context_can_recover() -> None:
    """Library safety profile: unrepresentable UTC arithmetic must not escape."""

    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    source = decode_packet(fixture.read_bytes())
    mission = ContextualStreamDecoder().feed(source.to_bytes())[0].event.value
    dwell = decode_dwell_segment(source.segments[2])
    assert isinstance(mission, MissionSegment)
    dwell_fields = list(dwell.fields)
    dwell_fields[dwell.mask.present_dwell_fields.index(6)] = (86_400_000).to_bytes(4, "big")
    overflowing = replace(dwell, fields=tuple(dwell_fields))
    maximum_date = replace(
        mission, reference_year=9999, reference_month=12, reference_day=31
    )
    invalid_packet = _packet_like(
        source,
        (maximum_date.to_segment(), overflowing.to_segment()),
        mission_id=4242,
        job_id=77,
    )
    decoder = ContextualStreamDecoder()

    events = decoder.feed(invalid_packet.to_bytes())

    assert events[-1].event_time_utc is None
    assert events[-1].event_time_issue is not None
    assert events[-1].event_time_issue.code == "context.event_time_out_of_range"
    assert events[-1].event_time_issue.fields == ("M5", "M6", "M7", "D6")

    recovered_packet = _packet_like(
        source,
        (mission.to_segment(), source.segments[2]),
        mission_id=4242,
        job_id=77,
    )
    recovered = decoder.feed(recovered_packet.to_bytes())
    assert recovered[-1].event_time_utc == datetime(
        2026, 4, 29, 8, 30, tzinfo=timezone.utc
    )
    assert recovered[-1].event_time_issue is None


def test_platform_location_receives_the_same_exact_mission_time_context() -> None:
    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    source = decode_packet(fixture.read_bytes())
    segments = (source.segments[0], Segment(13, PLATFORM_LOCATION_PAYLOAD))
    packet = _packet_like(source, segments, mission_id=4242, job_id=0)

    events = ContextualStreamDecoder().feed(packet.to_bytes())

    assert events[-1].event_time_utc == datetime(
        2026, 4, 29, 8, 30, tzinfo=timezone.utc
    )
    assert events[-1].dwell_time_utc is None


def test_test_status_receives_the_same_exact_mission_time_context() -> None:
    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    source = decode_packet(fixture.read_bytes())
    status = StatusSegment(77, 0, 0, 30_600_000, 0, 0)
    segments = (source.segments[0], status.to_segment())
    packet = _packet_like(source, segments, mission_id=4242, job_id=0)

    events = ContextualStreamDecoder().feed(packet.to_bytes())

    assert events[-1].event_time_utc == datetime(
        2026, 4, 29, 8, 30, tzinfo=timezone.utc
    )
    assert events[-1].dwell_time_utc is None


def test_public_repeated_mission_is_identified_as_a_repeat() -> None:
    fixture = Path(__file__).with_name("fixtures") / "repeated_mission_segment.gmti"

    events = ContextualStreamDecoder().feed(fixture.read_bytes())

    updates = [event.context_update for event in events if event.context_update is not None]
    assert [update.action for update in updates] == ["new", "repeat"]
    assert all(update.kind == "mission" for update in updates)
    assert updates[1].previous is events[0].event.value
    assert updates[1].evicted_key is None


def test_mission_replacement_updates_following_event_time() -> None:
    fixture = Path(__file__).with_name("fixtures") / "repeated_mission_segment.gmti"
    packet = decode_packet(fixture.read_bytes())
    original_mission = ContextualStreamDecoder().feed(packet.to_bytes())[0].event.value
    assert isinstance(original_mission, MissionSegment)
    replacement = replace(original_mission, reference_day=30).to_segment()
    segments = (*packet.segments[:2], replacement, packet.segments[3])
    changed = Packet(packet.header, segments)

    events = ContextualStreamDecoder().feed(changed.to_bytes())

    update = events[2].context_update
    assert update is not None
    assert update.action == "replace"
    assert update.previous is events[0].event.value
    assert events[3].event_time_utc == datetime(
        2026, 4, 30, 8, 30, 30, tzinfo=timezone.utc
    )


def test_job_replacement_updates_following_dwell_context() -> None:
    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    packet = decode_packet(fixture.read_bytes())
    initial_job = ContextualStreamDecoder().feed(packet.to_bytes())[1].event.value
    assert isinstance(initial_job, JobDefinitionSegment)
    replacement = replace(initial_job, priority=7).to_segment()
    segments = (packet.segments[0], packet.segments[1], replacement, packet.segments[2])
    changed = _packet_like(packet, segments, mission_id=4242, job_id=77)

    events = ContextualStreamDecoder().feed(changed.to_bytes())

    assert events[1].context_update is not None
    assert events[1].context_update.action == "new"
    assert events[2].context_update is not None
    assert events[2].context_update.action == "replace"
    assert events[2].context_update.previous is events[1].event.value
    assert events[3].job_definition is events[2].event.value


def test_context_update_reports_deterministic_lru_eviction_key() -> None:
    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    source = decode_packet(fixture.read_bytes())
    first = _packet_like(source, source.segments[:1], mission_id=1, job_id=0)
    second = _packet_like(source, source.segments[:1], mission_id=2, job_id=0)
    decoder = ContextualStreamDecoder(max_mission_contexts=1)

    decoder.feed(first.to_bytes())
    event = decoder.feed(second.to_bytes())[0]

    assert event.context_update is not None
    assert event.context_update.action == "new"
    assert event.context_update.evicted_key == (source.header.platform_id, 1)


def test_job_context_update_reports_deterministic_lru_eviction_key() -> None:
    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    source = decode_packet(fixture.read_bytes())
    initial_job = ContextualStreamDecoder().feed(source.to_bytes())[1].event.value
    assert isinstance(initial_job, JobDefinitionSegment)
    second_job = replace(initial_job, job_id=78).to_segment()
    first = _packet_like(source, source.segments[1:2], mission_id=1, job_id=77)
    second = _packet_like(source, (second_job,), mission_id=1, job_id=78)
    decoder = ContextualStreamDecoder(max_job_contexts=1)

    decoder.feed(first.to_bytes())
    event = decoder.feed(second.to_bytes())[0]

    assert event.context_update is not None
    assert event.context_update.action == "new"
    assert event.context_update.evicted_key == (source.header.platform_id, 1, 77)
