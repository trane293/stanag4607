"""Bounded contextual decoding for incremental STANAG 4607 streams."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from .dwell import DwellSegment
from .events import SegmentEvent, iter_packet_events
from .job_definition import JobDefinitionSegment
from .mission import MissionSegment
from .packet import DecodeLimits, PacketHeader
from .platform_location import PlatformLocationSegment
from .stream import PacketStreamDecoder
from .test_status import TestStatusSegment
from .validation import ValidationIssue

DEFAULT_MAX_MISSION_CONTEXTS = 128
DEFAULT_MAX_JOB_CONTEXTS = 1_024
_MissionKey = tuple[bytes, int]
_JobKey = tuple[bytes, int, int]
_ContextKey = _MissionKey | _JobKey
_ContextValue = MissionSegment | JobDefinitionSegment


@dataclass(frozen=True, slots=True)
class ContextUpdate:
    """One explicit Mission or Job context insertion, repeat, or replacement."""

    kind: Literal["mission", "job"]
    action: Literal["new", "repeat", "replace"]
    key: _ContextKey
    previous: _ContextValue | None
    evicted_key: _ContextKey | None


@dataclass(frozen=True, slots=True)
class ContextualSegmentEvent:
    """A typed event plus bounded standard-defined mission and job context."""

    packet_index: int
    event: SegmentEvent
    mission: MissionSegment | None
    job_definition: JobDefinitionSegment | None
    event_time_utc: datetime | None
    context_update: ContextUpdate | None
    event_time_issue: ValidationIssue | None = None

    @property
    def dwell_time_utc(self) -> datetime | None:
        """Return event time only for a Dwell value."""

        return self.event_time_utc if isinstance(self.event.value, DwellSegment) else None


class ContextualStreamDecoder:
    """Incrementally decode events while retaining bounded Mission/Job state."""

    def __init__(
        self,
        *,
        limits: DecodeLimits | None = None,
        max_mission_contexts: int = DEFAULT_MAX_MISSION_CONTEXTS,
        max_job_contexts: int = DEFAULT_MAX_JOB_CONTEXTS,
    ) -> None:
        if max_mission_contexts <= 0:
            raise ValueError("max_mission_contexts must be positive")
        if max_job_contexts <= 0:
            raise ValueError("max_job_contexts must be positive")
        self._packets = PacketStreamDecoder(limits=limits)
        self._max_mission_contexts = max_mission_contexts
        self._max_job_contexts = max_job_contexts
        self._missions: OrderedDict[_MissionKey, MissionSegment] = OrderedDict()
        self._jobs: OrderedDict[_JobKey, JobDefinitionSegment] = OrderedDict()
        self._packet_index = 0

    @property
    def mission_context_count(self) -> int:
        return len(self._missions)

    @property
    def job_context_count(self) -> int:
        return len(self._jobs)

    @staticmethod
    def _mission_key(header: PacketHeader) -> _MissionKey:
        return header.platform_id, header.mission_id

    @staticmethod
    def _job_key(header: PacketHeader, job_id: int | None = None) -> _JobKey:
        return header.platform_id, header.mission_id, header.job_id if job_id is None else job_id

    def _put_mission(self, key: _MissionKey, value: MissionSegment) -> ContextUpdate:
        previous = self._missions.get(key)
        action: Literal["new", "repeat", "replace"] = (
            "new" if previous is None else "repeat" if previous == value else "replace"
        )
        self._missions[key] = value
        self._missions.move_to_end(key)
        evicted_key: _MissionKey | None = None
        if len(self._missions) > self._max_mission_contexts:
            evicted_key, _ = self._missions.popitem(last=False)
        return ContextUpdate("mission", action, key, previous, evicted_key)

    def _put_job(self, key: _JobKey, value: JobDefinitionSegment) -> ContextUpdate:
        previous = self._jobs.get(key)
        action: Literal["new", "repeat", "replace"] = (
            "new" if previous is None else "repeat" if previous == value else "replace"
        )
        self._jobs[key] = value
        self._jobs.move_to_end(key)
        evicted_key: _JobKey | None = None
        if len(self._jobs) > self._max_job_contexts:
            evicted_key, _ = self._jobs.popitem(last=False)
        return ContextUpdate("job", action, key, previous, evicted_key)

    @staticmethod
    def _event_time(
        value: object, mission: MissionSegment | None
    ) -> tuple[datetime | None, ValidationIssue | None]:
        if mission is None:
            return None, None
        if isinstance(value, DwellSegment):
            milliseconds = value.dwell_time_milliseconds
            time_field = "D6"
        elif isinstance(value, PlatformLocationSegment):
            milliseconds = value.location_time_milliseconds
            time_field = "L1"
        elif isinstance(value, TestStatusSegment):
            milliseconds = value.dwell_time_milliseconds
            time_field = "T4"
        else:
            return None, None
        try:
            reference = datetime(
                mission.reference_year,
                mission.reference_month,
                mission.reference_day,
                tzinfo=timezone.utc,
            )
        except ValueError:
            return None, ValidationIssue(
                "context.invalid_mission_date",
                "M5-M7 do not form a representable Gregorian reference date",
                ("M5", "M6", "M7"),
            )
        try:
            return reference + timedelta(milliseconds=milliseconds), None
        except OverflowError:
            return None, ValidationIssue(
                "context.event_time_out_of_range",
                "mission reference date plus event milliseconds is not representable",
                ("M5", "M6", "M7", time_field),
            )

    def feed(
        self, data: bytes | bytearray | memoryview
    ) -> tuple[ContextualSegmentEvent, ...]:
        """Consume bytes and return contextual events from completed packets."""

        contextual: list[ContextualSegmentEvent] = []
        for packet in self._packets.feed(data):
            mission_key = self._mission_key(packet.header)
            for event in iter_packet_events(packet):
                value = event.value
                context_update = None
                if isinstance(value, MissionSegment):
                    context_update = self._put_mission(mission_key, value)
                mission = self._missions.get(mission_key)
                if mission is not None:
                    self._missions.move_to_end(mission_key)

                if isinstance(value, JobDefinitionSegment):
                    context_update = self._put_job(
                        self._job_key(packet.header, value.job_id), value
                    )
                job_key = self._job_key(packet.header)
                job = self._jobs.get(job_key)
                if job is not None:
                    self._jobs.move_to_end(job_key)

                event_time_utc, event_time_issue = self._event_time(value, mission)

                contextual.append(
                    ContextualSegmentEvent(
                        packet_index=self._packet_index,
                        event=event,
                        mission=mission,
                        job_definition=job,
                        event_time_utc=event_time_utc,
                        context_update=context_update,
                        event_time_issue=event_time_issue,
                    )
                )
            self._packet_index += 1
        return tuple(contextual)

    def finish(self) -> None:
        """Finalize the underlying packet stream."""

        self._packets.finish()

    def reset(self) -> None:
        """Reset byte-stream and all retained mission/job context."""

        self._packets.reset()
        self._missions.clear()
        self._jobs.clear()
        self._packet_index = 0
