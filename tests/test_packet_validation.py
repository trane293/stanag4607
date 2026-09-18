"""AEDP-4607 Ed A V1 sections 3.1.10 and 3.4 packet context."""

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from stanag4607 import (
    PACKET_HEADER_SIZE,
    Packet,
    PacketContextProfile,
    PacketStreamDecoder,
    decode_dwell_segment,
    decode_packet,
    validate_packet_context,
)


def _fixture_packet() -> Packet:
    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    return decode_packet(fixture.read_bytes())


def test_public_packet_has_valid_nonzero_dwell_job_context() -> None:
    assert validate_packet_context(_fixture_packet()) == ()


def test_dwell_or_hrr_requires_nonzero_packet_job_id() -> None:
    packet = _fixture_packet()
    invalid = replace(packet, header=replace(packet.header, job_id=0))

    issues = validate_packet_context(invalid)

    assert {issue.code for issue in issues} == {"packet.job_id_required"}
    assert issues[0].fields == ("P10", "S1")


def test_packet_without_dwell_or_hrr_requires_zero_job_id() -> None:
    packet = _fixture_packet()
    segments = tuple(segment for segment in packet.segments if segment.segment_type not in (2, 3))
    packet_size = PACKET_HEADER_SIZE + sum(len(segment.to_bytes()) for segment in segments)
    invalid = Packet(replace(packet.header, packet_size=packet_size), segments)

    issues = validate_packet_context(invalid)

    assert {issue.code for issue in issues} == {"packet.job_id_without_radar_data"}


def test_legacy_profile_accepts_only_version_30_job_definition_packet_job_id() -> None:
    """Wireshark issue 19566 producer profile; not an Edition A conformance rule."""

    packet = _fixture_packet()
    job_only = (packet.segments[1],)
    packet_size = PACKET_HEADER_SIZE + sum(len(segment.to_bytes()) for segment in job_only)
    legacy = Packet(
        replace(packet.header, version_id=b"30", packet_size=packet_size),
        job_only,
    )

    assert {issue.code for issue in validate_packet_context(legacy)} == {
        "packet.job_id_without_radar_data"
    }
    assert (
        validate_packet_context(
            legacy, profile=PacketContextProfile.LEGACY_VERSION_30_JOB_DEFINITION
        )
        == ()
    )


@pytest.mark.parametrize(
    ("version_id", "segments"),
    [
        (b"41", (1,)),
        (b"30", (0,)),
        (b"30", (0, 1)),
    ],
)
def test_legacy_profile_does_not_weaken_other_packet_context_rules(
    version_id: bytes, segments: tuple[int, ...]
) -> None:
    packet = _fixture_packet()
    selected = tuple(packet.segments[index] for index in segments)
    packet_size = PACKET_HEADER_SIZE + sum(len(segment.to_bytes()) for segment in selected)
    candidate = Packet(
        replace(packet.header, version_id=version_id, packet_size=packet_size),
        selected,
    )

    issues = validate_packet_context(
        candidate, profile=PacketContextProfile.LEGACY_VERSION_30_JOB_DEFINITION
    )

    assert {issue.code for issue in issues} == {"packet.job_id_without_radar_data"}


def test_legacy_profile_requires_job_definition_identity_to_match_p10() -> None:
    packet = _fixture_packet()
    job_only = (packet.segments[1],)
    packet_size = PACKET_HEADER_SIZE + sum(len(segment.to_bytes()) for segment in job_only)
    mismatched = Packet(
        replace(
            packet.header,
            version_id=b"30",
            packet_size=packet_size,
            job_id=packet.header.job_id + 1,
        ),
        job_only,
    )

    issues = validate_packet_context(
        mismatched, profile=PacketContextProfile.LEGACY_VERSION_30_JOB_DEFINITION
    )

    assert {issue.code for issue in issues} == {"packet.job_id_without_radar_data"}


def test_packet_context_profile_must_be_an_explicit_enum_value() -> None:
    with pytest.raises(TypeError, match="PacketContextProfile"):
        validate_packet_context(_fixture_packet(), profile="edition_a_v1")  # type: ignore[arg-type]


def test_local_wireshark_19566_capture_has_explicit_legacy_context_profile() -> None:
    """Non-normative SHA-256-pinned real-stream regression when locally available."""

    sample = Path("samples/private/wireshark/gmti.s4607")
    if not sample.exists():
        pytest.skip("local-only Wireshark issue 19566 capture is unavailable")
    decoder = PacketStreamDecoder()
    packets = []
    wire = sample.read_bytes()
    assert hashlib.sha256(wire).hexdigest() == (
        "4dbab5b46cfeb9debbcc4fed5eb1fbc487b6ec803d4625f018819b9b42249812"
    )
    for offset in range(0, len(wire), 17):
        packets.extend(decoder.feed(wire[offset : offset + 17]))
    decoder.finish()

    strict = [issue for packet in packets for issue in validate_packet_context(packet)]
    compatible = [
        issue
        for packet in packets
        for issue in validate_packet_context(
            packet, profile=PacketContextProfile.LEGACY_VERSION_30_JOB_DEFINITION
        )
    ]

    assert len(packets) == 26
    assert sum(
        decode_dwell_segment(segment).target_report_count
        for packet in packets
        for segment in packet.segments
        if segment.segment_type == 2
    ) == 193
    assert len(strict) == 6
    assert compatible == []
