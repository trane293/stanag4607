"""End-to-end CLI workflows over a public synthetic Edition 4 fixture."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from test_tasking import REQUEST_PAYLOAD

import stanag4607.cli as cli
from stanag4607 import (
    PACKET_HEADER_SIZE,
    FreeTextSegment,
    HrrSegment,
    Packet,
    Segment,
    decode_hrr_segment,
    decode_job_request_segment,
    decode_packet,
)
from stanag4607 import TestStatusSegment as StatusSegment
from stanag4607.cli import main


def _fixture() -> Path:
    return Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"


def test_inspect_emits_one_json_record_per_segment(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = main(["inspect", str(_fixture())])

    records = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert result == 0
    assert [record["decoded_type"] for record in records] == [
        "MissionSegment",
        "JobDefinitionSegment",
        "DwellSegment",
    ]
    assert records[-1]["target_count"] == 3
    assert records[-1]["dwell_time_utc"] == "2026-04-29T08:30:00+00:00"


def test_validate_reports_valid_fixture(capsys: pytest.CaptureFixture[str]) -> None:
    result = main(["validate", str(_fixture())])

    report = json.loads(capsys.readouterr().out)
    assert result == 0
    assert report == {"valid": True, "issues": []}


def test_validate_returns_nonzero_for_packet_context_issue(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    packet = decode_packet(_fixture().read_bytes())
    packet = replace(packet, header=replace(packet.header, job_id=0))
    path = tmp_path / "invalid.gmti"
    path.write_bytes(packet.to_bytes())

    result = main(["validate", str(path)])

    report = json.loads(capsys.readouterr().out)
    assert result == 1
    assert report["valid"] is False
    assert report["issues"][0]["code"] == "packet.job_id_required"


def test_validate_reports_test_status_issues(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = decode_packet(_fixture().read_bytes())
    status = StatusSegment(1, 0, 0, 0, 0x01, 0).to_segment()
    packet = Packet(
        replace(
            source.header,
            packet_size=PACKET_HEADER_SIZE + len(status.to_bytes()),
            job_id=0,
        ),
        (status,),
    )
    path = tmp_path / "invalid-status.gmti"
    path.write_bytes(packet.to_bytes())

    result = main(["validate", str(path)])

    report = json.loads(capsys.readouterr().out)
    assert result == 1
    assert report["issues"][0]["code"] == "test_status.hardware_reserved_bits"


def test_validate_reports_free_text_issues(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = decode_packet(_fixture().read_bytes())
    message = FreeTextSegment(b"          ", b"OPS       ", b"x").to_segment()
    packet = Packet(
        replace(
            source.header,
            packet_size=PACKET_HEADER_SIZE + len(message.to_bytes()),
            job_id=0,
        ),
        (message,),
    )
    path = tmp_path / "invalid-text.gmti"
    path.write_bytes(packet.to_bytes())

    result = main(["validate", str(path)])

    report = json.loads(capsys.readouterr().out)
    assert result == 1
    assert report["issues"][0]["code"] == "free_text.blank_field"


def test_validate_reports_packet_character_issues(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    packet = decode_packet(_fixture().read_bytes())
    packet = replace(packet, header=replace(packet.header, version_id=b"4\x00"))
    path = tmp_path / "invalid-header.gmti"
    path.write_bytes(packet.to_bytes())

    result = main(["validate", str(path)])

    report = json.loads(capsys.readouterr().out)
    assert result == 1
    assert report["issues"][0]["code"] == "packet.invalid_bcs"


def test_validate_reports_hrr_issues(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fixture = (
        Path(__file__).with_name("fixtures")
        / "hrr_signature_parked_both_time_branches.gmti"
    )
    packet = decode_packet(fixture.read_bytes())
    segment_index = next(
        index for index, segment in enumerate(packet.segments) if segment.segment_type == 3
    )
    hrr = decode_hrr_segment(packet.segments[segment_index])
    fields = list(hrr.fields)
    fields[hrr.mask.present_hrr_fields.index(24)] = b"\x1e"
    invalid = HrrSegment(hrr.mask, tuple(fields), hrr.scatterer_data).to_segment()
    segments = list(packet.segments)
    segments[segment_index] = invalid
    packet = replace(packet, segments=tuple(segments))
    path = tmp_path / "invalid-hrr.gmti"
    path.write_bytes(packet.to_bytes())

    result = main(["validate", str(path)])

    report = json.loads(capsys.readouterr().out)
    assert result == 1
    assert report["issues"][0]["code"] == "hrr.processing_mask_reserved_bits"


def test_validate_bounds_retained_issues_but_counts_all_of_them(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = decode_packet(_fixture().read_bytes())
    message = FreeTextSegment(b"          ", b"OPS\x00      ", b"x").to_segment()
    packet = Packet(
        replace(
            source.header,
            packet_size=PACKET_HEADER_SIZE + len(message.to_bytes()),
            job_id=0,
        ),
        (message,),
    )
    path = tmp_path / "many-issues.gmti"
    path.write_bytes(packet.to_bytes())

    result = main(["validate", "--max-issues", "1", str(path)])

    report = json.loads(capsys.readouterr().out)
    assert result == 1
    assert len(report["issues"]) == 1
    assert report["issue_count"] == 2
    assert report["issues_truncated"] == 1


def test_geojson_exports_all_located_targets(capsys: pytest.CaptureFixture[str]) -> None:
    result = main(["geojson", str(_fixture())])

    collection = json.loads(capsys.readouterr().out)
    assert result == 0
    assert collection["type"] == "FeatureCollection"
    assert len(collection["features"]) == 3


def test_demo_command_forwards_safe_replay_options(monkeypatch: pytest.MonkeyPatch) -> None:
    call: dict[str, object] = {}

    def fake_serve_demo(path: str, *, host: str, port: int, interval: float) -> None:
        call.update(path=path, host=host, port=port, interval=interval)

    monkeypatch.setattr(cli, "serve_demo", fake_serve_demo, raising=False)

    result = main(
        [
            "demo",
            "--host",
            "127.0.0.1",
            "--port",
            "8769",
            "--interval",
            "0.1",
            str(_fixture()),
        ]
    )

    assert result == 0
    assert call == {
        "path": str(_fixture()),
        "host": "127.0.0.1",
        "port": 8769,
        "interval": 0.1,
    }


def test_demo_command_exits_cleanly_when_interrupted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def interrupt(*args: object, **kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "serve_demo", interrupt)

    assert main(["demo", str(_fixture())]) == 130


def test_validate_includes_job_request_diagnostics(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = decode_packet(_fixture().read_bytes())
    request = decode_job_request_segment(Segment(101, REQUEST_PAYLOAD))
    invalid = replace(request, request_type=2).to_segment()
    packet = Packet(
        replace(
            source.header,
            packet_size=PACKET_HEADER_SIZE + len(invalid.to_bytes()),
            job_id=0,
        ),
        (invalid,),
    )
    path = tmp_path / "invalid-request.gmti"
    path.write_bytes(packet.to_bytes())

    result = main(["validate", str(path)])

    report = json.loads(capsys.readouterr().out)
    assert result == 1
    assert [issue["code"] for issue in report["issues"]] == [
        "job_request.request_type"
    ]


def test_cli_reports_input_errors_without_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = main(["inspect", str(tmp_path / "missing.gmti")])

    assert result == 2
    assert "stanag4607:" in capsys.readouterr().err
