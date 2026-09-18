"""Dependency-free GeoJSON projection of decoded Dwell targets."""

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from stanag4607 import (
    BinaryAngle,
    DwellSegment,
    TargetReport,
    decode_dwell_segment,
    decode_packet,
)
from stanag4607.geojson import dwell_to_geojson


def _fixture_dwell() -> DwellSegment:
    fixture = Path(__file__).with_name("fixtures") / "mission_dwell_hi_res_targets.gmti"
    packet = decode_packet(fixture.read_bytes())
    return decode_dwell_segment(next(item for item in packet.segments if item.segment_type == 2))


def test_public_fixture_exports_target_features_with_useful_provenance() -> None:
    dwell = _fixture_dwell()
    timestamp = datetime(2026, 4, 29, 8, 30, tzinfo=timezone.utc)

    collection = dwell_to_geojson(dwell, dwell_time_utc=timestamp)

    assert collection["type"] == "FeatureCollection"
    features = collection["features"]
    assert isinstance(features, list)
    assert len(features) == 3
    first = features[0]
    assert first["geometry"]["type"] == "Point"
    assert first["geometry"]["coordinates"] == pytest.approx(
        [24.499999964609742, 57.09999999962747]
    )
    assert first["properties"] == {
        "target_index": 0,
        "report_index": 0,
        "classification": 130,
        "radial_velocity_centimeters_per_second": -450,
        "dwell_time_milliseconds": 30_600_000,
        "dwell_time_utc": "2026-04-29T08:30:00+00:00",
        "location_encoding": "high_resolution",
        "latitude_raw": dwell.targets[0].high_resolution_latitude.raw,
        "longitude_raw": dwell.targets[0].high_resolution_longitude.raw,
    }


def test_geojson_normalizes_longitude_to_minus_180_through_180() -> None:
    dwell = _fixture_dwell()
    target = dwell.targets[0]
    longitude = BinaryAngle((350 * 2**32) // 360, 32)
    changed = TargetReport(
        target.mask,
        (*target.fields[:2], longitude.to_bytes(), *target.fields[3:]),
    )
    dwell = replace(dwell, targets=(changed, *dwell.targets[1:]))

    collection = dwell_to_geojson(dwell)

    features = collection["features"]
    assert isinstance(features, list)
    assert features[0]["geometry"]["coordinates"][0] == pytest.approx(-10.0)


def test_geojson_omits_targets_without_complete_positions() -> None:
    dwell = _fixture_dwell()
    mask = replace(dwell.mask, raw=dwell.mask.raw & ~(1 << 32) & ~(1 << 31))
    targets = tuple(
        TargetReport(mask, (target.fields[0], *target.fields[3:]))
        for target in dwell.targets
    )

    collection = dwell_to_geojson(replace(dwell, mask=mask, targets=targets))

    assert collection["features"] == []


def test_geojson_rejects_naive_utc_argument() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        dwell_to_geojson(_fixture_dwell(), dwell_time_utc=datetime(2026, 4, 29))
