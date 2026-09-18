"""AEDP-4607 Ed A V1 sections 2.1, 2.2, 3.1.2, 3.2, and Table 3-6."""

from __future__ import annotations

from pathlib import Path

import pytest

from stanag4607 import (
    DecodeError,
    DecodeLimits,
    Packet,
    PacketHeader,
    Segment,
    SegmentHeader,
    decode_packet,
    decode_segment_header,
)


def packet_header(packet_size: int) -> PacketHeader:
    return PacketHeader(
        version_id=b"41",
        packet_size=packet_size,
        nationality=b"CA",
        security_classification=5,
        classification_system=b"CA",
        security_codes=0,
        exercise_indicator=1,
        platform_id=b"RADAR-01  ",
        mission_id=42,
        job_id=7,
    )


def test_segment_header_uses_five_byte_big_endian_layout() -> None:
    header = decode_segment_header(bytes.fromhex("80 00 00 01 02"))

    assert header == SegmentHeader(segment_type=128, segment_size=258)
    assert header.to_bytes() == bytes.fromhex("80 00 00 01 02")


@pytest.mark.parametrize("length", [0, 1, 4, 6])
def test_segment_header_requires_exactly_five_bytes(length: int) -> None:
    with pytest.raises(DecodeError, match="5 bytes"):
        decode_segment_header(b"\x01\x00\x00\x00\x05x"[:length])


def test_complete_packet_round_trip_preserves_unknown_segments() -> None:
    encoded_segments = bytes.fromhex("c8 00 00 00 08") + b"abc"
    encoded_segments += bytes.fromhex("06 00 00 00 07") + b"hi"
    encoded = packet_header(47).to_bytes() + encoded_segments

    packet = decode_packet(encoded)

    assert packet == Packet(
        header=packet_header(47),
        segments=(
            Segment(segment_type=200, payload=b"abc"),
            Segment(segment_type=6, payload=b"hi"),
        ),
    )
    assert packet.to_bytes() == encoded


def test_independent_edition_four_fixture_frames_and_round_trips() -> None:
    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    encoded = fixture.read_bytes()

    packet = decode_packet(encoded)

    assert packet.header.version_id == b"41"
    assert packet.header.packet_size == 254
    assert [segment.segment_type for segment in packet.segments] == [1, 5, 2]
    assert packet.to_bytes() == encoded


@pytest.mark.parametrize("declared_size", [31, 46, 48])
def test_packet_rejects_declared_size_that_disagrees_with_input(declared_size: int) -> None:
    valid_header = packet_header(47).to_bytes()
    encoded = valid_header[:2] + declared_size.to_bytes(4, "big") + valid_header[6:] + b"x" * 15

    with pytest.raises(DecodeError, match=r"packet[_ ]size"):
        decode_packet(encoded)


def test_packet_rejects_segment_smaller_than_its_header() -> None:
    encoded = packet_header(37).to_bytes() + bytes.fromhex("01 00 00 00 04")

    with pytest.raises(DecodeError, match=r"segment[_ ]size"):
        decode_packet(encoded)


def test_packet_rejects_segment_that_extends_beyond_packet() -> None:
    encoded = packet_header(40).to_bytes() + bytes.fromhex("01 00 00 00 09") + b"abc"

    with pytest.raises(DecodeError, match="segment size"):
        decode_packet(encoded)


def test_packet_rejects_trailing_bytes_too_short_for_segment_header() -> None:
    encoded = packet_header(34).to_bytes() + b"xx"

    with pytest.raises(DecodeError, match="truncated segment header"):
        decode_packet(encoded)


def test_packet_size_limit_is_enforced_before_segment_parsing() -> None:
    encoded = packet_header(37).to_bytes() + bytes.fromhex("01 00 00 00 05")

    with pytest.raises(DecodeError, match="maximum packet size"):
        decode_packet(encoded, limits=DecodeLimits(max_packet_size=36))


def test_input_size_limit_is_enforced_before_materializing_a_memoryview() -> None:
    encoded = memoryview(bytearray(64))

    with pytest.raises(DecodeError, match="input size 64 exceeds maximum packet size 32"):
        decode_packet(encoded, limits=DecodeLimits(max_packet_size=32))


def test_segment_count_limit_is_enforced() -> None:
    encoded = packet_header(42).to_bytes() + bytes.fromhex(
        "01 00 00 00 05 06 00 00 00 05"
    )

    with pytest.raises(DecodeError, match="segment count"):
        decode_packet(encoded, limits=DecodeLimits(max_segments=1))


@pytest.mark.parametrize(
    "limits",
    [
        {"max_packet_size": 31},
        {"max_packet_size": 2**32},
        {"max_segments": -1},
    ],
)
def test_decode_limits_reject_invalid_bounds(limits: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        DecodeLimits(**limits)


@pytest.mark.parametrize(
    "segment",
    [
        {"segment_type": -1, "payload": b""},
        {"segment_type": 256, "payload": b""},
        {"segment_type": 1, "payload": bytearray()},
    ],
)
def test_segment_rejects_values_that_do_not_fit_wire(segment: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        Segment(**segment)  # type: ignore[arg-type]


def test_packet_rejects_input_shorter_than_packet_header() -> None:
    with pytest.raises(DecodeError, match="shorter"):
        decode_packet(b"41")


def test_packet_encoder_rejects_header_size_disagreement() -> None:
    packet = Packet(header=packet_header(32), segments=(Segment(6, b"hi"),))

    with pytest.raises(ValueError, match="packet_size"):
        packet.to_bytes()
