"""High-Range Resolution Segment presence and layout primitives."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import cast

from .binary_decimals import SignedBinaryDecimal, SignedHertzDecimal
from .errors import DecodeError
from .packet import Segment

HRR_SEGMENT_TYPE = 3
DEFAULT_MAX_HRR_SCATTERER_BYTES = 65_535

_HRR_FIELD_WIDTHS = {
    2: 2,
    3: 2,
    4: 1,
    5: 2,
    6: 2,
    7: 2,
    8: 2,
    9: 1,
    10: 1,
    11: 2,
    12: 2,
    13: 4,
    14: 4,
    15: 4,
    16: 1,
    17: 1,
    18: 1,
    19: 2,
    20: 1,
    21: 2,
    22: 4,
    23: 1,
    24: 1,
    25: 1,
    26: 1,
    27: 1,
    28: 4,
    29: 1,
    30: 4,
    31: 4,
}
_SCATTERER_FIELDS = (1, 2, 3, 4)
_MANDATORY_HRR_FIELDS = (2, 3, 4, 8, 10, 11, 12, 13, 14, 16, 17, 18, 19, 23, 24, 25, 26)


@dataclass(frozen=True, slots=True)
class HrrExistenceMask:
    """The exact H1 mask with helpers for Figure 3-4 field positions."""

    raw: int

    def __post_init__(self) -> None:
        if not isinstance(self.raw, int) or not 0 <= self.raw < 2**40:
            raise ValueError("raw must be an unsigned 40-bit integer")

    @classmethod
    def from_bytes(cls, data: bytes | bytearray | memoryview) -> HrrExistenceMask:
        """Decode the five high-order-byte-first mask bytes."""

        encoded = bytes(data)
        if len(encoded) != 5:
            raise ValueError("HRR existence mask must be exactly 5 bytes")
        return cls(int.from_bytes(encoded, "big"))

    def to_bytes(self) -> bytes:
        """Encode the mask high-order byte first."""

        return self.raw.to_bytes(5, "big")

    def has_hrr(self, field: int) -> bool:
        """Return whether H2 through H31 is marked present."""

        if field not in _HRR_FIELD_WIDTHS:
            raise ValueError("HRR field must be H2 through H31")
        return bool(self.raw & (1 << (41 - field)))

    def has_scatterer(self, field: int) -> bool:
        """Return whether H32.1 through H32.4 is marked present."""

        if field not in _SCATTERER_FIELDS:
            raise ValueError("scatterer field must be H32.1 through H32.4")
        return bool(self.raw & (1 << (10 - field)))

    @property
    def present_hrr_fields(self) -> tuple[int, ...]:
        """Present H2-H31 fields in wire order."""

        return tuple(field for field in _HRR_FIELD_WIDTHS if self.has_hrr(field))

    @property
    def present_scatterer_fields(self) -> tuple[int, ...]:
        """Present H32 fields in wire order."""

        return tuple(field for field in _SCATTERER_FIELDS if self.has_scatterer(field))

    @property
    def missing_mandatory_fields(self) -> tuple[str, ...]:
        """Mandatory H fields whose mask bits are clear."""

        missing = tuple(
            f"H{field}" for field in _MANDATORY_HRR_FIELDS if not self.has_hrr(field)
        )
        if not self.has_scatterer(1):
            missing += ("H32.1",)
        return missing

    @property
    def spare_bits(self) -> int:
        """Return the six low-order spare bits unchanged."""

        return self.raw & 0x3F

    @property
    def hrr_fields_size(self) -> int:
        """Encoded bytes after H1 and before scatterer records."""

        return sum(_HRR_FIELD_WIDTHS[field] for field in self.present_hrr_fields)


def _validate_encoded_fields(
    fields: tuple[bytes, ...], present: tuple[int, ...]
) -> None:
    if len(fields) != len(present):
        raise ValueError("HRR field count does not match existence mask")
    for field, encoded in zip(present, fields, strict=True):
        if not isinstance(encoded, bytes) or len(encoded) != _HRR_FIELD_WIDTHS[field]:
            raise ValueError(
                f"HRR field H{field} must be exactly {_HRR_FIELD_WIDTHS[field]} bytes"
            )


@dataclass(frozen=True, slots=True)
class HrrScattererRecord:
    """One exact uncompressed H32 record from Table 3-13."""

    magnitude_bytes: bytes
    phase_bytes: bytes | None = None
    range_index: int | None = None
    doppler_index: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.magnitude_bytes, bytes) or len(self.magnitude_bytes) not in (
            1,
            2,
        ):
            raise ValueError("scatterer magnitude must be exactly one or two bytes")
        if self.phase_bytes is not None and (
            not isinstance(self.phase_bytes, bytes) or len(self.phase_bytes) not in (1, 2)
        ):
            raise ValueError("scatterer phase must be absent or exactly one or two bytes")
        for name, value in (
            ("range_index", self.range_index),
            ("doppler_index", self.doppler_index),
        ):
            if value is not None and (not isinstance(value, int) or not 0 <= value <= 65_535):
                raise ValueError(f"{name} must be absent or an unsigned 16-bit integer")

    @property
    def magnitude_raw(self) -> int:
        """Return exact H32.1 quarter-decibel magnitude units."""

        return int.from_bytes(self.magnitude_bytes, "big")

    @property
    def magnitude_decibels_below_peak(self) -> Fraction:
        """Return H32.1 as a negative distance below peak power."""

        return Fraction(-self.magnitude_raw, 4)

    @property
    def phase_raw(self) -> int | None:
        """Return the exact H32.2 quantized rotation, if present."""

        return None if self.phase_bytes is None else int.from_bytes(self.phase_bytes, "big")

    @property
    def phase_turns(self) -> Fraction | None:
        """Return H32.2 as an exact fraction of one complete rotation."""

        raw = self.phase_raw
        if raw is None:
            return None
        return Fraction(raw, 1 << (8 * len(cast(bytes, self.phase_bytes))))

    def to_bytes(self) -> bytes:
        """Encode the record without changing any quantized value."""

        encoded = self.magnitude_bytes
        if self.phase_bytes is not None:
            encoded += self.phase_bytes
        if self.range_index is not None:
            encoded += self.range_index.to_bytes(2, "big")
        if self.doppler_index is not None:
            encoded += self.doppler_index.to_bytes(2, "big")
        return encoded


@dataclass(frozen=True, slots=True)
class HrrSegment:
    """Lossless H1-H31 metadata with bounded opaque H32 scatterer bytes."""

    mask: HrrExistenceMask
    fields: tuple[bytes, ...]
    scatterer_data: bytes

    def __post_init__(self) -> None:
        if self.mask.missing_mandatory_fields:
            missing = ", ".join(self.mask.missing_mandatory_fields)
            raise ValueError(f"mandatory HRR fields absent: {missing}")
        _validate_encoded_fields(self.fields, self.mask.present_hrr_fields)
        if not isinstance(self.scatterer_data, bytes):
            raise ValueError("scatterer_data must be bytes")

    def field_bytes(self, field: int) -> bytes | None:
        """Return exact bytes for H2-H31, or ``None`` when absent."""

        if field not in _HRR_FIELD_WIDTHS:
            raise ValueError("HRR field must be H2 through H31")
        try:
            index = self.mask.present_hrr_fields.index(field)
        except ValueError:
            return None
        return self.fields[index]

    def _unsigned(self, field: int) -> int | None:
        encoded = self.field_bytes(field)
        return None if encoded is None else int.from_bytes(encoded, "big")

    def _signed(self, field: int) -> int | None:
        encoded = self.field_bytes(field)
        return None if encoded is None else int.from_bytes(encoded, "big", signed=True)

    def _required_unsigned(self, field: int) -> int:
        return int.from_bytes(cast(bytes, self.field_bytes(field)), "big")

    @property
    def revisit_index(self) -> int:
        return self._required_unsigned(2)

    @property
    def dwell_index(self) -> int:
        return self._required_unsigned(3)

    @property
    def last_dwell(self) -> int:
        return self._required_unsigned(4)

    @property
    def mti_report_index(self) -> int | None:
        return self._unsigned(5)

    @property
    def target_scatterer_count(self) -> int | None:
        return self._unsigned(6)

    @property
    def range_sample_count(self) -> int | None:
        return self._unsigned(7)

    @property
    def doppler_sample_count(self) -> int:
        return self._required_unsigned(8)

    @property
    def mean_clutter_power_decibels(self) -> Fraction | None:
        raw = self._unsigned(9)
        return None if raw is None else Fraction(raw, 4)

    @property
    def detection_threshold_decibels(self) -> Fraction:
        return Fraction(-self._required_unsigned(10), 4)

    @property
    def range_resolution(self) -> SignedBinaryDecimal:
        return SignedBinaryDecimal.from_bytes(cast(bytes, self.field_bytes(11)))

    @property
    def range_resolution_centimeters(self) -> Fraction | None:
        value = self.range_resolution.value
        return None if value == 0 else value

    @property
    def range_bin_spacing(self) -> SignedBinaryDecimal:
        return SignedBinaryDecimal.from_bytes(cast(bytes, self.field_bytes(12)))

    @property
    def range_bin_spacing_centimeters(self) -> Fraction | None:
        value = self.range_bin_spacing.value
        return None if value == 0 else value

    @property
    def doppler_resolution(self) -> SignedHertzDecimal:
        return SignedHertzDecimal.from_bytes(cast(bytes, self.field_bytes(13)))

    @property
    def doppler_bin_spacing(self) -> SignedHertzDecimal:
        return SignedHertzDecimal.from_bytes(cast(bytes, self.field_bytes(14)))

    @property
    def center_frequency(self) -> SignedBinaryDecimal | None:
        encoded = self.field_bytes(15)
        return None if encoded is None else SignedBinaryDecimal.from_bytes(encoded)

    @property
    def center_frequency_gigahertz(self) -> Fraction | None:
        value = self.center_frequency
        return None if value is None else value.value

    @property
    def compression_type(self) -> int:
        return self._required_unsigned(16)

    @property
    def range_weighting_function(self) -> int:
        return self._required_unsigned(17)

    @property
    def doppler_weighting_function(self) -> int:
        return self._required_unsigned(18)

    @property
    def maximum_pixel_power(self) -> SignedBinaryDecimal:
        return SignedBinaryDecimal.from_bytes(cast(bytes, self.field_bytes(19)))

    @property
    def maximum_pixel_power_decibels(self) -> Fraction | None:
        value = self.maximum_pixel_power.value
        return None if value == 0 else value

    @property
    def maximum_rcs_decibels(self) -> Fraction | None:
        raw = self._signed(20)
        return None if raw is None else Fraction(raw, 2)

    @property
    def range_origin_meters(self) -> int | None:
        return self._signed(21)

    @property
    def doppler_origin(self) -> SignedHertzDecimal | None:
        encoded = self.field_bytes(22)
        return None if encoded is None else SignedHertzDecimal.from_bytes(encoded)

    @property
    def data_type(self) -> int:
        return self._required_unsigned(23)

    @property
    def processing_mask(self) -> int:
        return self._required_unsigned(24)

    @property
    def magnitude_bytes(self) -> int:
        return self._required_unsigned(25)

    @property
    def phase_bytes(self) -> int:
        return self._required_unsigned(26)

    @property
    def range_extent_pixels(self) -> int | None:
        return self._unsigned(27)

    @property
    def range_to_nearest_edge_centimeters(self) -> int | None:
        return self._unsigned(28)

    @property
    def zero_velocity_bin_index(self) -> int | None:
        return self._unsigned(29)

    @property
    def target_radial_electrical_length(self) -> SignedBinaryDecimal | None:
        encoded = self.field_bytes(30)
        return None if encoded is None else SignedBinaryDecimal.from_bytes(encoded)

    @property
    def target_radial_electrical_length_meters(self) -> Fraction | None:
        value = self.target_radial_electrical_length
        return None if value is None else value.value

    @property
    def electrical_length_uncertainty(self) -> SignedBinaryDecimal | None:
        encoded = self.field_bytes(31)
        return None if encoded is None else SignedBinaryDecimal.from_bytes(encoded)

    @property
    def electrical_length_uncertainty_meters(self) -> Fraction | None:
        value = self.electrical_length_uncertainty
        return None if value is None else value.value

    @property
    def scatterer_records(self) -> tuple[HrrScattererRecord, ...] | None:
        """Decode uncompressed H32 records, or return ``None`` if not interpretable."""

        if self.compression_type != 0:
            return None
        magnitude_width = self.magnitude_bytes
        phase_width = self.phase_bytes
        if magnitude_width not in (1, 2) or phase_width not in (0, 1, 2):
            return None
        has_phase = self.mask.has_scatterer(2)
        if has_phase != (phase_width > 0):
            return None
        has_range = self.mask.has_scatterer(3)
        has_doppler = self.mask.has_scatterer(4)
        record_width = (
            magnitude_width
            + phase_width
            + (2 if has_range else 0)
            + (2 if has_doppler else 0)
        )
        if len(self.scatterer_data) % record_width:
            return None

        records: list[HrrScattererRecord] = []
        for offset in range(0, len(self.scatterer_data), record_width):
            cursor = offset
            magnitude = self.scatterer_data[cursor : cursor + magnitude_width]
            cursor += magnitude_width
            phase = None
            if has_phase:
                phase = self.scatterer_data[cursor : cursor + phase_width]
                cursor += phase_width
            range_index = None
            if has_range:
                range_index = int.from_bytes(self.scatterer_data[cursor : cursor + 2], "big")
                cursor += 2
            doppler_index = None
            if has_doppler:
                doppler_index = int.from_bytes(
                    self.scatterer_data[cursor : cursor + 2], "big"
                )
            records.append(
                HrrScattererRecord(magnitude, phase, range_index, doppler_index)
            )
        return tuple(records)

    def to_segment(self) -> Segment:
        """Encode H1-H31 and the unchanged H32 byte region."""

        payload = self.mask.to_bytes() + b"".join(self.fields) + self.scatterer_data
        return Segment(HRR_SEGMENT_TYPE, payload)


def decode_hrr_segment(
    segment: Segment,
    *,
    max_scatterer_bytes: int = DEFAULT_MAX_HRR_SCATTERER_BYTES,
) -> HrrSegment:
    """Decode H1-H31 while retaining the bounded H32 byte region opaquely."""

    if max_scatterer_bytes < 0:
        raise ValueError("max_scatterer_bytes must not be negative")
    if segment.segment_type != HRR_SEGMENT_TYPE:
        raise DecodeError(
            f"HRR decoder requires type {HRR_SEGMENT_TYPE}, received {segment.segment_type}"
        )
    if len(segment.payload) < 5:
        raise DecodeError("HRR payload requires at least 5 bytes for H1")
    mask = HrrExistenceMask.from_bytes(segment.payload[:5])
    if mask.missing_mandatory_fields:
        missing = ", ".join(mask.missing_mandatory_fields)
        raise DecodeError(f"mandatory HRR fields absent: {missing}")

    fields: list[bytes] = []
    offset = 5
    for field in mask.present_hrr_fields:
        width = _HRR_FIELD_WIDTHS[field]
        end = offset + width
        if end > len(segment.payload):
            raise DecodeError(f"truncated H{field} in HRR payload")
        fields.append(segment.payload[offset:end])
        offset = end

    scatterer_size = len(segment.payload) - offset
    if scatterer_size > max_scatterer_bytes:
        raise DecodeError(
            f"scatterer data size {scatterer_size} exceeds configured limit "
            f"{max_scatterer_bytes}"
        )
    return HrrSegment(mask, tuple(fields), segment.payload[offset:])
