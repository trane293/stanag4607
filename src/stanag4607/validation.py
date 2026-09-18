"""Non-destructive conformance diagnostics for decoded STANAG 4607 values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from .dwell import DwellSegment
from .free_text import FreeTextSegment
from .hrr import HrrSegment
from .job_definition import JobDefinitionSegment
from .mission import MissionSegment
from .packet import Packet, PacketHeader
from .platform_location import PlatformLocationSegment
from .processing_history import ProcessingHistorySegment
from .tasking import JobAcknowledgeSegment, JobRequestSegment
from .test_status import TestStatusSegment


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One deterministic, software-verifiable conformance issue."""

    code: str
    message: str
    fields: tuple[str, ...]


class PacketContextProfile(str, Enum):
    """Explicit packet-level validation profiles; strict Edition A is the default."""

    EDITION_A_V1 = "edition_a_v1"
    LEGACY_VERSION_30_JOB_DEFINITION = "legacy_version_30_job_definition"


def validate_hrr(hrr: HrrSegment) -> tuple[ValidationIssue, ...]:
    """Report mechanically decidable Edition A Version 1 H1-H31 issues."""

    issues: list[ValidationIssue] = []
    if hrr.mask.spare_bits:
        issues.append(
            ValidationIssue(
                "hrr.mask_spare_bits",
                "H1 spare bits must be zero",
                ("H1",),
            )
        )
    if hrr.last_dwell not in (0, 1):
        issues.append(
            ValidationIssue(
                "hrr.last_dwell_flag",
                "H4 must be zero or one",
                ("H4",),
            )
        )
    if hrr.target_scatterer_count is None and hrr.range_sample_count is None:
        issues.append(
            ValidationIssue(
                "hrr.scatterer_count_required",
                "at least one of H6 or H7 must be present",
                ("H6", "H7"),
            )
        )

    data_type = hrr.data_type
    has_report_index = hrr.mti_report_index is not None
    if has_report_index != (1 <= data_type <= 4):
        issues.append(
            ValidationIssue(
                "hrr.mti_report_index_context",
                "H5 must be present exactly for H23 data types 1 through 4",
                ("H5", "H23"),
            )
        )
    if (hrr.field_bytes(9) is not None) != (data_type == 3):
        issues.append(
            ValidationIssue(
                "hrr.mean_clutter_power_required",
                "H9 must be present exactly for sparse HRR data type 3",
                ("H9", "H23"),
            )
        )
    if data_type in (2, 4, 5, 6, 7) and hrr.center_frequency is None:
        issues.append(
            ValidationIssue(
                "hrr.center_frequency_required",
                "H15 is mandatory for H23 data types 2 and 4 through 7",
                ("H15", "H23"),
            )
        )
    if data_type in (4, 6) and (
        hrr.range_origin_meters is None or hrr.doppler_origin is None
    ):
        issues.append(
            ValidationIssue(
                "hrr.origin_required",
                "H21 and H22 are mandatory for H23 data types 4 and 6",
                ("H21", "H22", "H23"),
            )
        )
    if data_type == 3 and not (
        hrr.mask.has_scatterer(3) and hrr.mask.has_scatterer(4)
    ):
        issues.append(
            ValidationIssue(
                "hrr.sparse_indices_required",
                "H32.3 and H32.4 are mandatory for sparse HRR data type 3",
                ("H23", "H32.3", "H32.4"),
            )
        )

    if hrr.range_resolution.value < 0:
        issues.append(
            ValidationIssue(
                "hrr.range_resolution_range",
                "H11 must be nonnegative",
                ("H11",),
            )
        )
    if hrr.range_bin_spacing.value < 0:
        issues.append(
            ValidationIssue(
                "hrr.range_bin_spacing_range",
                "H12 must be nonnegative",
                ("H12",),
            )
        )
    for field, value, code in (
        ("H13", hrr.doppler_resolution.hertz, "hrr.doppler_resolution_range"),
        ("H14", hrr.doppler_bin_spacing.hertz, "hrr.doppler_bin_spacing_range"),
    ):
        if value == 0 or abs(value) > 32_767:
            issues.append(
                ValidationIssue(
                    code,
                    f"{field} magnitude must be greater than zero and at most 32767 Hz",
                    (field,),
                )
            )
    if hrr.center_frequency is not None and hrr.center_frequency.value <= 0:
        issues.append(
            ValidationIssue(
                "hrr.center_frequency_range",
                "H15 must be greater than zero when present",
                ("H15",),
            )
        )
    if hrr.doppler_origin is not None and (
        hrr.doppler_origin.hertz == 0 or abs(hrr.doppler_origin.hertz) > 32_767
    ):
        issues.append(
            ValidationIssue(
                "hrr.doppler_origin_range",
                "H22 magnitude must be greater than zero and at most 32767 Hz",
                ("H22",),
            )
        )
    if hrr.compression_type not in (0, 1):
        issues.append(
            ValidationIssue(
                "hrr.compression_type",
                "H16 must be zero or one",
                ("H16",),
            )
        )
    if hrr.range_weighting_function not in (0, 1, 2):
        issues.append(
            ValidationIssue(
                "hrr.range_weighting_function",
                "H17 must be zero through two",
                ("H17",),
            )
        )
    if hrr.doppler_weighting_function not in (0, 1, 2):
        issues.append(
            ValidationIssue(
                "hrr.doppler_weighting_function",
                "H18 must be zero through two",
                ("H18",),
            )
        )
    if not 0 <= data_type <= 7:
        issues.append(
            ValidationIssue(
                "hrr.data_type",
                "H23 must be zero through seven",
                ("H23",),
            )
        )
    if hrr.processing_mask & 0x1E:
        issues.append(
            ValidationIssue(
                "hrr.processing_mask_reserved_bits",
                "H24 spare bits 1 through 4 must be zero",
                ("H24",),
            )
        )
    if hrr.magnitude_bytes not in (1, 2):
        issues.append(
            ValidationIssue(
                "hrr.magnitude_bytes",
                "H25 must be one or two",
                ("H25",),
            )
        )
    if hrr.phase_bytes not in (0, 1, 2):
        issues.append(
            ValidationIssue(
                "hrr.phase_bytes",
                "H26 must be zero through two",
                ("H26",),
            )
        )
    elif hrr.mask.has_scatterer(2) != (hrr.phase_bytes > 0):
        issues.append(
            ValidationIssue(
                "hrr.phase_presence",
                "H32.2 must be present exactly when H26 is one or two",
                ("H26", "H32.2"),
            )
        )
    widths_are_valid = hrr.magnitude_bytes in (1, 2) and hrr.phase_bytes in (0, 1, 2)
    phase_presence_is_valid = hrr.mask.has_scatterer(2) == (hrr.phase_bytes > 0)
    scatterers = hrr.scatterer_records
    if (
        hrr.compression_type == 0
        and widths_are_valid
        and phase_presence_is_valid
        and scatterers is None
    ):
        issues.append(
            ValidationIssue(
                "hrr.scatterer_record_size",
                "uncompressed H32 bytes must contain complete scatterer records",
                ("H25", "H26", "H32"),
            )
        )
    elif (
        data_type == 3
        and scatterers is not None
        and hrr.range_sample_count is not None
        and len(scatterers) != hrr.range_sample_count
    ):
        issues.append(
            ValidationIssue(
                "hrr.sparse_scatterer_count",
                "H7 must equal the number of sparse H32 scatterer records",
                ("H7", "H23", "H32"),
            )
        )
    for field, decimal in (
        ("H30", hrr.target_radial_electrical_length),
        ("H31", hrr.electrical_length_uncertainty),
    ):
        if decimal is not None and not 0 <= decimal.value <= 100:
            issues.append(
                ValidationIssue(
                    "hrr.electrical_length_range",
                    f"{field} must be between zero and 100 meters",
                    (field,),
                )
            )
    return tuple(issues)


_VALID_BCS = frozenset((0x0A, 0x0C, 0x0D, *range(0x20, 0x7F)))


def _invalid_bcs_fields(fields: tuple[tuple[str, bytes], ...]) -> tuple[str, ...]:
    return tuple(name for name, value in fields if any(byte not in _VALID_BCS for byte in value))


def _valid_date(year: int, month: int, day: int) -> bool:
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def validate_job_request(request: JobRequestSegment) -> tuple[ValidationIssue, ...]:
    """Report software-verifiable Chapter 4 Job Request issues."""

    issues: list[ValidationIssue] = []
    invalid_bcs = _invalid_bcs_fields(
        (
            ("R1", request.requestor_id),
            ("R2", request.requestor_task_id),
            ("R25", request.sensor_model),
        )
    )
    if invalid_bcs:
        issues.append(
            ValidationIssue(
                "job_request.invalid_bcs",
                "Job Request character fields must use the Basic Character Set",
                invalid_bcs,
            )
        )
    if request.priority > 99:
        issues.append(
            ValidationIssue(
                "job_request.priority_range",
                "R3 must be zero through 99",
                ("R3",),
            )
        )
    if not (
        2000 <= request.earliest_start_year <= 2099
        and 1 <= request.earliest_start_month <= 12
        and 1 <= request.earliest_start_day <= 31
        and _valid_date(
            request.earliest_start_year,
            request.earliest_start_month,
            request.earliest_start_day,
        )
    ):
        issues.append(
            ValidationIssue(
                "job_request.start_date_range",
                "R15-R17 must contain the stated calendar component ranges",
                ("R15", "R16", "R17"),
            )
        )
    if not (
        request.earliest_start_hour <= 23
        and request.earliest_start_minute <= 59
        and request.earliest_start_second <= 60
    ):
        issues.append(
            ValidationIssue(
                "job_request.start_time_range",
                "R18-R20 must contain a valid UTC time component range",
                ("R18", "R19", "R20"),
            )
        )
    if request.request_type not in (0, 1):
        issues.append(
            ValidationIssue(
                "job_request.request_type",
                "R26 must be zero for an initial request or one for cancellation",
                ("R26",),
            )
        )
    return tuple(issues)


def validate_job_acknowledge(
    acknowledge: JobAcknowledgeSegment,
) -> tuple[ValidationIssue, ...]:
    """Report software-verifiable Chapter 4 Job Acknowledge issues."""

    issues: list[ValidationIssue] = []
    invalid_bcs = _invalid_bcs_fields(
        (
            ("A2", acknowledge.requestor_id),
            ("A3", acknowledge.requestor_task_id),
            ("A5", acknowledge.sensor_model),
            ("A25", acknowledge.requestor_nationality),
        )
    )
    if invalid_bcs:
        issues.append(
            ValidationIssue(
                "job_acknowledge.invalid_bcs",
                "Job Acknowledge character fields must use the Basic Character Set",
                invalid_bcs,
            )
        )
    if acknowledge.job_id == 0:
        issues.append(
            ValidationIssue(
                "job_acknowledge.job_id_required",
                "A1 must be nonzero",
                ("A1",),
            )
        )
    if not 1 <= acknowledge.priority <= 99:
        issues.append(
            ValidationIssue(
                "job_acknowledge.priority_range",
                "A6 must be one through 99",
                ("A6",),
            )
        )
    if acknowledge.request_status > 10:
        issues.append(
            ValidationIssue(
                "job_acknowledge.request_status",
                "A18 must be zero through ten",
                ("A18",),
            )
        )
    if not (
        2000 <= acknowledge.start_year <= 2099
        and 1 <= acknowledge.start_month <= 12
        and 1 <= acknowledge.start_day <= 31
        and _valid_date(
            acknowledge.start_year,
            acknowledge.start_month,
            acknowledge.start_day,
        )
    ):
        issues.append(
            ValidationIssue(
                "job_acknowledge.start_date_range",
                "A19-A21 must contain the stated calendar component ranges",
                ("A19", "A20", "A21"),
            )
        )
    if not (
        acknowledge.start_hour <= 23
        and acknowledge.start_minute <= 59
        and acknowledge.start_second <= 60
    ):
        issues.append(
            ValidationIssue(
                "job_acknowledge.start_time_range",
                "A22-A24 must contain a valid UTC time component range",
                ("A22", "A23", "A24"),
            )
        )
    return tuple(issues)


def validate_packet_header(header: PacketHeader) -> tuple[ValidationIssue, ...]:
    """Report Annex A character-repertoire issues in P1, P3, P5, and P8."""

    invalid = _invalid_bcs_fields(
        (
            ("P1", header.version_id),
            ("P3", header.nationality),
            ("P5", header.classification_system),
            ("P8", header.platform_id),
        )
    )
    if not invalid:
        return ()
    return (
        ValidationIssue(
            "packet.invalid_bcs",
            "packet character fields may contain only the Annex A Basic Character Set",
            invalid,
        ),
    )


def validate_mission(mission: MissionSegment) -> tuple[ValidationIssue, ...]:
    """Report Annex A character-repertoire issues in M1, M2, and M4."""

    invalid = _invalid_bcs_fields(
        (
            ("M1", mission.mission_plan),
            ("M2", mission.flight_plan),
            ("M4", mission.platform_configuration),
        )
    )
    if not invalid:
        return ()
    return (
        ValidationIssue(
            "mission.invalid_bcs",
            "Mission character fields may contain only the Annex A Basic Character Set",
            invalid,
        ),
    )


def validate_free_text(message: FreeTextSegment) -> tuple[ValidationIssue, ...]:
    """Report Edition A Version 1 F1-F3 Basic Character Set issues."""

    fields = (
        ("F1", message.originator_id),
        ("F2", message.recipient_id),
        ("F3", message.free_text),
    )
    blank = tuple(name for name, value in fields if value and set(value) == {0x20})
    invalid = _invalid_bcs_fields(fields)
    issues: list[ValidationIssue] = []
    if blank:
        issues.append(
            ValidationIssue(
                "free_text.blank_field",
                "F1-F3 must not contain only space characters",
                blank,
            )
        )
    if invalid:
        issues.append(
            ValidationIssue(
                "free_text.invalid_bcs",
                "F1-F3 may contain only the Annex A Basic Character Set",
                invalid,
            )
        )
    return tuple(issues)


def validate_test_status(status: TestStatusSegment) -> tuple[ValidationIssue, ...]:
    """Report mechanically decidable Edition A Version 1 T1-T6 issues."""

    issues: list[ValidationIssue] = []
    if status.dwell_time_milliseconds > 4_000_000_000:
        issues.append(
            ValidationIssue(
                "test_status.time_range",
                "T4 must not exceed 4,000,000,000 ms",
                ("T4",),
            )
        )
    if status.hardware_status & 0x07:
        issues.append(
            ValidationIssue(
                "test_status.hardware_reserved_bits",
                "T5 spare bits 0 through 2 must be zero",
                ("T5",),
            )
        )
    if status.mode_status & 0x0F:
        issues.append(
            ValidationIssue(
                "test_status.mode_reserved_bits",
                "T6 spare bits 0 through 3 must be zero",
                ("T6",),
            )
        )
    return tuple(issues)


def validate_platform_location(
    location: PlatformLocationSegment,
) -> tuple[ValidationIssue, ...]:
    """Report mechanically decidable Edition A Version 1 L1-L7 issues."""

    issues: list[ValidationIssue] = []
    if location.location_time_milliseconds > 4_000_000_000:
        issues.append(
            ValidationIssue(
                "platform_location.time_range",
                "L1 must not exceed 4,000,000,000 ms",
                ("L1",),
            )
        )
    if not -50_000 <= location.altitude_centimeters <= 2_000_000_000:
        issues.append(
            ValidationIssue(
                "platform_location.altitude_range",
                "L4 must be between -50,000 and 2,000,000,000 cm",
                ("L4",),
            )
        )
    if location.speed_millimeters_per_second > 8_000_000:
        issues.append(
            ValidationIssue(
                "platform_location.speed_range",
                "L6 must not exceed 8,000,000 mm/s",
                ("L6",),
            )
        )
    return tuple(issues)


def validate_processing_history(
    history: ProcessingHistorySegment,
) -> tuple[ValidationIssue, ...]:
    """Report mechanically decidable Edition A Version 1 C1-C6 issues."""

    issues: list[ValidationIssue] = []
    if history.based_on_job_id == 0:
        issues.append(
            ValidationIssue(
                "processing_history.based_on_job_id_range",
                "C5 must be nonzero",
                ("C5",),
            )
        )
    for index, record in enumerate(history.records):
        record_number = index + 1
        if record.sequence_number != record_number:
            issues.append(
                ValidationIssue(
                    "processing_history.sequence",
                    "C6.1 must count records sequentially from one",
                    (f"C6.1[{index}]",),
                )
            )
        if record.modifying_job_id == 0:
            issues.append(
                ValidationIssue(
                    "processing_history.modifying_job_id_range",
                    "C6.5 must be nonzero",
                    (f"C6.5[{index}]",),
                )
            )
        if record.processing_performed & 0xC000:
            issues.append(
                ValidationIssue(
                    "processing_history.reserved_bits",
                    "C6.6 reserved bits 14 and 15 must be zero",
                    (f"C6.6[{index}]",),
                )
            )
    invalid = _invalid_bcs_fields(
        (
            ("C2", history.based_on_nationality),
            ("C3", history.based_on_platform_id),
            *tuple(
                field
                for index, record in enumerate(history.records)
                for field in (
                    (f"C6.2[{index}]", record.modifying_nationality),
                    (f"C6.3[{index}]", record.modifying_platform_id),
                )
            ),
        )
    )
    if invalid:
        issues.append(
            ValidationIssue(
                "processing_history.invalid_bcs",
                "Processing History character fields may contain only Annex A BCS bytes",
                invalid,
            )
        )
    return tuple(issues)


def validate_packet_context(
    packet: Packet,
    *,
    profile: PacketContextProfile = PacketContextProfile.EDITION_A_V1,
) -> tuple[ValidationIssue, ...]:
    """Report packet-level Job ID context under an explicit validation profile."""

    if not isinstance(profile, PacketContextProfile):
        raise TypeError("profile must be a PacketContextProfile value")
    has_radar_data = any(segment.segment_type in (2, 3) for segment in packet.segments)
    if has_radar_data and packet.header.job_id == 0:
        return (
            ValidationIssue(
                "packet.job_id_required",
                "P10 must be nonzero when the packet contains Dwell or HRR data",
                ("P10", "S1"),
            ),
        )
    legacy_version_30_job_definition = (
        profile is PacketContextProfile.LEGACY_VERSION_30_JOB_DEFINITION
        and packet.header.version_id == b"30"
        and len(packet.segments) == 1
        and packet.segments[0].segment_type == 5
        and len(packet.segments[0].payload) == 68
        and int.from_bytes(packet.segments[0].payload[:4], "big") == packet.header.job_id
    )
    if (
        not has_radar_data
        and packet.header.job_id != 0
        and not legacy_version_30_job_definition
    ):
        return (
            ValidationIssue(
                "packet.job_id_without_radar_data",
                "P10 must be zero when the packet contains no Dwell or HRR data",
                ("P10", "S1"),
            ),
        )
    return ()


def validate_job_definition(job: JobDefinitionSegment) -> tuple[ValidationIssue, ...]:
    """Report mechanically decidable Edition A Version 1 Job issues."""

    issues: list[ValidationIssue] = []
    if job.job_id == 0:
        issues.append(ValidationIssue("job.id_range", "J1 must be nonzero", ("J1",)))
    if job.target_filtering & 0xF8:
        issues.append(
            ValidationIssue(
                "job.target_filtering_reserved_bits",
                "J4 reserved bits 3 through 7 must be zero",
                ("J4",),
            )
        )
    if not (1 <= job.priority <= 99 or job.priority == 0xFF):
        issues.append(
            ValidationIssue(
                "job.priority_range",
                "J5 must be 1 through 99 or 255 for End of Job",
                ("J5",),
            )
        )
    position_uncertainty = (
        job.nominal_sensor_position_along_track_uncertainty_raw,
        job.nominal_sensor_position_cross_track_uncertainty_raw,
    )
    if any(value > 10_000 and value != 0xFFFF for value in position_uncertainty):
        issues.append(
            ValidationIssue(
                "job.sensor_position_uncertainty_range",
                "J16 and J17 must not exceed 10,000 dm unless No Statement",
                ("J16", "J17"),
            )
        )
    altitude_uncertainty = job.nominal_sensor_position_altitude_uncertainty_raw
    if altitude_uncertainty > 20_000 and altitude_uncertainty != 0xFFFF:
        issues.append(
            ValidationIssue(
                "job.sensor_altitude_uncertainty_range",
                "J18 must not exceed 20,000 dm unless No Statement",
                ("J18",),
            )
        )
    track_uncertainty = job.nominal_sensor_track_uncertainty_raw
    if track_uncertainty > 45 and track_uncertainty != 0xFF:
        issues.append(
            ValidationIssue(
                "job.sensor_track_uncertainty_range",
                "J19 must not exceed 45 degrees unless No Statement",
                ("J19",),
            )
        )
    radial_uncertainty = job.nominal_radial_velocity_standard_deviation_raw
    if radial_uncertainty > 5000 and radial_uncertainty != 0xFFFF:
        issues.append(
            ValidationIssue(
                "job.radial_velocity_uncertainty_range",
                "J23 must not exceed 5,000 cm/s unless No Statement",
                ("J23",),
            )
        )
    detection_probability = job.nominal_detection_probability_raw
    if detection_probability > 100 and detection_probability != 0xFF:
        issues.append(
            ValidationIssue(
                "job.detection_probability_range",
                "J25 must not exceed 100 percent unless No Statement",
                ("J25",),
            )
        )
    if invalid := _invalid_bcs_fields((("J3", job.sensor_model),)):
        issues.append(
            ValidationIssue(
                "job.invalid_bcs",
                "J3 may contain only the Annex A Basic Character Set",
                invalid,
            )
        )
    return tuple(issues)


def _presence_group_issue(
    dwell: DwellSegment,
    fields: tuple[int, ...],
    code: str,
    message: str,
) -> ValidationIssue | None:
    present = tuple(dwell.mask.has_dwell(field) for field in fields)
    if any(present) and not all(present):
        return ValidationIssue(code, message, tuple(f"D{field}" for field in fields))
    return None


def validate_dwell(dwell: DwellSegment) -> tuple[ValidationIssue, ...]:
    """Report Edition A Version 1 Dwell/Target conformance issues losslessly."""

    issues: list[ValidationIssue] = []

    if dwell.mask.spare_bits:
        issues.append(
            ValidationIssue(
                "dwell.existence_mask_spare_bits",
                "D1 spare bits must be zero",
                ("D1",),
            )
        )

    groups = (
        (
            (10, 11),
            "dwell.coordinate_scale_pair",
            "D10 and D11 must be sent together",
        ),
        (
            (12, 13, 14),
            "dwell.sensor_position_uncertainty_group",
            "D12, D13, and D14 must be sent together",
        ),
        (
            (15, 16, 17),
            "dwell.sensor_velocity_group",
            "D15, D16, and D17 must be sent together",
        ),
        (
            (18, 19, 20),
            "dwell.sensor_velocity_uncertainty_group",
            "D18, D19, and D20 must be sent together",
        ),
        (
            (21, 22, 23),
            "dwell.platform_orientation_group",
            "D21, D22, and D23 must be sent together",
        ),
    )
    for fields, code, message in groups:
        issue = _presence_group_issue(dwell, fields, code, message)
        if issue is not None:
            issues.append(issue)

    if dwell.dwell_time_milliseconds > 4_000_000_000:
        issues.append(
            ValidationIssue("dwell.time_range", "D6 must not exceed 4,000,000,000 ms", ("D6",))
        )
    if not -50_000 <= dwell.sensor_altitude_centimeters <= 2_000_000_000:
        issues.append(
            ValidationIssue(
                "dwell.sensor_altitude_range",
                "D9 must be between -50,000 and 2,000,000,000 cm",
                ("D9",),
            )
        )
    position_uncertainty = (
        dwell.sensor_position_along_track_uncertainty_centimeters,
        dwell.sensor_position_cross_track_uncertainty_centimeters,
    )
    if any(value is not None and value > 1_000_000 for value in position_uncertainty):
        issues.append(
            ValidationIssue(
                "dwell.sensor_position_uncertainty_range",
                "D12 and D13 must not exceed 1,000,000 cm",
                ("D12", "D13"),
            )
        )
    speed = dwell.sensor_speed_millimeters_per_second
    if speed is not None and speed > 8_000_000:
        issues.append(
            ValidationIssue(
                "dwell.sensor_speed_range",
                "D16 must not exceed 8,000,000 mm/s",
                ("D16",),
            )
        )
    track_uncertainty = dwell.sensor_track_uncertainty_degrees
    if track_uncertainty is not None and track_uncertainty > 45:
        issues.append(
            ValidationIssue(
                "dwell.sensor_track_uncertainty_range",
                "D18 must not exceed 45 degrees",
                ("D18",),
            )
        )
    platform_attitude = (dwell.platform_pitch, dwell.platform_roll)
    if any(angle is not None and not -16384 <= angle.raw <= 16383 for angle in platform_attitude):
        issues.append(
            ValidationIssue(
                "dwell.platform_attitude_range",
                "D22 and D23 must be between -90 and just under 90 degrees",
                ("D22", "D23"),
            )
        )
    sensor_attitude = (dwell.sensor_pitch, dwell.sensor_roll)
    if any(angle is not None and not -16384 <= angle.raw <= 16383 for angle in sensor_attitude):
        issues.append(
            ValidationIssue(
                "dwell.sensor_attitude_range",
                "D29 and D30 must be between -90 and just under 90 degrees",
                ("D29", "D30"),
            )
        )

    def has_target(field: int) -> bool:
        return bool(dwell.targets) and dwell.mask.has_target(field)

    high_resolution = (has_target(2), has_target(3))
    reduced = (has_target(4), has_target(5))
    scale = (dwell.mask.has_dwell(10), dwell.mask.has_dwell(11))
    if any(high_resolution) and not all(high_resolution):
        issues.append(
            ValidationIssue(
                "target.high_resolution_location_pair",
                "D32.2 and D32.3 must be sent together",
                ("D32.2", "D32.3"),
            )
        )
    if any(reduced) and not all(reduced):
        issues.append(
            ValidationIssue(
                "target.reduced_location_pair",
                "D32.4 and D32.5 must be sent together",
                ("D32.4", "D32.5"),
            )
        )
    if any(high_resolution) and any(reduced):
        issues.append(
            ValidationIssue(
                "target.location_encodings_exclusive",
                "high- and reduced-resolution target locations are mutually exclusive",
                ("D32.2", "D32.3", "D32.4", "D32.5"),
            )
        )
    if any(scale) != any(reduced):
        issues.append(
            ValidationIssue(
                "target.reduced_location_scale_factors",
                "D10/D11 are sent if and only if D32.4/D32.5 are sent",
                ("D10", "D11", "D32.4", "D32.5"),
            )
        )

    target_pairs = (
        (
            (7, 8),
            "target.velocity_wrap_pair",
            "D32.7 and D32.8 must be sent together",
        ),
        (
            (16, 17),
            "target.truth_tag_pair",
            "D32.16 and D32.17 must be sent together",
        ),
    )
    for fields, code, message in target_pairs:
        present = tuple(has_target(field) for field in fields)
        if any(present) and not all(present):
            issues.append(
                ValidationIssue(code, message, tuple(f"D32.{field}" for field in fields))
            )

    uncertainty_fields = tuple(has_target(field) for field in (12, 13, 14, 15))
    sensor_position_uncertainty = tuple(dwell.mask.has_dwell(field) for field in (12, 13, 14))
    if any(uncertainty_fields) and not all(sensor_position_uncertainty):
        issues.append(
            ValidationIssue(
                "target.uncertainty_sensor_position_required",
                "D32.12-D32.15 may be sent only when D12-D14 are sent",
                ("D12", "D13", "D14", "D32.12", "D32.13", "D32.14", "D32.15"),
            )
        )
    if has_target(14) and not has_target(6):
        issues.append(
            ValidationIssue(
                "target.height_uncertainty_height_required",
                "D32.14 may be sent only when D32.6 is sent",
                ("D32.6", "D32.14"),
            )
        )
    if has_target(15) and not has_target(7):
        issues.append(
            ValidationIssue(
                "target.velocity_uncertainty_velocity_required",
                "D32.15 may be sent only when D32.7 is sent",
                ("D32.7", "D32.15"),
            )
        )

    for target_index, target in enumerate(dwell.targets):
        probability = target.classification_probability_percent
        if probability is not None and probability > 100:
            issues.append(
                ValidationIssue(
                    "target.classification_probability_range",
                    "D32.11 must be between 0 and 100 percent",
                    (f"D32.11[{target_index}]",),
                )
            )
        height = target.geodetic_height_meters
        if height is not None and height < -1000:
            issues.append(
                ValidationIssue(
                    "target.geodetic_height_range",
                    "D32.6 must not be below -1,000 m",
                    (f"D32.6[{target_index}]",),
                )
            )
        velocity_uncertainty = target.radial_velocity_uncertainty_centimeters_per_second
        if velocity_uncertainty is not None and velocity_uncertainty > 5000:
            issues.append(
                ValidationIssue(
                    "target.radial_velocity_uncertainty_range",
                    "D32.15 must not exceed 5,000 cm/s",
                    (f"D32.15[{target_index}]",),
                )
            )

    return tuple(issues)
