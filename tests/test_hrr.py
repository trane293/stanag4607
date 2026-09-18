"""AEDP-4607 Ed A V1 section 3.5 and Table 3-12 fixed HRR fields."""

from fractions import Fraction
from pathlib import Path

import pytest

from stanag4607 import (
    DecodeError,
    HrrScattererRecord,
    HrrSegment,
    Segment,
    SignedBinaryDecimal,
    SignedHertzDecimal,
    decode_hrr_segment,
    decode_packet,
    decode_typed_segment,
)


def _public_hrr_segments() -> tuple[Segment, Segment]:
    fixture = Path(__file__).with_name("fixtures") / "hrr_signature_parked_both_time_branches.gmti"
    packet = decode_packet(fixture.read_bytes())
    values = tuple(segment for segment in packet.segments if segment.segment_type == 3)
    assert len(values) == 2
    return values


def test_public_hrr_fixed_fields_decode_and_round_trip() -> None:
    first, second = _public_hrr_segments()

    hrr = decode_hrr_segment(first)

    assert hrr.revisit_index == 3
    assert hrr.dwell_index == 11
    assert hrr.last_dwell == 1
    assert hrr.mti_report_index is None
    assert hrr.target_scatterer_count == 2
    assert hrr.range_sample_count is None
    assert hrr.doppler_sample_count == 4
    assert hrr.mean_clutter_power_decibels is None
    assert hrr.detection_threshold_decibels == Fraction(-10)
    assert hrr.range_resolution == SignedBinaryDecimal(0x0F00, 16)
    assert hrr.range_resolution_centimeters == 30
    assert hrr.range_bin_spacing_centimeters == 15
    assert hrr.doppler_resolution == SignedHertzDecimal(0x00788000)
    assert hrr.doppler_bin_spacing == SignedHertzDecimal(0x00044000)
    assert hrr.center_frequency == SignedBinaryDecimal(0x04C00000, 32)
    assert hrr.center_frequency_gigahertz == Fraction(19, 2)
    assert hrr.compression_type == 0
    assert hrr.range_weighting_function == 1
    assert hrr.doppler_weighting_function == 1
    assert hrr.maximum_pixel_power == SignedBinaryDecimal(0x1800, 16)
    assert hrr.maximum_pixel_power_decibels == 48
    assert hrr.maximum_rcs_decibels is None
    assert hrr.range_origin_meters is None
    assert hrr.doppler_origin is None
    assert hrr.data_type == 5
    assert hrr.processing_mask == 0x80
    assert hrr.magnitude_bytes == 1
    assert hrr.phase_bytes == 0
    assert hrr.range_extent_pixels is None
    assert hrr.range_to_nearest_edge_centimeters is None
    assert hrr.zero_velocity_bin_index is None
    assert hrr.target_radial_electrical_length is None
    assert hrr.electrical_length_uncertainty is None
    assert hrr.scatterer_data == b"\x10\x20\x30\x40"
    assert hrr.to_segment() == first
    assert decode_typed_segment(first) == hrr

    second_hrr = decode_hrr_segment(second)
    assert second_hrr.revisit_index == 9
    assert second_hrr.dwell_index == 99
    assert second_hrr.scatterer_data == b"\xaa\xbb"
    assert second_hrr.to_segment() == second


def test_optional_numeric_accessors_preserve_sign_and_units() -> None:
    first, _ = _public_hrr_segments()
    original = decode_hrr_segment(first)
    raw = original.mask.raw
    for field in (9, 20, 21, 22, 27, 28, 29, 30, 31):
        raw |= 1 << (41 - field)
    mask = original.mask.__class__(raw)
    encoded = {
        field: original.field_bytes(field)
        for field in original.mask.present_hrr_fields
    }
    encoded.update(
        {
            9: b"\x20",
            20: b"\xf2",
            21: (-123).to_bytes(2, "big", signed=True),
            22: bytes.fromhex("80 02 80 00"),
            27: b"\x09",
            28: (1234).to_bytes(4, "big"),
            29: b"\x07",
            30: bytes.fromhex("01 40 00 00"),
            31: bytes.fromhex("00 40 00 00"),
        }
    )
    hrr = HrrSegment(
        mask,
        tuple(encoded[field] for field in mask.present_hrr_fields),
        b"\x01",
    )

    assert hrr.mean_clutter_power_decibels == 8
    assert hrr.maximum_rcs_decibels == -7
    assert hrr.range_origin_meters == -123
    assert hrr.doppler_origin == SignedHertzDecimal(0x80028000)
    assert hrr.range_extent_pixels == 9
    assert hrr.range_to_nearest_edge_centimeters == 1234
    assert hrr.zero_velocity_bin_index == 7
    assert hrr.target_radial_electrical_length_meters == Fraction(5, 2)
    assert hrr.electrical_length_uncertainty_meters == Fraction(1, 2)
    assert decode_hrr_segment(hrr.to_segment()) == hrr


@pytest.mark.parametrize("size", [0, 4])
def test_decode_rejects_payload_shorter_than_mask(size: int) -> None:
    with pytest.raises(DecodeError, match="at least 5 bytes"):
        decode_hrr_segment(Segment(3, bytes(size)))


def test_decode_rejects_wrong_segment_type() -> None:
    with pytest.raises(DecodeError, match="requires type 3"):
        decode_hrr_segment(Segment(2, bytes(5)))


def test_decode_rejects_missing_mandatory_fields() -> None:
    with pytest.raises(DecodeError, match="mandatory HRR fields absent"):
        decode_hrr_segment(Segment(3, bytes(5)))


def test_decode_rejects_truncated_fixed_fields() -> None:
    first, _ = _public_hrr_segments()

    with pytest.raises(DecodeError, match="truncated H26"):
        decode_hrr_segment(Segment(3, first.payload[:39]))


def test_scatterer_bytes_are_bounded_before_copying() -> None:
    first, _ = _public_hrr_segments()

    with pytest.raises(DecodeError, match="scatterer data size 4 exceeds configured limit 3"):
        decode_hrr_segment(first, max_scatterer_bytes=3)


def test_scatterer_bound_must_not_be_negative() -> None:
    first, _ = _public_hrr_segments()

    with pytest.raises(ValueError, match="max_scatterer_bytes"):
        decode_hrr_segment(first, max_scatterer_bytes=-1)


def test_model_rejects_fields_that_disagree_with_mask() -> None:
    first, _ = _public_hrr_segments()
    hrr = decode_hrr_segment(first)

    with pytest.raises(ValueError, match="field count"):
        HrrSegment(hrr.mask, hrr.fields[:-1], hrr.scatterer_data)

    wrong_width = (*hrr.fields[:-1], b"xx")
    with pytest.raises(ValueError, match="H26 must be exactly 1 byte"):
        HrrSegment(hrr.mask, wrong_width, hrr.scatterer_data)


def test_model_rejects_non_bytes_scatterer_data() -> None:
    first, _ = _public_hrr_segments()
    hrr = decode_hrr_segment(first)

    with pytest.raises(ValueError, match="scatterer_data"):
        HrrSegment(hrr.mask, hrr.fields, bytearray())  # type: ignore[arg-type]


def test_field_lookup_distinguishes_absence_and_invalid_field_number() -> None:
    first, _ = _public_hrr_segments()
    hrr = decode_hrr_segment(first)

    assert hrr.field_bytes(5) is None
    with pytest.raises(ValueError, match="H2 through H31"):
        hrr.field_bytes(32)


def test_uncompressed_scatterer_records_decode_exact_values_and_round_trip() -> None:
    # AEDP-4607 Ed A V1 sections 3.5.25-3.5.26 and 3.5.32, Table 3-13.
    first, _ = _public_hrr_segments()
    original = decode_hrr_segment(first)
    mask = original.mask.__class__(original.mask.raw | (1 << (41 - 7)) | 0x3C0)
    encoded = {
        field: original.field_bytes(field)
        for field in original.mask.present_hrr_fields
    }
    encoded.update({7: b"\x00\x02", 23: b"\x03", 25: b"\x02", 26: b"\x01"})
    raw_records = bytes.fromhex(
        "01 23 40 00 02 01 02 "
        "ff ff c0 ff ff 00 00"
    )
    hrr = HrrSegment(
        mask,
        tuple(encoded[field] for field in mask.present_hrr_fields),
        raw_records,
    )

    assert hrr.scatterer_records == (
        HrrScattererRecord(b"\x01\x23", b"\x40", 2, 258),
        HrrScattererRecord(b"\xff\xff", b"\xc0", 65535, 0),
    )
    assert hrr.scatterer_records[0].magnitude_raw == 0x0123
    assert hrr.scatterer_records[0].magnitude_decibels_below_peak == Fraction(-0x0123, 4)
    assert hrr.scatterer_records[0].phase_turns == Fraction(1, 4)
    assert b"".join(record.to_bytes() for record in hrr.scatterer_records) == raw_records
    assert decode_hrr_segment(hrr.to_segment()).scatterer_records == hrr.scatterer_records


def test_compressed_or_incomplete_scatterer_layout_remains_opaque() -> None:
    # H16=1 names threshold decomposition but the edition does not define a
    # sufficiently precise decompression algorithm for this implementation.
    first, _ = _public_hrr_segments()
    original = decode_hrr_segment(first)
    encoded = {
        field: original.field_bytes(field)
        for field in original.mask.present_hrr_fields
    }
    encoded[16] = b"\x01"
    compressed = HrrSegment(
        original.mask,
        tuple(encoded[field] for field in original.mask.present_hrr_fields),
        b"\x10\x20\x30",
    )
    incomplete_fields = {
        field: original.field_bytes(field)
        for field in original.mask.present_hrr_fields
    }
    incomplete_fields[25] = b"\x02"
    incomplete = HrrSegment(
        original.mask,
        tuple(incomplete_fields[field] for field in original.mask.present_hrr_fields),
        b"\x10\x20\x30",
    )

    assert compressed.scatterer_records is None
    assert compressed.to_segment().payload.endswith(b"\x10\x20\x30")
    assert incomplete.scatterer_records is None
