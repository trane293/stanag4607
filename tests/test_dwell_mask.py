"""AEDP-4607 Ed A V1 section 3.4.1, Figure 3-1, and Tables 3-9/3-10."""

import pytest

from stanag4607 import DwellExistenceMask


def test_official_ff3f_example_maps_to_documented_fields() -> None:
    mask = DwellExistenceMask.from_bytes(bytes.fromhex("ff 3f 00 00 00 00 00 00"))

    assert mask.present_dwell_fields == (2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14, 15, 16, 17)
    assert not mask.has_dwell(10)
    assert not mask.has_dwell(11)
    assert mask.to_bytes() == bytes.fromhex("ff 3f 00 00 00 00 00 00")


def test_sparse_fixture_mask_has_mandatory_and_high_resolution_target_fields() -> None:
    mask = DwellExistenceMask.from_bytes(bytes.fromhex("ff 00 03 c1 80 00 00 00"))

    assert mask.present_dwell_fields == (2, 3, 4, 5, 6, 7, 8, 9, 24, 25, 26, 27)
    assert mask.present_target_fields == (2, 3)
    assert mask.missing_mandatory_fields == ()
    assert mask.dwell_fields_size == 35
    assert mask.target_report_size == 8


def test_missing_mandatory_fields_are_reported_in_field_order() -> None:
    mask = DwellExistenceMask(0)

    assert mask.missing_mandatory_fields == (2, 3, 4, 5, 6, 7, 8, 9, 24, 25, 26, 27)


def test_spare_bits_are_preserved_but_not_reported_as_fields() -> None:
    mask = DwellExistenceMask(0xFFFF)

    assert mask.spare_bits == 0xFFFF
    assert mask.present_dwell_fields == ()
    assert mask.present_target_fields == ()
    assert mask.to_bytes() == b"\x00" * 6 + b"\xff\xff"


@pytest.mark.parametrize("field", [1, 32, 100])
def test_dwell_field_query_rejects_non_dwell_field_numbers(field: int) -> None:
    with pytest.raises(ValueError, match="D2 through D31"):
        DwellExistenceMask(0).has_dwell(field)


@pytest.mark.parametrize("field", [0, 19, 100])
def test_target_field_query_rejects_non_target_field_numbers(field: int) -> None:
    with pytest.raises(ValueError, match=r"D32\.1 through D32\.18"):
        DwellExistenceMask(0).has_target(field)


@pytest.mark.parametrize("encoded", [b"", b"x" * 7, b"x" * 9])
def test_mask_decode_requires_exactly_eight_bytes(encoded: bytes) -> None:
    with pytest.raises(ValueError, match="8 bytes"):
        DwellExistenceMask.from_bytes(encoded)


@pytest.mark.parametrize("raw", [-1, 2**64])
def test_mask_constructor_enforces_unsigned_64_bit_range(raw: int) -> None:
    with pytest.raises(ValueError, match="64-bit"):
        DwellExistenceMask(raw)
