"""Application-level tests for the dependency-free live demo adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from stanag4607.demo import demo_document, iter_demo_events

FIXTURES = Path(__file__).with_name("fixtures")


def test_demo_stream_reports_valid_targets_from_public_edition_4_sample() -> None:
    # Interoperability evidence: pinned public Edition 4 synthetic packet described
    # in references/data/manifest.json. This tests the demo adapter, not wire semantics.
    payload = (FIXTURES / "mission_dwell_hi_res_targets.gmti").read_bytes()

    events = list(iter_demo_events((payload[:17], payload[17:89], payload[89:])))

    assert [event["decoded_type"] for event in events] == [
        "MissionSegment",
        "JobDefinitionSegment",
        "DwellSegment",
    ]
    assert all(event["valid"] is True for event in events)
    assert events[-1]["target_count"] == 3
    assert len(events[-1]["targets"]) == 3
    assert events[-1]["targets"][0]["coordinates"] == pytest.approx([24.5, 57.1])


def test_demo_stream_surfaces_validation_findings() -> None:
    payload = (FIXTURES / "free_text_and_test_status.gmti").read_bytes()

    events = list(iter_demo_events((payload,)))

    assert events[0]["valid"] is False
    assert events[0]["issues"][0]["code"] == "packet.job_id_without_radar_data"
    assert events[1]["valid"] is True
    assert events[2]["valid"] is True


def test_demo_document_contains_live_validity_and_target_views() -> None:
    document = demo_document("sample.gmti")

    assert "EventSource('/events')" in document
    assert "Live validity" in document
    assert "Target positions" in document
    assert "sample.gmti" in document
    assert "https://" not in document
