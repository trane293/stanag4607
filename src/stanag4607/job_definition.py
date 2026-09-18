"""Typed Job Definition Segment support."""

from __future__ import annotations

from dataclasses import dataclass
from struct import Struct

from .angles import BinaryAngle, SignedBinaryAngle
from .errors import DecodeError
from .packet import Segment

JOB_DEFINITION_SEGMENT_TYPE = 5
JOB_DEFINITION_PAYLOAD_SIZE = 68
_PREFIX = Struct(">IB6sBB")
_TAIL = Struct(">BHHHHBHHHHBBBBB")


def _uint(name: str, value: int, bits: int) -> None:
    if not isinstance(value, int) or not 0 <= value < 2**bits:
        raise ValueError(f"{name} must be an unsigned {bits}-bit integer")


def _optional(raw: int, sentinel: int) -> int | None:
    return None if raw == sentinel else raw


@dataclass(frozen=True, slots=True)
class JobDefinitionSegment:
    """Job fields J1-J28 with exact sentinels and geospatial context."""

    job_id: int
    sensor_type: int
    sensor_model: bytes
    target_filtering: int
    priority: int
    bounding_area: tuple[tuple[SignedBinaryAngle, BinaryAngle], ...]
    radar_mode: int
    nominal_revisit_interval_deciseconds: int
    nominal_sensor_position_along_track_uncertainty_raw: int
    nominal_sensor_position_cross_track_uncertainty_raw: int
    nominal_sensor_position_altitude_uncertainty_raw: int
    nominal_sensor_track_uncertainty_raw: int
    nominal_sensor_speed_uncertainty_raw: int
    nominal_slant_range_standard_deviation_raw: int
    nominal_cross_range_standard_deviation_raw: int
    nominal_radial_velocity_standard_deviation_raw: int
    nominal_minimum_detectable_velocity_raw: int
    nominal_detection_probability_raw: int
    nominal_false_alarm_density_raw: int
    terrain_elevation_model: int
    geoid_model: int

    def __post_init__(self) -> None:
        for name, value, bits in (
            ("job_id", self.job_id, 32),
            ("sensor_type", self.sensor_type, 8),
            ("target_filtering", self.target_filtering, 8),
            ("priority", self.priority, 8),
            ("radar_mode", self.radar_mode, 8),
            ("nominal_revisit_interval_deciseconds", self.nominal_revisit_interval_deciseconds, 16),
            (
                "nominal_sensor_position_along_track_uncertainty_raw",
                self.nominal_sensor_position_along_track_uncertainty_raw,
                16,
            ),
            (
                "nominal_sensor_position_cross_track_uncertainty_raw",
                self.nominal_sensor_position_cross_track_uncertainty_raw,
                16,
            ),
            (
                "nominal_sensor_position_altitude_uncertainty_raw",
                self.nominal_sensor_position_altitude_uncertainty_raw,
                16,
            ),
            ("nominal_sensor_track_uncertainty_raw", self.nominal_sensor_track_uncertainty_raw, 8),
            ("nominal_sensor_speed_uncertainty_raw", self.nominal_sensor_speed_uncertainty_raw, 16),
            (
                "nominal_slant_range_standard_deviation_raw",
                self.nominal_slant_range_standard_deviation_raw,
                16,
            ),
            (
                "nominal_cross_range_standard_deviation_raw",
                self.nominal_cross_range_standard_deviation_raw,
                16,
            ),
            (
                "nominal_radial_velocity_standard_deviation_raw",
                self.nominal_radial_velocity_standard_deviation_raw,
                16,
            ),
            (
                "nominal_minimum_detectable_velocity_raw",
                self.nominal_minimum_detectable_velocity_raw,
                8,
            ),
            ("nominal_detection_probability_raw", self.nominal_detection_probability_raw, 8),
            ("nominal_false_alarm_density_raw", self.nominal_false_alarm_density_raw, 8),
            ("terrain_elevation_model", self.terrain_elevation_model, 8),
            ("geoid_model", self.geoid_model, 8),
        ):
            _uint(name, value, bits)
        if not isinstance(self.sensor_model, bytes) or len(self.sensor_model) != 6:
            raise ValueError("sensor_model must be exactly 6 bytes")
        if len(self.bounding_area) != 4:
            raise ValueError("bounding_area must contain exactly four points")
        for latitude, longitude in self.bounding_area:
            if latitude.bits != 32 or longitude.bits != 32:
                raise ValueError("bounding_area coordinates must be SA32/BA32 values")

    @property
    def nominal_sensor_position_along_track_uncertainty_decimeters(self) -> int | None:
        return _optional(self.nominal_sensor_position_along_track_uncertainty_raw, 0xFFFF)

    @property
    def nominal_sensor_position_cross_track_uncertainty_decimeters(self) -> int | None:
        return _optional(self.nominal_sensor_position_cross_track_uncertainty_raw, 0xFFFF)

    @property
    def nominal_sensor_position_altitude_uncertainty_decimeters(self) -> int | None:
        return _optional(self.nominal_sensor_position_altitude_uncertainty_raw, 0xFFFF)

    @property
    def nominal_sensor_track_uncertainty_degrees(self) -> int | None:
        return _optional(self.nominal_sensor_track_uncertainty_raw, 0xFF)

    @property
    def nominal_sensor_speed_uncertainty_millimeters_per_second(self) -> int | None:
        return _optional(self.nominal_sensor_speed_uncertainty_raw, 0xFFFF)

    @property
    def nominal_slant_range_standard_deviation_centimeters(self) -> int | None:
        return _optional(self.nominal_slant_range_standard_deviation_raw, 0xFFFF)

    @property
    def nominal_cross_range_standard_deviation(self) -> BinaryAngle | None:
        if self.nominal_cross_range_standard_deviation_raw >= 0x8000:
            return None
        return BinaryAngle(self.nominal_cross_range_standard_deviation_raw, 16)

    @property
    def nominal_radial_velocity_standard_deviation_centimeters_per_second(self) -> int | None:
        return _optional(self.nominal_radial_velocity_standard_deviation_raw, 0xFFFF)

    @property
    def nominal_minimum_detectable_velocity_decimeters_per_second(self) -> int | None:
        return _optional(self.nominal_minimum_detectable_velocity_raw, 0xFF)

    @property
    def nominal_detection_probability_percent(self) -> int | None:
        return _optional(self.nominal_detection_probability_raw, 0xFF)

    @property
    def nominal_false_alarm_density_negative_decibels(self) -> int | None:
        return _optional(self.nominal_false_alarm_density_raw, 0xFF)

    def to_segment(self) -> Segment:
        """Encode J1-J28 as a type-5 segment without changing sentinels."""

        payload = _PREFIX.pack(
            self.job_id,
            self.sensor_type,
            self.sensor_model,
            self.target_filtering,
            self.priority,
        )
        payload += b"".join(
            latitude.to_bytes() + longitude.to_bytes()
            for latitude, longitude in self.bounding_area
        )
        payload += _TAIL.pack(
            self.radar_mode,
            self.nominal_revisit_interval_deciseconds,
            self.nominal_sensor_position_along_track_uncertainty_raw,
            self.nominal_sensor_position_cross_track_uncertainty_raw,
            self.nominal_sensor_position_altitude_uncertainty_raw,
            self.nominal_sensor_track_uncertainty_raw,
            self.nominal_sensor_speed_uncertainty_raw,
            self.nominal_slant_range_standard_deviation_raw,
            self.nominal_cross_range_standard_deviation_raw,
            self.nominal_radial_velocity_standard_deviation_raw,
            self.nominal_minimum_detectable_velocity_raw,
            self.nominal_detection_probability_raw,
            self.nominal_false_alarm_density_raw,
            self.terrain_elevation_model,
            self.geoid_model,
        )
        return Segment(JOB_DEFINITION_SEGMENT_TYPE, payload)


def decode_job_definition_segment(segment: Segment) -> JobDefinitionSegment:
    """Decode a complete type-5 Job Definition Segment payload."""

    if segment.segment_type != JOB_DEFINITION_SEGMENT_TYPE:
        raise DecodeError(
            f"job definition decoder requires segment type {JOB_DEFINITION_SEGMENT_TYPE}, "
            f"received {segment.segment_type}"
        )
    if len(segment.payload) != JOB_DEFINITION_PAYLOAD_SIZE:
        raise DecodeError(
            f"job definition payload must be exactly {JOB_DEFINITION_PAYLOAD_SIZE} bytes, "
            f"received {len(segment.payload)}"
        )
    prefix = _PREFIX.unpack_from(segment.payload)
    offset = _PREFIX.size
    points: list[tuple[SignedBinaryAngle, BinaryAngle]] = []
    for _ in range(4):
        points.append(
            (
                SignedBinaryAngle.from_bytes(segment.payload[offset : offset + 4]),
                BinaryAngle.from_bytes(segment.payload[offset + 4 : offset + 8]),
            )
        )
        offset += 8
    tail = _TAIL.unpack_from(segment.payload, offset)
    return JobDefinitionSegment(
        job_id=prefix[0],
        sensor_type=prefix[1],
        sensor_model=prefix[2],
        target_filtering=prefix[3],
        priority=prefix[4],
        bounding_area=tuple(points),
        radar_mode=tail[0],
        nominal_revisit_interval_deciseconds=tail[1],
        nominal_sensor_position_along_track_uncertainty_raw=tail[2],
        nominal_sensor_position_cross_track_uncertainty_raw=tail[3],
        nominal_sensor_position_altitude_uncertainty_raw=tail[4],
        nominal_sensor_track_uncertainty_raw=tail[5],
        nominal_sensor_speed_uncertainty_raw=tail[6],
        nominal_slant_range_standard_deviation_raw=tail[7],
        nominal_cross_range_standard_deviation_raw=tail[8],
        nominal_radial_velocity_standard_deviation_raw=tail[9],
        nominal_minimum_detectable_velocity_raw=tail[10],
        nominal_detection_probability_raw=tail[11],
        nominal_false_alarm_density_raw=tail[12],
        terrain_elevation_model=tail[13],
        geoid_model=tail[14],
    )
