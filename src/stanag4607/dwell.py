"""Dwell Segment presence and layout primitives."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal, cast

from .angles import BinaryAngle, SignedBinaryAngle
from .errors import DecodeError
from .packet import Segment

DWELL_SEGMENT_TYPE = 2
DEFAULT_MAX_TARGET_REPORTS = 4_096

_DWELL_FIELD_WIDTHS = {
    2: 2,
    3: 2,
    4: 1,
    5: 2,
    6: 4,
    7: 4,
    8: 4,
    9: 4,
    10: 4,
    11: 4,
    12: 4,
    13: 4,
    14: 2,
    15: 2,
    16: 4,
    17: 1,
    18: 1,
    19: 2,
    20: 2,
    21: 2,
    22: 2,
    23: 2,
    24: 4,
    25: 4,
    26: 2,
    27: 2,
    28: 2,
    29: 2,
    30: 2,
    31: 1,
}

_TARGET_FIELD_WIDTHS = {
    1: 2,
    2: 4,
    3: 4,
    4: 2,
    5: 2,
    6: 2,
    7: 2,
    8: 2,
    9: 1,
    10: 1,
    11: 1,
    12: 2,
    13: 2,
    14: 1,
    15: 2,
    16: 1,
    17: 4,
    18: 1,
}

_MANDATORY_DWELL_FIELDS = (2, 3, 4, 5, 6, 7, 8, 9, 24, 25, 26, 27)


@dataclass(frozen=True, slots=True)
class DwellExistenceMask:
    """The exact D1 mask with helpers for Figure 3-1 field positions."""

    raw: int

    def __post_init__(self) -> None:
        if not isinstance(self.raw, int) or not 0 <= self.raw < 2**64:
            raise ValueError("raw must be an unsigned 64-bit integer")

    @classmethod
    def from_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> DwellExistenceMask:
        """Decode the eight high-order-byte-first mask bytes."""

        encoded = bytes(data)
        if len(encoded) != 8:
            raise ValueError("dwell existence mask must be exactly 8 bytes")
        return cls(int.from_bytes(encoded, "big"))

    def to_bytes(self) -> bytes:
        """Encode the mask high-order byte first."""

        return self.raw.to_bytes(8, "big")

    def has_dwell(self, field: int) -> bool:
        """Return whether D2 through D31 is marked present."""

        if field not in _DWELL_FIELD_WIDTHS:
            raise ValueError("dwell field must be D2 through D31")
        return bool(self.raw & (1 << (65 - field)))

    def has_target(self, field: int) -> bool:
        """Return whether D32.1 through D32.18 is marked present."""

        if field not in _TARGET_FIELD_WIDTHS:
            raise ValueError("target field must be D32.1 through D32.18")
        return bool(self.raw & (1 << (34 - field)))

    @property
    def present_dwell_fields(self) -> tuple[int, ...]:
        """Present Dwell fields in wire order."""

        return tuple(field for field in _DWELL_FIELD_WIDTHS if self.has_dwell(field))

    @property
    def present_target_fields(self) -> tuple[int, ...]:
        """Present Target Report fields in wire order."""

        return tuple(field for field in _TARGET_FIELD_WIDTHS if self.has_target(field))

    @property
    def missing_mandatory_fields(self) -> tuple[int, ...]:
        """Mandatory Dwell fields whose mask bits are clear."""

        return tuple(field for field in _MANDATORY_DWELL_FIELDS if not self.has_dwell(field))

    @property
    def spare_bits(self) -> int:
        """Return the sixteen low-order spare bits unchanged."""

        return self.raw & 0xFFFF

    @property
    def dwell_fields_size(self) -> int:
        """Encoded bytes after D1 and before target reports."""

        return sum(_DWELL_FIELD_WIDTHS[field] for field in self.present_dwell_fields)

    @property
    def target_report_size(self) -> int:
        """Encoded bytes in each Target Report selected by this mask."""

        return sum(_TARGET_FIELD_WIDTHS[field] for field in self.present_target_fields)


def _validate_encoded_fields(
    name: str,
    fields: tuple[bytes, ...],
    present: tuple[int, ...],
    widths: dict[int, int],
) -> None:
    if len(fields) != len(present):
        raise ValueError(f"{name} count does not match existence mask")
    for field, encoded in zip(present, fields, strict=True):
        if not isinstance(encoded, bytes) or len(encoded) != widths[field]:
            raise ValueError(f"{name} D{field} must be exactly {widths[field]} bytes")


@dataclass(frozen=True, slots=True)
class TargetReport:
    """One lossless D32 Target Report interpreted by its parent D1 mask."""

    mask: DwellExistenceMask
    fields: tuple[bytes, ...]

    def __post_init__(self) -> None:
        _validate_encoded_fields(
            "target field", self.fields, self.mask.present_target_fields, _TARGET_FIELD_WIDTHS
        )

    def field_bytes(self, field: int) -> bytes | None:
        """Return exact bytes for D32.n, or ``None`` when absent."""

        if field not in _TARGET_FIELD_WIDTHS:
            raise ValueError("target field must be D32.1 through D32.18")
        try:
            index = self.mask.present_target_fields.index(field)
        except ValueError:
            return None
        return self.fields[index]

    def _unsigned(self, field: int) -> int | None:
        encoded = self.field_bytes(field)
        return None if encoded is None else int.from_bytes(encoded, "big")

    def _signed(self, field: int) -> int | None:
        encoded = self.field_bytes(field)
        return None if encoded is None else int.from_bytes(encoded, "big", signed=True)

    @property
    def report_index(self) -> int | None:
        return self._unsigned(1)

    @property
    def high_resolution_latitude(self) -> SignedBinaryAngle | None:
        encoded = self.field_bytes(2)
        return None if encoded is None else SignedBinaryAngle.from_bytes(encoded)

    @property
    def high_resolution_longitude(self) -> BinaryAngle | None:
        encoded = self.field_bytes(3)
        return None if encoded is None else BinaryAngle.from_bytes(encoded)

    @property
    def delta_latitude(self) -> int | None:
        return self._signed(4)

    @property
    def delta_longitude(self) -> int | None:
        return self._signed(5)

    @property
    def geodetic_height_meters(self) -> int | None:
        return self._signed(6)

    @property
    def radial_velocity_centimeters_per_second(self) -> int | None:
        return self._signed(7)

    @property
    def wrap_velocity_centimeters_per_second(self) -> int | None:
        return self._unsigned(8)

    @property
    def signal_to_noise_ratio_decibels(self) -> int | None:
        return self._signed(9)

    @property
    def classification(self) -> int | None:
        return self._unsigned(10)

    @property
    def classification_probability_percent(self) -> int | None:
        return self._unsigned(11)

    @property
    def slant_range_uncertainty_centimeters(self) -> int | None:
        return self._unsigned(12)

    @property
    def cross_range_uncertainty_decimeters(self) -> int | None:
        return self._unsigned(13)

    @property
    def height_uncertainty_meters(self) -> int | None:
        return self._unsigned(14)

    @property
    def radial_velocity_uncertainty_centimeters_per_second(self) -> int | None:
        return self._unsigned(15)

    @property
    def truth_tag_application(self) -> int | None:
        return self._unsigned(16)

    @property
    def truth_tag_entity(self) -> int | None:
        return self._unsigned(17)

    @property
    def radar_cross_section_decibels(self) -> Fraction | None:
        raw = self._signed(18)
        return None if raw is None else Fraction(raw, 2)

    def to_bytes(self) -> bytes:
        """Return all selected D32 fields in wire order."""

        return b"".join(self.fields)


@dataclass(frozen=True, slots=True)
class TargetLocation:
    """One exact target location and its STANAG 4607 wire representation."""

    latitude: SignedBinaryAngle
    longitude: BinaryAngle
    encoding: Literal["high_resolution", "reduced"]


@dataclass(frozen=True, slots=True)
class DwellSegment:
    """A lossless Dwell body with exact core time and geometry accessors."""

    mask: DwellExistenceMask
    fields: tuple[bytes, ...]
    targets: tuple[TargetReport, ...]

    def __post_init__(self) -> None:
        if self.mask.missing_mandatory_fields:
            missing = ", ".join(f"D{field}" for field in self.mask.missing_mandatory_fields)
            raise ValueError(f"mandatory Dwell fields absent: {missing}")
        _validate_encoded_fields(
            "dwell field", self.fields, self.mask.present_dwell_fields, _DWELL_FIELD_WIDTHS
        )
        if self.last_dwell not in (0, 1):
            raise ValueError("D4 last dwell flag must be 0 or 1")
        if self.target_report_count != len(self.targets):
            raise ValueError("D5 target report count does not match decoded targets")
        if any(target.mask != self.mask for target in self.targets):
            raise ValueError("target report mask does not match Dwell mask")

    def field_bytes(self, field: int) -> bytes | None:
        """Return exact bytes for D2-D31, or ``None`` when absent."""

        if field not in _DWELL_FIELD_WIDTHS:
            raise ValueError("dwell field must be D2 through D31")
        try:
            index = self.mask.present_dwell_fields.index(field)
        except ValueError:
            return None
        return self.fields[index]

    def _required_uint(self, field: int) -> int:
        encoded = self.field_bytes(field)
        return int.from_bytes(cast(bytes, encoded), "big")

    def _optional_uint(self, field: int) -> int | None:
        encoded = self.field_bytes(field)
        return None if encoded is None else int.from_bytes(encoded, "big")

    def _optional_signed(self, field: int) -> int | None:
        encoded = self.field_bytes(field)
        return None if encoded is None else int.from_bytes(encoded, "big", signed=True)

    def _optional_binary_angle(self, field: int) -> BinaryAngle | None:
        encoded = self.field_bytes(field)
        return None if encoded is None else BinaryAngle.from_bytes(encoded)

    def _optional_signed_binary_angle(self, field: int) -> SignedBinaryAngle | None:
        encoded = self.field_bytes(field)
        return None if encoded is None else SignedBinaryAngle.from_bytes(encoded)

    @property
    def revisit_index(self) -> int:
        return self._required_uint(2)

    @property
    def dwell_index(self) -> int:
        return self._required_uint(3)

    @property
    def last_dwell(self) -> int:
        return self._required_uint(4)

    @property
    def target_report_count(self) -> int:
        return self._required_uint(5)

    @property
    def dwell_time_milliseconds(self) -> int:
        return self._required_uint(6)

    @property
    def sensor_latitude(self) -> SignedBinaryAngle:
        return SignedBinaryAngle.from_bytes(self.field_bytes(7) or b"")

    @property
    def sensor_longitude(self) -> BinaryAngle:
        return BinaryAngle.from_bytes(self.field_bytes(8) or b"")

    @property
    def sensor_altitude_centimeters(self) -> int:
        return int.from_bytes(self.field_bytes(9) or b"", "big", signed=True)

    @property
    def latitude_scale(self) -> SignedBinaryAngle | None:
        encoded = self.field_bytes(10)
        return None if encoded is None else SignedBinaryAngle.from_bytes(encoded)

    @property
    def longitude_scale(self) -> BinaryAngle | None:
        encoded = self.field_bytes(11)
        return None if encoded is None else BinaryAngle.from_bytes(encoded)

    @property
    def sensor_position_along_track_uncertainty_centimeters(self) -> int | None:
        return self._optional_uint(12)

    @property
    def sensor_position_cross_track_uncertainty_centimeters(self) -> int | None:
        return self._optional_uint(13)

    @property
    def sensor_position_altitude_uncertainty_centimeters(self) -> int | None:
        return self._optional_uint(14)

    @property
    def sensor_track(self) -> BinaryAngle | None:
        return self._optional_binary_angle(15)

    @property
    def sensor_speed_millimeters_per_second(self) -> int | None:
        return self._optional_uint(16)

    @property
    def sensor_vertical_velocity_decimeters_per_second(self) -> int | None:
        return self._optional_signed(17)

    @property
    def sensor_track_uncertainty_degrees(self) -> int | None:
        return self._optional_uint(18)

    @property
    def sensor_speed_uncertainty_millimeters_per_second(self) -> int | None:
        return self._optional_uint(19)

    @property
    def sensor_vertical_velocity_uncertainty_centimeters_per_second(self) -> int | None:
        return self._optional_uint(20)

    @property
    def platform_heading(self) -> BinaryAngle | None:
        return self._optional_binary_angle(21)

    @property
    def platform_pitch(self) -> SignedBinaryAngle | None:
        return self._optional_signed_binary_angle(22)

    @property
    def platform_roll(self) -> SignedBinaryAngle | None:
        return self._optional_signed_binary_angle(23)

    @property
    def center_latitude(self) -> SignedBinaryAngle:
        return SignedBinaryAngle.from_bytes(self.field_bytes(24) or b"")

    @property
    def center_longitude(self) -> BinaryAngle:
        return BinaryAngle.from_bytes(self.field_bytes(25) or b"")

    @property
    def range_half_extent_kilometers(self) -> Fraction:
        return Fraction(self._required_uint(26), 128)

    @property
    def angle_half_extent(self) -> BinaryAngle:
        return BinaryAngle.from_bytes(self.field_bytes(27) or b"")

    @property
    def sensor_heading(self) -> BinaryAngle | None:
        return self._optional_binary_angle(28)

    @property
    def sensor_pitch(self) -> SignedBinaryAngle | None:
        return self._optional_signed_binary_angle(29)

    @property
    def sensor_roll(self) -> SignedBinaryAngle | None:
        return self._optional_signed_binary_angle(30)

    @property
    def minimum_detectable_velocity_decimeters_per_second(self) -> int | None:
        return self._optional_uint(31)

    def target_location(self, target_index: int) -> TargetLocation | None:
        """Return an exact direct or reconstructed target position when complete."""

        target = self.targets[target_index]
        latitude = target.high_resolution_latitude
        longitude = target.high_resolution_longitude
        if latitude is not None and longitude is not None:
            return TargetLocation(latitude, longitude, "high_resolution")

        delta_latitude = target.delta_latitude
        delta_longitude = target.delta_longitude
        latitude_scale = self.latitude_scale
        longitude_scale = self.longitude_scale
        if (
            delta_latitude is None
            or delta_longitude is None
            or latitude_scale is None
            or longitude_scale is None
        ):
            return None

        latitude_raw = self.center_latitude.raw + delta_latitude * latitude_scale.raw
        minimum = -(2**31)
        maximum = 2**31 - 1
        if not minimum <= latitude_raw <= maximum:
            raise ValueError("reconstructed target latitude exceeds SA32 range")
        longitude_raw = (
            self.center_longitude.raw + delta_longitude * longitude_scale.raw
        ) % 2**32
        return TargetLocation(
            SignedBinaryAngle(latitude_raw, 32),
            BinaryAngle(longitude_raw, 32),
            "reduced",
        )

    def to_segment(self) -> Segment:
        """Re-encode D1, D2-D31, and every D32 report exactly."""

        payload = self.mask.to_bytes() + b"".join(self.fields)
        payload += b"".join(target.to_bytes() for target in self.targets)
        return Segment(DWELL_SEGMENT_TYPE, payload)


def _read_fields(
    payload: bytes,
    offset: int,
    present: tuple[int, ...],
    widths: dict[int, int],
) -> tuple[tuple[bytes, ...], int]:
    fields: list[bytes] = []
    for field in present:
        end = offset + widths[field]
        fields.append(payload[offset:end])
        offset = end
    return tuple(fields), offset


def decode_dwell_segment(
    segment: Segment, *, max_target_reports: int = DEFAULT_MAX_TARGET_REPORTS
) -> DwellSegment:
    """Decode a type-2 Dwell Segment using D1 to determine every field width."""

    if max_target_reports < 0:
        raise ValueError("max_target_reports must not be negative")
    if segment.segment_type != DWELL_SEGMENT_TYPE:
        raise DecodeError(
            f"dwell decoder requires segment type {DWELL_SEGMENT_TYPE}, "
            f"received {segment.segment_type}"
        )
    payload = segment.payload
    if len(payload) < 8:
        raise DecodeError("truncated Dwell existence mask")
    mask = DwellExistenceMask.from_bytes(payload[:8])
    if mask.missing_mandatory_fields:
        missing = ", ".join(f"D{field}" for field in mask.missing_mandatory_fields)
        raise DecodeError(f"mandatory Dwell fields absent: {missing}")

    prefix_size = 8 + mask.dwell_fields_size
    if len(payload) < prefix_size:
        raise DecodeError(
            f"truncated Dwell fields: need {prefix_size} bytes, received {len(payload)}"
        )
    fields, offset = _read_fields(payload, 8, mask.present_dwell_fields, _DWELL_FIELD_WIDTHS)
    count_index = mask.present_dwell_fields.index(5)
    target_count = int.from_bytes(fields[count_index], "big")
    if target_count > max_target_reports:
        raise DecodeError(
            f"target report count {target_count} exceeds configured limit {max_target_reports}"
        )
    if target_count and mask.target_report_size == 0:
        raise DecodeError("D5 is positive but the mask selects no Target Report fields")

    expected_size = prefix_size + target_count * mask.target_report_size
    if len(payload) < expected_size:
        raise DecodeError(
            f"truncated Target Reports: need {expected_size} bytes, received {len(payload)}"
        )
    if len(payload) > expected_size:
        raise DecodeError(
            f"trailing Dwell bytes: expected {expected_size}, received {len(payload)}"
        )

    targets: list[TargetReport] = []
    for _ in range(target_count):
        target_fields, offset = _read_fields(
            payload, offset, mask.present_target_fields, _TARGET_FIELD_WIDTHS
        )
        targets.append(TargetReport(mask, target_fields))

    try:
        return DwellSegment(mask, fields, tuple(targets))
    except ValueError as error:
        raise DecodeError(f"invalid Dwell Segment: {error}") from error
