"""Dependency-free GeoJSON adapters for STANAG 4607 observations."""

from __future__ import annotations

from datetime import datetime, timezone
from fractions import Fraction

from .dwell import DwellSegment


def _longitude_degrees(raw_degrees: Fraction) -> float:
    if raw_degrees > 180:
        raw_degrees -= 360
    return float(raw_degrees)


def dwell_to_geojson(
    dwell: DwellSegment, *, dwell_time_utc: datetime | None = None
) -> dict[str, object]:
    """Project complete Dwell target positions into a GeoJSON FeatureCollection."""

    if dwell_time_utc is not None and dwell_time_utc.tzinfo is None:
        raise ValueError("dwell_time_utc must be timezone-aware")
    timestamp = (
        None
        if dwell_time_utc is None
        else dwell_time_utc.astimezone(timezone.utc).isoformat()
    )
    features: list[dict[str, object]] = []
    for target_index, target in enumerate(dwell.targets):
        location = dwell.target_location(target_index)
        if location is None:
            continue
        properties: dict[str, object] = {
            "target_index": target_index,
            "report_index": target.report_index,
            "classification": target.classification,
            "radial_velocity_centimeters_per_second": (
                target.radial_velocity_centimeters_per_second
            ),
            "dwell_time_milliseconds": dwell.dwell_time_milliseconds,
            "dwell_time_utc": timestamp,
            "location_encoding": location.encoding,
            "latitude_raw": location.latitude.raw,
            "longitude_raw": location.longitude.raw,
        }
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        _longitude_degrees(location.longitude.degrees),
                        float(location.latitude.degrees),
                    ],
                },
                "properties": properties,
            }
        )
    return {"type": "FeatureCollection", "features": features}
