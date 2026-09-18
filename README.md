# stanag4607

`stanag4607` is an MIT-licensed, pure-Python toolkit for STANAG 4607 Ground
Moving Target Indicator (GMTI) data. It reads, writes, validates, and displays
radar packets and their target reports.

Use it to build radar ingest services, stream diagnostics, geospatial exports,
and applications that display GMTI beside Full Motion Video or other sensor
feeds.

## Try it

Python 3.10 or newer is required. Clone the repository to run the bundled
sample and examples:

```console
git clone https://github.com/trane293/stanag4607.git
cd stanag4607
python -m pip install .
```

For an installation without the source examples, use
`python -m pip install stanag4607` once the distribution is available on PyPI.

Inspect and validate the included sample:

```console
stanag4607 inspect tests/fixtures/mission_dwell_hi_res_targets.gmti
stanag4607 validate tests/fixtures/mission_dwell_hi_res_targets.gmti
stanag4607 geojson tests/fixtures/mission_dwell_hi_res_targets.gmti > targets.geojson
```

Open the local replay demo at `http://127.0.0.1:8768/`:

```console
stanag4607 demo tests/fixtures/mission_dwell_hi_res_targets.gmti
```

The page shows packet validity, segment activity, and located target points as
the sample passes through the incremental decoder.

![Local GMTI replay with validity, target positions, and activity](https://raw.githubusercontent.com/trane293/stanag4607/main/docs/assets/screenshots/local-demo.png)

## What you can build

- Inspect GMTI files or pipes and report packet, field, and continuity issues.
- Decode Mission, Dwell, Target Report, Job Definition, HRR, and other commonly
  used segments into typed Python values.
- Process chunked streams with bounded state and Mission-relative UTC timestamps.
- Export target locations and their original coordinate values as GeoJSON.
- Carry time, position, uncertainty, identity, and provenance into a map,
  analytics service, or downstream sensor adapter.

The core has no required third-party Python dependencies.

## Read a stream from Python

This example runs from the cloned repository:

```python
from pathlib import Path

from stanag4607 import ContextualStreamDecoder, DwellSegment

decoder = ContextualStreamDecoder()
with Path("tests/fixtures/mission_dwell_hi_res_targets.gmti").open("rb") as source:
    for chunk in iter(lambda: source.read(4096), b""):
        for item in decoder.feed(chunk):
            if isinstance(item.event.value, DwellSegment):
                print(item.dwell_time_utc, item.event.value.target_report_count)
decoder.finish()
```

The [quickstart](https://github.com/trane293/stanag4607/blob/main/docs/QUICKSTART.md)
walks through inspection, validation, GeoJSON export, and the replay demo.

## Choose a workflow

| I want to… | Start here |
| --- | --- |
| Run the included sample | [Quickstart](https://github.com/trane293/stanag4607/blob/main/docs/QUICKSTART.md) |
| Read a stream from Python | [Live streams and context](https://github.com/trane293/stanag4607/blob/main/docs/STREAMS.md) |
| Export target points | [Target geometry and GeoJSON](https://github.com/trane293/stanag4607/blob/main/docs/GEOJSON.md) |
| Understand supported fields and validation | [Conformance matrix](https://github.com/trane293/stanag4607/blob/main/docs/CONFORMANCE.md) |
| Integrate GMTI with another sensor feed | [Architecture](https://github.com/trane293/stanag4607/blob/main/docs/ARCHITECTURE.md) |

## Standards support at a glance

| Status | STANAG 4607 Edition 4 / AEDP-4607 Edition A Version 1 scope |
| --- | --- |
| **Implemented software-verifiable profile** | Packet and segment framing; Mission; Dwell and Target Reports; Job Definition; Free Text; Processing History; Platform Location; Test and Status; Job Request and Job Acknowledge; HRR fixed metadata and uncompressed scatterers; contextual events and validation |
| **Partial or preservation-only** | Job Definition geographic validation; compressed HRR scatterers; registered extensions without published payload layouts |
| **Future or separate work** | General historical-edition profiles; network transport adapters; production visualization; cross-sensor fusion |

The [conformance matrix](https://github.com/trane293/stanag4607/blob/main/docs/CONFORMANCE.md)
shows field-level evidence and the [limitations](https://github.com/trane293/stanag4607/blob/main/docs/LIMITATIONS.md)
explain interoperability boundaries. The supported baseline is STANAG 4607
Edition 4 / AEDP-4607 Edition A Version 1.

## Design principles

- Keep the protocol core pure Python and dependency-free.
- Parse incrementally with explicit limits, failure, and finalization behavior.
- Preserve exact wire values and unknown data through applicable round trips.
- Keep validation separate from decoding.
- Retain standard-defined time, geometry, uncertainty, identity, and provenance
  for downstream adapters.
- Tie support claims to a named edition, requirement trace, and executable tests.

## Documentation

The documentation includes a [quickstart](https://github.com/trane293/stanag4607/blob/main/docs/QUICKSTART.md),
[runnable examples](https://github.com/trane293/stanag4607/blob/main/docs/EXAMPLES.md),
a [Python API reference](https://github.com/trane293/stanag4607/blob/main/docs/api/index.md),
and detailed [standards coverage](https://github.com/trane293/stanag4607/blob/main/docs/CONFORMANCE.md).
The public API is pre-1.0; see the [stability policy](https://github.com/trane293/stanag4607/blob/main/docs/API_STABILITY.md).

## Contributing

Development is specification-led and test-driven. See
[CONTRIBUTING.md](https://github.com/trane293/stanag4607/blob/main/CONTRIBUTING.md)
for setup, tests, standards provenance, and pull-request guidance.

## License

[MIT](https://github.com/trane293/stanag4607/blob/main/LICENSE). The bundled
sample retains its [Apache-2.0 terms](https://github.com/trane293/stanag4607/blob/main/THIRD_PARTY_NOTICES.md).
