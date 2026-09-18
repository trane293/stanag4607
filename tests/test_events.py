"""Typed event boundary over losslessly framed packet segments."""

from pathlib import Path

from stanag4607 import (
    DwellSegment,
    JobDefinitionSegment,
    MissionSegment,
    Packet,
    PacketHeader,
    Segment,
    iter_packet_events,
)


def test_packet_events_decode_known_segments_and_retain_provenance() -> None:
    from stanag4607 import decode_packet

    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    packet = decode_packet(fixture.read_bytes())

    events = tuple(iter_packet_events(packet))

    assert len(events) == 3
    assert isinstance(events[0].value, MissionSegment)
    assert isinstance(events[1].value, JobDefinitionSegment)
    assert isinstance(events[2].value, DwellSegment)
    for index, event in enumerate(events):
        assert event.packet_header is packet.header
        assert event.segment_index == index
        assert event.segment is packet.segments[index]


def test_unknown_segment_remains_the_exact_opaque_value() -> None:
    segment = Segment(200, b"extension-data")
    packet = Packet(
        PacketHeader(
            version_id=b"41",
            packet_size=32 + 5 + len(segment.payload),
            nationality=b"CA",
            security_classification=5,
            classification_system=b"CA",
            security_codes=0,
            exercise_indicator=0,
            platform_id=b"RADAR-01  ",
            mission_id=42,
            job_id=0,
        ),
        (segment,),
    )

    event = next(iter_packet_events(packet))

    assert event.value is segment
    assert event.segment is segment
