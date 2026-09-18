"""Command-line inspection, validation, GeoJSON export, and local demo."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import BinaryIO, NoReturn

from .context import ContextualSegmentEvent, ContextualStreamDecoder
from .continuity import StreamContinuityValidator
from .demo import serve_demo
from .dwell import DwellSegment
from .errors import DecodeError
from .events import iter_packet_events
from .free_text import FreeTextSegment
from .geojson import dwell_to_geojson
from .hrr import HrrSegment
from .job_definition import JobDefinitionSegment
from .mission import MissionSegment
from .platform_location import PlatformLocationSegment
from .processing_history import ProcessingHistorySegment
from .stream import PacketStreamDecoder
from .tasking import JobAcknowledgeSegment, JobRequestSegment
from .test_status import TestStatusSegment
from .validation import (
    ValidationIssue,
    validate_dwell,
    validate_free_text,
    validate_hrr,
    validate_job_acknowledge,
    validate_job_definition,
    validate_job_request,
    validate_mission,
    validate_packet_context,
    validate_packet_header,
    validate_platform_location,
    validate_processing_history,
    validate_test_status,
)

_CHUNK_SIZE = 64 * 1024
_DEFAULT_MAX_VALIDATION_ISSUES = 10_000


def _stream_chunks(stream: BinaryIO) -> Iterator[bytes]:
    while chunk := stream.read(_CHUNK_SIZE):
        yield chunk


def _chunks(path: str) -> Iterator[bytes]:
    if path == "-":
        yield from _stream_chunks(sys.stdin.buffer)
        return
    with Path(path).open("rb") as stream:
        yield from _stream_chunks(stream)


def _context_events(path: str) -> Iterator[ContextualSegmentEvent]:
    decoder = ContextualStreamDecoder()
    for chunk in _chunks(path):
        yield from decoder.feed(chunk)
    decoder.finish()


def _inspect(path: str) -> int:
    for contextual in _context_events(path):
        event = contextual.event
        record: dict[str, object] = {
            "packet_index": contextual.packet_index,
            "segment_index": event.segment_index,
            "segment_type": event.segment.segment_type,
            "decoded_type": type(event.value).__name__,
            "platform_id": event.packet_header.platform_id.decode("ascii", errors="replace"),
            "mission_id": event.packet_header.mission_id,
            "job_id": event.packet_header.job_id,
        }
        if isinstance(event.value, DwellSegment):
            record["target_count"] = event.value.target_report_count
            record["dwell_time_utc"] = (
                None
                if contextual.dwell_time_utc is None
                else contextual.dwell_time_utc.isoformat()
            )
        print(json.dumps(record, sort_keys=True))
    return 0


def _validate(path: str, *, max_issues: int) -> int:
    decoder = PacketStreamDecoder()
    continuity = StreamContinuityValidator()
    issues: list[dict[str, object]] = []
    issue_count = 0

    def collect(new_issues: Iterable[ValidationIssue]) -> None:
        nonlocal issue_count
        for issue in new_issues:
            issue_count += 1
            if len(issues) < max_issues:
                issues.append(asdict(issue))

    for chunk in _chunks(path):
        for packet in decoder.feed(chunk):
            collect(validate_packet_header(packet.header))
            collect(validate_packet_context(packet))
            for event in iter_packet_events(packet):
                value = event.value
                collect(continuity.observe(event))
                if isinstance(value, MissionSegment):
                    collect(validate_mission(value))
                elif isinstance(value, DwellSegment):
                    collect(validate_dwell(value))
                elif isinstance(value, FreeTextSegment):
                    collect(validate_free_text(value))
                elif isinstance(value, HrrSegment):
                    collect(validate_hrr(value))
                elif isinstance(value, JobDefinitionSegment):
                    collect(validate_job_definition(value))
                elif isinstance(value, PlatformLocationSegment):
                    collect(validate_platform_location(value))
                elif isinstance(value, ProcessingHistorySegment):
                    collect(validate_processing_history(value))
                elif isinstance(value, TestStatusSegment):
                    collect(validate_test_status(value))
                elif isinstance(value, JobRequestSegment):
                    collect(validate_job_request(value))
                elif isinstance(value, JobAcknowledgeSegment):
                    collect(validate_job_acknowledge(value))
    decoder.finish()
    report: dict[str, object] = {"valid": issue_count == 0, "issues": issues}
    truncated = issue_count - len(issues)
    if truncated:
        report["issue_count"] = issue_count
        report["issues_truncated"] = truncated
    print(json.dumps(report, sort_keys=True))
    return 0 if issue_count == 0 else 1


def _geojson(path: str) -> int:
    sys.stdout.write('{"type":"FeatureCollection","features":[')
    first = True
    for contextual in _context_events(path):
        value = contextual.event.value
        if not isinstance(value, DwellSegment):
            continue
        collection = dwell_to_geojson(value, dwell_time_utc=contextual.dwell_time_utc)
        features = collection["features"]
        if not isinstance(features, list):
            raise RuntimeError("internal GeoJSON feature collection is invalid")
        for feature in features:
            if not first:
                sys.stdout.write(",")
            sys.stdout.write(json.dumps(feature, separators=(",", ":"), sort_keys=True))
            first = False
    sys.stdout.write("]}\n")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stanag4607")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("inspect", "geojson"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("input", help="STANAG 4607 file, or - for standard input")
    validate = subparsers.add_parser("validate")
    validate.add_argument(
        "--max-issues",
        type=_nonnegative_int,
        default=_DEFAULT_MAX_VALIDATION_ISSUES,
        help="maximum issues retained in the JSON report (default: %(default)s)",
    )
    validate.add_argument("input", help="STANAG 4607 file, or - for standard input")
    demo = subparsers.add_parser("demo", help="replay a stream in a local validation UI")
    demo.add_argument("input", help="STANAG 4607 file")
    demo.add_argument("--host", default="127.0.0.1", help="listen address")
    demo.add_argument("--port", type=_port, default=8768, help="listen port")
    demo.add_argument(
        "--interval",
        type=_nonnegative_float,
        default=0.5,
        help="seconds between segment events",
    )
    return parser


def _nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def _nonnegative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def _port(value: str) -> int:
    parsed = int(value)
    if not 0 <= parsed <= 65_535:
        raise argparse.ArgumentTypeError("must be between 0 and 65535")
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return its process status."""

    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "validate":
            return _validate(arguments.input, max_issues=arguments.max_issues)
        if arguments.command == "demo":
            serve_demo(
                arguments.input,
                host=arguments.host,
                port=arguments.port,
                interval=arguments.interval,
            )
            return 0
        commands = {"inspect": _inspect, "geojson": _geojson}
        return commands[arguments.command](arguments.input)
    except KeyboardInterrupt:
        return 130
    except (DecodeError, OSError, ValueError) as error:
        print(f"stanag4607: {error}", file=sys.stderr)
        return 2


def entrypoint() -> NoReturn:
    """Installed console-script entry point."""

    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
