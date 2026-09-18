"""AEDP-4607 Ed A V1 sections 3.4.2-3.4.4 stream continuity."""

from dataclasses import replace
from pathlib import Path

import pytest

from stanag4607 import (
    DwellSegment,
    HrrSegment,
    Packet,
    SegmentEvent,
    StreamContinuityValidator,
    decode_packet,
    iter_packet_events,
)


def _dwell_event(
    packet: Packet, *, revisit: int, dwell_index: int, last: int
) -> SegmentEvent:
    event = next(
        event for event in iter_packet_events(packet) if isinstance(event.value, DwellSegment)
    )
    dwell = event.value
    fields = list(dwell.fields)
    present = dwell.mask.present_dwell_fields
    fields[present.index(2)] = revisit.to_bytes(2, "big")
    fields[present.index(3)] = dwell_index.to_bytes(2, "big")
    fields[present.index(4)] = last.to_bytes(1, "big")
    changed = replace(dwell, fields=tuple(fields))
    return replace(event, value=changed, segment=changed.to_segment())


def _packet() -> Packet:
    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    return decode_packet(fixture.read_bytes())


def _hrr_event(*, revisit: int, dwell_index: int, last: int) -> SegmentEvent:
    fixture = (
        Path(__file__).with_name("fixtures")
        / "hrr_signature_parked_both_time_branches.gmti"
    )
    packet = decode_packet(fixture.read_bytes())
    event = next(
        event for event in iter_packet_events(packet) if isinstance(event.value, HrrSegment)
    )
    hrr = event.value
    fields = list(hrr.fields)
    present = hrr.mask.present_hrr_fields
    fields[present.index(2)] = revisit.to_bytes(2, "big")
    fields[present.index(3)] = dwell_index.to_bytes(2, "big")
    fields[present.index(4)] = last.to_bytes(1, "big")
    changed = replace(hrr, fields=tuple(fields))
    return replace(event, value=changed, segment=changed.to_segment())


def test_sequential_dwells_and_new_revisit_are_valid() -> None:
    packet = _packet()
    validator = StreamContinuityValidator()

    assert validator.observe(_dwell_event(packet, revisit=0, dwell_index=0, last=0)) == ()
    assert validator.observe(_dwell_event(packet, revisit=0, dwell_index=1, last=1)) == ()
    assert validator.observe(_dwell_event(packet, revisit=1, dwell_index=0, last=0)) == ()


def test_gap_after_last_and_nonzero_first_dwell_are_reported() -> None:
    packet = _packet()
    validator = StreamContinuityValidator()
    validator.observe(_dwell_event(packet, revisit=4, dwell_index=7, last=1))

    same_revisit = validator.observe(_dwell_event(packet, revisit=4, dwell_index=9, last=0))
    new_revisit = validator.observe(_dwell_event(packet, revisit=5, dwell_index=2, last=0))

    assert {issue.code for issue in same_revisit} == {
        "stream.dwell_index_gap",
        "stream.dwell_after_last",
    }
    assert {issue.code for issue in new_revisit} == {"stream.revisit_first_dwell_index"}


def test_dwell_index_wrap_is_sequential() -> None:
    packet = _packet()
    validator = StreamContinuityValidator()
    validator.observe(_dwell_event(packet, revisit=2, dwell_index=0xFFFF, last=0))

    assert validator.observe(_dwell_event(packet, revisit=2, dwell_index=0, last=0)) == ()


def test_non_dwell_events_do_not_create_continuity_state() -> None:
    event = next(iter_packet_events(_packet()))
    validator = StreamContinuityValidator(max_jobs=1)

    assert validator.observe(event) == ()
    assert validator.tracked_jobs == 0


def test_continuity_state_is_bounded_and_resettable() -> None:
    packet = _packet()
    validator = StreamContinuityValidator(max_jobs=1)
    validator.observe(_dwell_event(packet, revisit=0, dwell_index=0, last=0))
    other_header = replace(packet.header, mission_id=packet.header.mission_id + 1)
    validator.observe(
        replace(
            _dwell_event(packet, revisit=0, dwell_index=0, last=0),
            packet_header=other_header,
        )
    )

    assert validator.tracked_jobs == 1
    validator.reset()
    assert validator.tracked_jobs == 0


def test_continuity_bound_must_be_positive() -> None:
    with pytest.raises(ValueError, match="max_jobs"):
        StreamContinuityValidator(max_jobs=0)


def test_hrr_sequence_is_checked_independently_from_dwell_sequence() -> None:
    packet = _packet()
    validator = StreamContinuityValidator()

    assert validator.observe(_dwell_event(packet, revisit=3, dwell_index=11, last=0)) == ()
    assert validator.observe(_hrr_event(revisit=3, dwell_index=11, last=0)) == ()
    assert validator.observe(_hrr_event(revisit=3, dwell_index=12, last=1)) == ()


def test_hrr_gap_after_last_and_nonzero_new_revisit_are_reported() -> None:
    validator = StreamContinuityValidator()
    validator.observe(_hrr_event(revisit=4, dwell_index=7, last=1))

    same_revisit = validator.observe(_hrr_event(revisit=4, dwell_index=9, last=0))
    new_revisit = validator.observe(_hrr_event(revisit=5, dwell_index=2, last=0))

    assert {issue.code for issue in same_revisit} == {
        "stream.hrr_after_last",
        "stream.hrr_dwell_index_gap",
    }
    assert {issue.code for issue in new_revisit} == {
        "stream.hrr_revisit_first_dwell_index"
    }
