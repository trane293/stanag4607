"""AEDP-4607 Ed A V1 section 3.5.1, Figure 3-4, and Table 3-12."""

import pytest

from stanag4607 import HrrExistenceMask


def test_public_hrr_mask_maps_header_and_scatterer_fields() -> None:
    mask = HrrExistenceMask.from_bytes(bytes.fromhex("ea ff c7 82 00"))

    assert mask.present_hrr_fields == (
        2,
        3,
        4,
        6,
        8,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        23,
        24,
        25,
        26,
    )
    assert mask.present_scatterer_fields == (1,)
    assert mask.missing_mandatory_fields == ()
    assert mask.hrr_fields_size == 35
    assert mask.to_bytes() == bytes.fromhex("ea ff c7 82 00")


def test_missing_mandatory_fields_are_reported_in_wire_order() -> None:
    mask = HrrExistenceMask(0)

    assert mask.missing_mandatory_fields == (
        "H2",
        "H3",
        "H4",
        "H8",
        "H10",
        "H11",
        "H12",
        "H13",
        "H14",
        "H16",
        "H17",
        "H18",
        "H19",
        "H23",
        "H24",
        "H25",
        "H26",
        "H32.1",
    )


def test_spare_bits_are_preserved_but_not_reported_as_fields() -> None:
    mask = HrrExistenceMask(0x3F)

    assert mask.spare_bits == 0x3F
    assert mask.present_hrr_fields == ()
    assert mask.present_scatterer_fields == ()
    assert mask.to_bytes() == b"\x00\x00\x00\x00\x3f"


@pytest.mark.parametrize("field", [1, 32, 100])
def test_hrr_field_query_rejects_invalid_numbers(field: int) -> None:
    with pytest.raises(ValueError, match="H2 through H31"):
        HrrExistenceMask(0).has_hrr(field)


@pytest.mark.parametrize("field", [0, 5, 100])
def test_scatterer_field_query_rejects_invalid_numbers(field: int) -> None:
    with pytest.raises(ValueError, match=r"H32\.1 through H32\.4"):
        HrrExistenceMask(0).has_scatterer(field)


@pytest.mark.parametrize("encoded", [b"", b"x" * 4, b"x" * 6])
def test_mask_decode_requires_exactly_five_bytes(encoded: bytes) -> None:
    with pytest.raises(ValueError, match="5 bytes"):
        HrrExistenceMask.from_bytes(encoded)


@pytest.mark.parametrize("raw", [-1, 2**40])
def test_mask_constructor_enforces_unsigned_40_bit_range(raw: int) -> None:
    with pytest.raises(ValueError, match="40-bit"):
        HrrExistenceMask(raw)
