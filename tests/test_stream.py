"""Packet streaming tests derived from AEDP-4607 Ed A V1 sections 2.1-2.2."""

from __future__ import annotations

import pytest

from stanag4607 import DecodeError, DecodeLimits, PacketHeader, PacketStreamDecoder, Segment


def encode_packet(payload: bytes, *, mission_id: int = 1) -> bytes:
    segment = Segment(200, payload)
    size = 32 + len(segment.to_bytes())
    header = PacketHeader(
        version_id=b"41",
        packet_size=size,
        nationality=b"CA",
        security_classification=5,
        classification_system=b"CA",
        security_codes=0,
        exercise_indicator=1,
        platform_id=b"RADAR-01  ",
        mission_id=mission_id,
        job_id=1,
    )
    return header.to_bytes() + segment.to_bytes()


@pytest.mark.parametrize("chunk_size", [1, 2, 5, 6, 31, 32, 37, 64, 4096])
def test_arbitrary_chunks_decode_consecutive_packets(chunk_size: int) -> None:
    first = encode_packet(b"first", mission_id=1)
    second = encode_packet(b"second", mission_id=2)
    stream = first + second
    decoder = PacketStreamDecoder()
    packets = []

    for offset in range(0, len(stream), chunk_size):
        packets.extend(decoder.feed(stream[offset : offset + chunk_size]))
    decoder.finish()

    assert [packet.header.mission_id for packet in packets] == [1, 2]
    assert [packet.to_bytes() for packet in packets] == [first, second]
    assert decoder.buffered_bytes == 0


def test_empty_chunks_are_no_op() -> None:
    decoder = PacketStreamDecoder()

    assert decoder.feed(b"") == ()
    decoder.finish()


def test_finish_rejects_truncated_header() -> None:
    decoder = PacketStreamDecoder()
    decoder.feed(b"41\x00")

    with pytest.raises(DecodeError, match="truncated packet header"):
        decoder.finish()


def test_finish_rejects_truncated_packet_body() -> None:
    encoded = encode_packet(b"payload")
    decoder = PacketStreamDecoder()
    decoder.feed(encoded[:-1])

    with pytest.raises(DecodeError, match="truncated packet"):
        decoder.finish()


def test_declared_oversize_fails_after_header_without_buffering_body() -> None:
    encoded = bytearray(encode_packet(b""))
    encoded[2:6] = (101).to_bytes(4, "big")
    decoder = PacketStreamDecoder(limits=DecodeLimits(max_packet_size=100))

    with pytest.raises(DecodeError, match="maximum packet size"):
        decoder.feed(encoded[:32])

    assert decoder.buffered_bytes == 32
    assert decoder.failed


def test_failure_requires_explicit_reset() -> None:
    encoded = bytearray(encode_packet(b""))
    encoded[2:6] = (31).to_bytes(4, "big")
    decoder = PacketStreamDecoder()

    with pytest.raises(DecodeError):
        decoder.feed(encoded[:32])
    with pytest.raises(RuntimeError, match="failed"):
        decoder.feed(b"")

    decoder.reset()
    assert decoder.feed(encode_packet(b"ok"))[0].segments[0].payload == b"ok"
    decoder.finish()


def test_finish_is_terminal_until_reset() -> None:
    decoder = PacketStreamDecoder()
    decoder.finish()

    with pytest.raises(RuntimeError, match="finished"):
        decoder.feed(b"")
    with pytest.raises(RuntimeError, match="finished"):
        decoder.finish()

    decoder.reset()
    assert len(decoder.feed(encode_packet(b"ok"))) == 1


def test_internal_buffer_never_exceeds_configured_packet_limit() -> None:
    maximum = 64
    encoded = bytearray(encode_packet(b""))
    encoded[2:6] = maximum.to_bytes(4, "big")
    decoder = PacketStreamDecoder(limits=DecodeLimits(max_packet_size=maximum))

    assert decoder.feed(encoded[:32] + b"x" * 31) == ()

    assert decoder.buffered_bytes == maximum - 1
    assert not decoder.failed
