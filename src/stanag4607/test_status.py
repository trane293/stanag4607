"""Typed Test and Status Segment support."""

from __future__ import annotations

from dataclasses import dataclass
from struct import Struct

from .errors import DecodeError
from .packet import Segment

TEST_STATUS_SEGMENT_TYPE = 10
TEST_STATUS_PAYLOAD_SIZE = 14
_TEST_STATUS = Struct(">IHHIBB")

_HARDWARE_FAILURES = (
    (0x80, "antenna"),
    (0x40, "rf_electronics"),
    (0x20, "processor"),
    (0x10, "datalink"),
    (0x08, "calibration_mode"),
)
_MODE_LIMITS = (
    (0x80, "range"),
    (0x40, "azimuth"),
    (0x20, "elevation"),
    (0x10, "temperature"),
)


def _uint(name: str, value: int, bits: int) -> None:
    if not isinstance(value, int) or not 0 <= value < 2**bits:
        raise ValueError(f"{name} must be an unsigned {bits}-bit integer")


@dataclass(frozen=True, slots=True)
class TestStatusSegment:
    """Job-specific platform health fields T1-T6."""

    job_id: int
    revisit_index: int
    dwell_index: int
    dwell_time_milliseconds: int
    hardware_status: int
    mode_status: int

    def __post_init__(self) -> None:
        _uint("job_id", self.job_id, 32)
        _uint("revisit_index", self.revisit_index, 16)
        _uint("dwell_index", self.dwell_index, 16)
        _uint("dwell_time_milliseconds", self.dwell_time_milliseconds, 32)
        _uint("hardware_status", self.hardware_status, 8)
        _uint("mode_status", self.mode_status, 8)

    @property
    def failed_hardware(self) -> tuple[str, ...]:
        """Return hardware whose corresponding T5 failure bit is set."""

        return tuple(name for mask, name in _HARDWARE_FAILURES if self.hardware_status & mask)

    @property
    def exceeded_mode_limits(self) -> tuple[str, ...]:
        """Return operational limits whose corresponding T6 bit is set."""

        return tuple(name for mask, name in _MODE_LIMITS if self.mode_status & mask)

    def to_segment(self) -> Segment:
        """Encode T1-T6 as an exact type-10 segment."""

        return Segment(
            TEST_STATUS_SEGMENT_TYPE,
            _TEST_STATUS.pack(
                self.job_id,
                self.revisit_index,
                self.dwell_index,
                self.dwell_time_milliseconds,
                self.hardware_status,
                self.mode_status,
            ),
        )


def decode_test_status_segment(segment: Segment) -> TestStatusSegment:
    """Decode a complete type-10 Test and Status Segment."""

    if segment.segment_type != TEST_STATUS_SEGMENT_TYPE:
        raise DecodeError(
            f"test/status decoder requires type {TEST_STATUS_SEGMENT_TYPE}, "
            f"received {segment.segment_type}"
        )
    if len(segment.payload) != TEST_STATUS_PAYLOAD_SIZE:
        raise DecodeError(
            f"test/status payload must be exactly {TEST_STATUS_PAYLOAD_SIZE} bytes, "
            f"received {len(segment.payload)}"
        )
    return TestStatusSegment(*_TEST_STATUS.unpack(segment.payload))
