"""Bounded, conservative Dwell sequence diagnostics."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

from .dwell import DwellSegment
from .events import SegmentEvent
from .hrr import HrrSegment
from .validation import ValidationIssue

DEFAULT_MAX_CONTINUITY_JOBS = 1_024
_JobKey = tuple[bytes, int, int]


@dataclass(frozen=True, slots=True)
class _SequenceState:
    revisit_index: int
    dwell_index: int
    last_dwell: int


@dataclass(frozen=True, slots=True)
class _JobState:
    dwell: _SequenceState | None = None
    hrr: _SequenceState | None = None


class StreamContinuityValidator:
    """Track locally decidable Dwell ordering for a bounded set of jobs."""

    def __init__(self, *, max_jobs: int = DEFAULT_MAX_CONTINUITY_JOBS) -> None:
        if max_jobs <= 0:
            raise ValueError("max_jobs must be positive")
        self._max_jobs = max_jobs
        self._states: OrderedDict[_JobKey, _JobState] = OrderedDict()

    @property
    def tracked_jobs(self) -> int:
        return len(self._states)

    def observe(self, event: SegmentEvent) -> tuple[ValidationIssue, ...]:
        """Observe one event and report only unambiguous sequence violations."""

        value = event.value
        if isinstance(value, DwellSegment):
            kind = "dwell"
            field_prefix = "D"
            gap_code = "stream.dwell_index_gap"
            after_last_code = "stream.dwell_after_last"
            first_dwell_code = "stream.revisit_first_dwell_index"
        elif isinstance(value, HrrSegment):
            kind = "hrr"
            field_prefix = "H"
            gap_code = "stream.hrr_dwell_index_gap"
            after_last_code = "stream.hrr_after_last"
            first_dwell_code = "stream.hrr_revisit_first_dwell_index"
        else:
            return ()
        header = event.packet_header
        key = header.platform_id, header.mission_id, header.job_id
        job_state = self._states.get(key, _JobState())
        previous = job_state.dwell if kind == "dwell" else job_state.hrr
        issues: list[ValidationIssue] = []
        if previous is not None:
            if value.revisit_index == previous.revisit_index:
                expected = (previous.dwell_index + 1) & 0xFFFF
                if value.dwell_index != expected:
                    issues.append(
                        ValidationIssue(
                            gap_code,
                            f"{field_prefix}3 is {value.dwell_index}; expected {expected} "
                            "in this revisit",
                            (f"{field_prefix}2", f"{field_prefix}3"),
                        )
                    )
                if previous.last_dwell == 1:
                    issues.append(
                        ValidationIssue(
                            after_last_code,
                            f"a {field_prefix}RR Dwell followed {field_prefix}4=1 within "
                            "the same revisit"
                            if kind == "hrr"
                            else "a Dwell followed D4=1 within the same revisit",
                            (f"{field_prefix}2", f"{field_prefix}4"),
                        )
                    )
            elif value.dwell_index != 0:
                issues.append(
                    ValidationIssue(
                        first_dwell_code,
                        "the first observed Dwell of a new revisit must have "
                        f"{field_prefix}3=0",
                        (f"{field_prefix}2", f"{field_prefix}3"),
                    )
                )
        current = _SequenceState(
            value.revisit_index, value.dwell_index, value.last_dwell
        )
        self._states[key] = (
            _JobState(dwell=current, hrr=job_state.hrr)
            if kind == "dwell"
            else _JobState(dwell=job_state.dwell, hrr=current)
        )
        self._states.move_to_end(key)
        if len(self._states) > self._max_jobs:
            self._states.popitem(last=False)
        return tuple(issues)

    def reset(self) -> None:
        """Discard every retained job sequence."""

        self._states.clear()
