"""AEDP-4607 Ed A V1 sections 2.3, 3.1, Table 3-1, and Annex C-4.1."""

from __future__ import annotations

import pytest

from stanag4607 import DecodeError, PacketHeader, decode_packet_header

HEADER_BYTES = bytes.fromhex(
    "34 31"  # P1: Edition A Version 1 (\"41\")
    "00 00 00 fe"  # P2: 254 bytes
    "5a 5a"  # P3: ZZ
    "05"  # P4: UNCLASSIFIED
    "5a 5a"  # P5: ZZ
    "00 41"  # P6: preserve multiple security-code bits
    "81"  # P7: Exercise, Simulated Data
    "5a 5a 53 59 4e 30 30 30 30 31"  # P8: ZZSYN00001
    "00 00 10 92"  # P9: 4242
    "00 00 00 4d"  # P10: 77
)


def test_decode_packet_header_preserves_all_wire_values() -> None:
    header = decode_packet_header(HEADER_BYTES)

    assert header == PacketHeader(
        version_id=b"41",
        packet_size=254,
        nationality=b"ZZ",
        security_classification=5,
        classification_system=b"ZZ",
        security_codes=0x0041,
        exercise_indicator=129,
        platform_id=b"ZZSYN00001",
        mission_id=4242,
        job_id=77,
    )
    assert header.to_bytes() == HEADER_BYTES


@pytest.mark.parametrize("length", [0, 1, 6, 31, 33])
def test_decode_packet_header_requires_exactly_32_bytes(length: int) -> None:
    with pytest.raises(DecodeError, match="32 bytes"):
        decode_packet_header((HEADER_BYTES + b"x")[:length])


def test_decode_rejects_packet_size_smaller_than_header() -> None:
    malformed = HEADER_BYTES[:2] + (31).to_bytes(4, "big") + HEADER_BYTES[6:]

    with pytest.raises(DecodeError, match=r"packet[_ ]size"):
        decode_packet_header(malformed)


def test_reserved_enumeration_values_are_preserved_structurally() -> None:
    reserved = bytearray(HEADER_BYTES)
    reserved[8] = 255
    reserved[13] = 255

    header = decode_packet_header(reserved)

    assert header.security_classification == 255
    assert header.exercise_indicator == 255
    assert header.to_bytes() == reserved


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"version_id": b"4"}, "version_id"),
        ({"packet_size": 31}, "packet_size"),
        ({"nationality": b"CAN"}, "nationality"),
        ({"security_classification": 256}, "security_classification"),
        ({"classification_system": b""}, "classification_system"),
        ({"security_codes": 65536}, "security_codes"),
        ({"exercise_indicator": -1}, "exercise_indicator"),
        ({"platform_id": b"TOO-SHORT"}, "platform_id"),
        ({"mission_id": -1}, "mission_id"),
        ({"job_id": 2**32}, "job_id"),
    ],
)
def test_packet_header_rejects_values_that_do_not_fit_the_wire(
    changes: dict[str, object], message: str
) -> None:
    values: dict[str, object] = {
        "version_id": b"41",
        "packet_size": 32,
        "nationality": b"CA",
        "security_classification": 5,
        "classification_system": b"CA",
        "security_codes": 0,
        "exercise_indicator": 0,
        "platform_id": b"RADAR-01  ",
        "mission_id": 0,
        "job_id": 0,
    }
    values.update(changes)

    with pytest.raises(ValueError, match=message):
        PacketHeader(**values)  # type: ignore[arg-type]
