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

The [quickstart](https://stanag4607.readthedocs.io/en/latest/QUICKSTART/)
walks through inspection, validation, GeoJSON export, and the replay demo.

## Choose a workflow

| I want to… | Start here |
| --- | --- |
| Run the included sample | [Quickstart](https://stanag4607.readthedocs.io/en/latest/QUICKSTART/) |
| Read a stream from Python | [Live streams and context](https://stanag4607.readthedocs.io/en/latest/STREAMS/) |
| Export target points | [Target geometry and GeoJSON](https://stanag4607.readthedocs.io/en/latest/GEOJSON/) |
| Understand supported fields and validation | [Conformance matrix](https://stanag4607.readthedocs.io/en/latest/CONFORMANCE/) |
| Integrate GMTI with another sensor feed | [Architecture](https://stanag4607.readthedocs.io/en/latest/ARCHITECTURE/) |

## Standards support at a glance

| Status | STANAG 4607 Edition 4 / AEDP-4607 Edition A Version 1 scope |
| --- | --- |
| **Implemented software-verifiable profile** | Packet and segment framing; Mission; Dwell and Target Reports; Job Definition; Free Text; Processing History; Platform Location; Test and Status; Job Request and Job Acknowledge; HRR fixed metadata and uncompressed scatterers; contextual events and validation |
| **Partial or preservation-only** | Job Definition geographic validation; compressed HRR scatterers; registered extensions without published payload layouts |
| **Future or separate work** | General historical-edition profiles; network transport adapters; production visualization; cross-sensor fusion |

The [conformance matrix](https://stanag4607.readthedocs.io/en/latest/CONFORMANCE/)
shows field-level evidence and the [limitations](https://stanag4607.readthedocs.io/en/latest/LIMITATIONS/)
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

The documentation includes a [quickstart](https://stanag4607.readthedocs.io/en/latest/QUICKSTART/),
[runnable examples](https://stanag4607.readthedocs.io/en/latest/EXAMPLES/),
a [Python API reference](https://stanag4607.readthedocs.io/en/latest/api/),
and detailed [standards coverage](https://stanag4607.readthedocs.io/en/latest/CONFORMANCE/).
The public API is pre-1.0; see the [stability policy](https://stanag4607.readthedocs.io/en/latest/API_STABILITY/).

## Contributing

Development is specification-led and test-driven. See
[CONTRIBUTING.md](https://github.com/trane293/stanag4607/blob/main/CONTRIBUTING.md)
for setup, tests, standards provenance, and pull-request guidance.

## License

[MIT](https://github.com/trane293/stanag4607/blob/main/LICENSE). The bundled
sample retains its [Apache-2.0 terms](https://github.com/trane293/stanag4607/blob/main/THIRD_PARTY_NOTICES.md).
