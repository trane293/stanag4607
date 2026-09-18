# Target geometry and GeoJSON

`DwellSegment.target_location(index)` returns a target position when its
selected fields provide enough information. It handles direct high-resolution
coordinates and the standard's reduced-coordinate representation while
retaining the exact binary-angle values.

To export a Dwell as GeoJSON, pass it to `dwell_to_geojson()` with an optional
resolved UTC observation time:

```python
from pathlib import Path

from stanag4607 import ContextualStreamDecoder, DwellSegment, dwell_to_geojson

decoder = ContextualStreamDecoder()
for item in decoder.feed(
    Path("tests/fixtures/mission_dwell_hi_res_targets.gmti").read_bytes()
):
    if isinstance(item.event.value, DwellSegment):
        collection = dwell_to_geojson(
            item.event.value, dwell_time_utc=item.dwell_time_utc
        )
        print(len(collection["features"]))
decoder.finish()
```

The sample prints `3`. GeoJSON coordinates use longitude, latitude order and
ordinary decimal numbers. Each feature also carries the raw binary-angle
integers, location encoding, report index, and time metadata so consumers can
audit the displayed point. Targets without a complete location are omitted
from the Point collection.

For a ready-to-save file, use the
[GeoJSON CLI command](CLI.md#export-locations). The
[GeoJSON API](api/validation.md) documents
the function signature.
