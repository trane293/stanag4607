"""Typed, provenance-preserving application events."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .dwell import DwellSegment, decode_dwell_segment
from .free_text import FreeTextSegment, decode_free_text_segment
from .hrr import HrrSegment, decode_hrr_segment
from .job_definition import JobDefinitionSegment, decode_job_definition_segment
from .mission import MissionSegment, decode_mission_segment
from .packet import Packet, PacketHeader, Segment
from .platform_location import PlatformLocationSegment, decode_platform_location_segment
from .processing_history import ProcessingHistorySegment, decode_processing_history_segment
from .tasking import (
    JobAcknowledgeSegment,
    JobRequestSegment,
    decode_job_acknowledge_segment,
    decode_job_request_segment,
)
from .test_status import TestStatusSegment, decode_test_status_segment

DecodedSegment = (
    MissionSegment
    | DwellSegment
    | FreeTextSegment
    | HrrSegment
    | JobDefinitionSegment
    | PlatformLocationSegment
    | ProcessingHistorySegment
    | TestStatusSegment
    | JobRequestSegment
    | JobAcknowledgeSegment
    | Segment
)


@dataclass(frozen=True, slots=True)
class SegmentEvent:
    """One typed segment with its unchanged packet and wire provenance."""

    packet_header: PacketHeader
    segment_index: int
    segment: Segment
    value: DecodedSegment


def decode_typed_segment(segment: Segment) -> DecodedSegment:
    """Decode a supported segment type or return the original opaque segment."""

    if segment.segment_type == 1:
        return decode_mission_segment(segment)
    if segment.segment_type == 2:
        return decode_dwell_segment(segment)
    if segment.segment_type == 3:
        return decode_hrr_segment(segment)
    if segment.segment_type == 5:
        return decode_job_definition_segment(segment)
    if segment.segment_type == 6:
        return decode_free_text_segment(segment)
    if segment.segment_type == 10:
        return decode_test_status_segment(segment)
    if segment.segment_type == 12:
        return decode_processing_history_segment(segment)
    if segment.segment_type == 13:
        return decode_platform_location_segment(segment)
    if segment.segment_type == 101:
        return decode_job_request_segment(segment)
    if segment.segment_type == 102:
        return decode_job_acknowledge_segment(segment)
    return segment


def iter_packet_events(packet: Packet) -> Iterator[SegmentEvent]:
    """Yield typed events in wire order without copying opaque segment payloads."""

    for index, segment in enumerate(packet.segments):
        yield SegmentEvent(
            packet_header=packet.header,
            segment_index=index,
            segment=segment,
            value=decode_typed_segment(segment),
        )
