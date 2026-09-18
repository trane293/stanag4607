"""AEDP-4607 Ed A V1 section 3.14 and Tables 3-21 through 3-23."""

from dataclasses import replace

import pytest

from stanag4607 import (
    DecodeError,
    ProcessingHistorySegment,
    ProcessingRecord,
    Segment,
    decode_processing_history_segment,
    decode_typed_segment,
)

PROCESSING_PAYLOAD = bytes.fromhex(
    "02 43 41 52 41 44 41 52 2d 30 31 20 20 00 00 00 2a 00 00 00 4d"
    "01 55 53 41 49 2d 4e 4f 44 45 20 20 20 00 00 00 64 00 00 00 65 00 82"
    "02 47 42 41 49 2d 4e 4f 44 45 20 20 20 00 00 00 66 00 00 00 67 02 01"
)


def test_processing_history_decodes_records_and_round_trips_exactly() -> None:
    history = decode_processing_history_segment(Segment(12, PROCESSING_PAYLOAD))

    assert history.processing_history_count == 2
    assert history.based_on_nationality == b"CA"
    assert history.based_on_platform_id == b"RADAR-01  "
    assert history.based_on_mission_id == 42
    assert history.based_on_job_id == 77
    assert history.records == (
        ProcessingRecord(1, b"US", b"AI-NODE   ", 100, 101, 0x0082),
        ProcessingRecord(2, b"GB", b"AI-NODE   ", 102, 103, 0x0201),
    )
    assert history.to_segment() == Segment(12, PROCESSING_PAYLOAD)
    assert isinstance(
        decode_typed_segment(Segment(12, PROCESSING_PAYLOAD)),
        ProcessingHistorySegment,
    )


@pytest.mark.parametrize("length", [0, 1, 20, 21, len(PROCESSING_PAYLOAD) - 1])
def test_processing_history_rejects_truncation_or_zero_records(length: int) -> None:
    with pytest.raises(DecodeError, match=r"processing history|Processing History"):
        decode_processing_history_segment(Segment(12, PROCESSING_PAYLOAD[:length]))


def test_processing_history_rejects_trailing_bytes_and_wrong_type() -> None:
    with pytest.raises(DecodeError, match="payload size"):
        decode_processing_history_segment(Segment(12, PROCESSING_PAYLOAD + b"x"))
    with pytest.raises(DecodeError, match="type 12"):
        decode_processing_history_segment(Segment(2, PROCESSING_PAYLOAD))


def test_processing_history_rejects_zero_declared_records() -> None:
    with pytest.raises(DecodeError, match="count"):
        decode_processing_history_segment(Segment(12, b"\x00" + PROCESSING_PAYLOAD[1:21]))


def test_processing_models_reject_values_that_do_not_fit_wire() -> None:
    history = decode_processing_history_segment(Segment(12, PROCESSING_PAYLOAD))

    with pytest.raises(ValueError, match="based_on_nationality"):
        replace(history, based_on_nationality=b"CAN")
    with pytest.raises(ValueError, match="records"):
        replace(history, records=())
    with pytest.raises(ValueError, match="ProcessingRecord"):
        replace(history, records=(object(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="sequence_number"):
        replace(history.records[0], sequence_number=256)
    with pytest.raises(ValueError, match="modifying_platform_id"):
        replace(history.records[0], modifying_platform_id=b"short")
