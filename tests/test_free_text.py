"""AEDP-4607 Ed A V1 section 3.8, Table 3-19, and Annex A tests."""

import pytest

from stanag4607 import (
    DecodeError,
    FreeTextSegment,
    Segment,
    decode_free_text_segment,
    decode_typed_segment,
    validate_free_text,
)


def test_decode_preserves_exact_fields_and_round_trips() -> None:
    segment = Segment(6, b"SENSOR-1  " + b"OPS       " + b"TRACK 14\r\nNORTH")

    message = decode_free_text_segment(segment)

    assert message.originator_id == b"SENSOR-1  "
    assert message.recipient_id == b"OPS       "
    assert message.free_text == b"TRACK 14\r\nNORTH"
    assert message.to_segment() == segment
    assert decode_typed_segment(segment) == message


@pytest.mark.parametrize("size", [0, 20, 65_536])
def test_decode_rejects_payload_outside_declared_size(size: int) -> None:
    with pytest.raises(DecodeError, match="between 21 and 65535 bytes"):
        decode_free_text_segment(Segment(6, bytes(size)))


def test_decode_rejects_wrong_segment_type() -> None:
    with pytest.raises(DecodeError, match="requires type 6"):
        decode_free_text_segment(Segment(5, bytes(21)))


@pytest.mark.parametrize(
    ("args", "field"),
    [
        ((b"short", b"RECIPIENT ", b"x"), "originator_id"),
        ((b"ORIGINATOR", b"short", b"x"), "recipient_id"),
        ((b"ORIGINATOR", b"RECIPIENT ", b""), "free_text"),
    ],
)
def test_constructor_enforces_field_widths(args: tuple[bytes, bytes, bytes], field: str) -> None:
    with pytest.raises(ValueError, match=field):
        FreeTextSegment(*args)


def test_validation_reports_blank_and_non_bcs_fields_without_mutating_bytes() -> None:
    message = FreeTextSegment(b"          ", b"OPS\x00      ", b"\xff")

    issues = validate_free_text(message)

    assert {issue.code for issue in issues} == {
        "free_text.blank_field",
        "free_text.invalid_bcs",
    }
    assert message.to_segment().payload == b"          OPS\x00      \xff"
