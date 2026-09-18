"""AEDP-4607 Ed A V1 sections 3.5.1-3.5.32 HRR validation."""

from pathlib import Path

from stanag4607 import HrrExistenceMask, HrrSegment, decode_hrr_segment, decode_packet, validate_hrr


def _hrr() -> HrrSegment:
    fixture = Path(__file__).with_name("fixtures") / "hrr_signature_parked_both_time_branches.gmti"
    packet = decode_packet(fixture.read_bytes())
    segment = next(segment for segment in packet.segments if segment.segment_type == 3)
    return decode_hrr_segment(segment)


def _changed(
    hrr: HrrSegment,
    *,
    fields: dict[int, bytes] | None = None,
    add: dict[int, bytes] | None = None,
    remove: tuple[int, ...] = (),
    scatterer_bits: int | None = None,
    scatterer_data: bytes | None = None,
) -> HrrSegment:
    values = dict(zip(hrr.mask.present_hrr_fields, hrr.fields, strict=True))
    values.update(fields or {})
    raw = hrr.mask.raw
    for field in remove:
        raw &= ~(1 << (41 - field))
        values.pop(field)
    for field, encoded in (add or {}).items():
        raw |= 1 << (41 - field)
        values[field] = encoded
    if scatterer_bits is not None:
        raw = (raw & ~0x3C0) | scatterer_bits
    mask = HrrExistenceMask(raw)
    return HrrSegment(
        mask,
        tuple(values[field] for field in mask.present_hrr_fields),
        hrr.scatterer_data if scatterer_data is None else scatterer_data,
    )


def test_public_hrr_metadata_is_valid() -> None:
    assert validate_hrr(_hrr()) == ()


def test_count_report_and_frequency_presence_follow_data_type() -> None:
    hrr = _hrr()

    no_count = validate_hrr(_changed(hrr, remove=(6,)))
    report_on_full_rdm = validate_hrr(_changed(hrr, add={5: b"\x00\x01"}))
    no_frequency = validate_hrr(_changed(hrr, remove=(15,)))

    assert {issue.code for issue in no_count} == {"hrr.scatterer_count_required"}
    assert {issue.code for issue in report_on_full_rdm} == {"hrr.mti_report_index_context"}
    assert {issue.code for issue in no_frequency} == {"hrr.center_frequency_required"}


def test_sparse_and_origin_data_types_require_their_conditional_fields() -> None:
    hrr = _hrr()
    sparse = _changed(hrr, fields={23: b"\x03"})
    partial_rdm = _changed(hrr, fields={23: b"\x06"})

    sparse_codes = {issue.code for issue in validate_hrr(sparse)}
    partial_codes = {issue.code for issue in validate_hrr(partial_rdm)}

    assert sparse_codes == {
        "hrr.mean_clutter_power_required",
        "hrr.mti_report_index_context",
        "hrr.sparse_indices_required",
    }
    assert partial_codes == {"hrr.origin_required"}


def test_phase_mask_must_agree_with_phase_byte_width() -> None:
    hrr = _hrr()
    phase_width_without_field = _changed(hrr, fields={26: b"\x01"})
    field_without_phase_width = _changed(hrr, scatterer_bits=0x300)

    assert {issue.code for issue in validate_hrr(phase_width_without_field)} == {
        "hrr.phase_presence"
    }
    assert {issue.code for issue in validate_hrr(field_without_phase_width)} == {
        "hrr.phase_presence"
    }


def test_fixed_value_ranges_and_reserved_bits_are_reported_together() -> None:
    hrr = _changed(
        _hrr(),
        fields={
            4: b"\x02",
            11: bytes.fromhex("80 80"),
            12: bytes.fromhex("80 80"),
            13: bytes(4),
            14: bytes.fromhex("7f ff 00 01"),
            15: bytes.fromhex("80 00 00 01"),
            16: b"\x02",
            17: b"\x03",
            18: b"\x03",
            23: b"\x08",
            24: b"\x1e",
            25: b"\x00",
            26: b"\x03",
        },
    )

    assert {issue.code for issue in validate_hrr(hrr)} == {
        "hrr.center_frequency_range",
        "hrr.compression_type",
        "hrr.data_type",
        "hrr.doppler_bin_spacing_range",
        "hrr.doppler_resolution_range",
        "hrr.doppler_weighting_function",
        "hrr.last_dwell_flag",
        "hrr.magnitude_bytes",
        "hrr.phase_bytes",
        "hrr.processing_mask_reserved_bits",
        "hrr.range_bin_spacing_range",
        "hrr.range_resolution_range",
        "hrr.range_weighting_function",
    }


def test_mask_spare_bits_are_reported() -> None:
    hrr = _hrr()
    changed = HrrSegment(
        HrrExistenceMask(hrr.mask.raw | 0x3F),
        hrr.fields,
        hrr.scatterer_data,
    )

    assert {issue.code for issue in validate_hrr(changed)} == {"hrr.mask_spare_bits"}


def test_optional_decimal_ranges_are_checked_exactly() -> None:
    hrr = _changed(
        _hrr(),
        add={
            22: bytes(4),
            30: bytes.fromhex("80 80 00 00"),
            31: bytes.fromhex("32 80 00 00"),
        },
    )

    issues = validate_hrr(hrr)

    assert [(issue.code, issue.fields) for issue in issues] == [
        ("hrr.doppler_origin_range", ("H22",)),
        ("hrr.electrical_length_range", ("H30",)),
        ("hrr.electrical_length_range", ("H31",)),
    ]


def test_mean_clutter_power_is_rejected_outside_sparse_type() -> None:
    hrr = _changed(_hrr(), add={9: b"\x01"})

    assert {issue.code for issue in validate_hrr(hrr)} == {
        "hrr.mean_clutter_power_required"
    }


def test_uncompressed_scatterer_record_size_is_validated() -> None:
    # AEDP-4607 Ed A V1 sections 3.5.25-3.5.26 and Table 3-13.
    hrr = _changed(_hrr(), fields={25: b"\x02"}, scatterer_data=b"\x01\x02\x03")

    assert {issue.code for issue in validate_hrr(hrr)} == {
        "hrr.scatterer_record_size"
    }


def test_sparse_total_scatterer_count_must_match_h7() -> None:
    # Section 3.5.7 defines H7 as total scatterer records for sparse H23=3.
    hrr = _changed(
        _hrr(),
        fields={23: b"\x03"},
        add={5: b"\x00\x01", 7: b"\x00\x02", 9: b"\x10"},
        scatterer_bits=0x2C0,
        scatterer_data=b"\x20\x00\x01\x00\x02",
    )

    assert {issue.code for issue in validate_hrr(hrr)} == {
        "hrr.sparse_scatterer_count"
    }
