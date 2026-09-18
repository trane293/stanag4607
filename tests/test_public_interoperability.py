"""Round-trip evidence from the attributed Apache-2.0 Edition 4 corpus."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from stanag4607 import ContextualStreamDecoder, HrrSegment, PacketStreamDecoder, Segment

_FIXTURES = Path(__file__).with_name("fixtures")


@pytest.mark.parametrize(
    ("name", "types"),
    [
        (
            "free_text_and_test_status.gmti",
            ("MissionSegment", "FreeTextSegment", "TestStatusSegment"),
        ),
        (
            "processing_history_chain.gmti",
            ("MissionSegment", "ProcessingHistorySegment"),
        ),
        (
            "platform_location_mixed_time_basis.gmti",
            (
                "MissionSegment",
                "DwellSegment",
                "PlatformLocationSegment",
                "PlatformLocationSegment",
            ),
        ),
        (
            "repeated_mission_segment.gmti",
            (
                "MissionSegment",
                "PlatformLocationSegment",
                "MissionSegment",
                "PlatformLocationSegment",
            ),
        ),
        (
            "reserved_and_extension_segments_recorded.gmti",
            ("MissionSegment", "Segment", "Segment", "DwellSegment"),
        ),
        (
            "hrr_signature_parked_both_time_branches.gmti",
            ("MissionSegment", "DwellSegment", "HrrSegment", "HrrSegment"),
        ),
    ],
)
def test_public_packet_decodes_in_chunks_and_round_trips(
    name: str, types: tuple[str, ...]
) -> None:
    wire = (_FIXTURES / name).read_bytes()
    decoder = PacketStreamDecoder()
    packets = []

    for offset in range(0, len(wire), 11):
        packets.extend(decoder.feed(wire[offset : offset + 11]))
    decoder.finish()

    assert len(packets) == 1
    assert packets[0].to_bytes() == wire
    contextual = ContextualStreamDecoder().feed(wire)
    assert tuple(type(item.event.value).__name__ for item in contextual) == types


def test_public_status_and_platform_times_resolve_exactly() -> None:
    status_wire = (_FIXTURES / "free_text_and_test_status.gmti").read_bytes()
    location_wire = (_FIXTURES / "platform_location_mixed_time_basis.gmti").read_bytes()

    status_events = ContextualStreamDecoder().feed(status_wire)
    location_events = ContextualStreamDecoder().feed(location_wire)

    assert status_events[-1].event_time_utc == datetime(
        2026, 4, 29, 8, 30, 1, tzinfo=timezone.utc
    )
    assert [event.event_time_utc for event in location_events[-2:]] == [
        datetime(2026, 4, 29, 8, 31, tzinfo=timezone.utc),
        datetime(2026, 4, 29, 8, 32, tzinfo=timezone.utc),
    ]


def test_reserved_extensions_and_hrr_scatterer_regions_remain_opaque() -> None:
    reserved = ContextualStreamDecoder().feed(
        (_FIXTURES / "reserved_and_extension_segments_recorded.gmti").read_bytes()
    )
    hrr = ContextualStreamDecoder().feed(
        (_FIXTURES / "hrr_signature_parked_both_time_branches.gmti").read_bytes()
    )

    assert [
        item.event.value.segment_type
        for item in reserved
        if isinstance(item.event.value, Segment)
    ] == [8, 132]
    assert [
        item.event.value.scatterer_data
        for item in hrr
        if isinstance(item.event.value, HrrSegment)
    ] == [b"\x10\x20\x30\x40", b"\xaa\xbb"]
