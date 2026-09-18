# stanag4607

`stanag4607` is an MIT-licensed, pure-Python toolkit for STANAG 4607 Ground
Moving Target Indicator (GMTI) data. It reads, validates, preserves, and writes
radar packets and segments, including data arriving in arbitrary stream chunks.

Use it to build radar-data ingest services, stream diagnostics, geospatial
exports, and applications that bring GMTI alongside Full Motion Video or other
sensor feeds. The library supplies the standard-defined data; cross-sensor
fusion remains the application's responsibility.

## Try it

Python 3.10 or newer is required. The package is not on PyPI yet, so install it
from the source repository:

```console
git clone https://github.com/trane293/stanag4607.git
cd stanag4607
python -m pip install .
```

Inspect and validate the small synthetic sample included in the source tree:

```console
stanag4607 inspect tests/fixtures/mission_dwell_hi_res_targets.gmti
stanag4607 validate tests/fixtures/mission_dwell_hi_res_targets.gmti
stanag4607 geojson tests/fixtures/mission_dwell_hi_res_targets.gmti > targets.geojson
```

To watch the same sample pass through the incremental decoder and validators,
start the local replay demo and open `http://127.0.0.1:8768/`:

```console
stanag4607 demo tests/fixtures/mission_dwell_hi_res_targets.gmti
```

The demo shows packet validity, activity, and located target points. It is a
localhost protocol demonstration, not a production map, live network receiver,
or fusion application.

## What you can build

- Inspect GMTI files or standard input and report malformed packets, segment
  fields, and continuity issues without silently changing the source data.
- Decode Mission, Dwell, Target Report, Job Definition, HRR, and practical
  optional segments into typed Python values.
- Process an arbitrarily chunked byte stream with bounded parser and context
  state, explicit truncation errors, and Mission-relative UTC timestamps when
  enough context is present.
- Export located targets as GeoJSON, including the original coordinate values
  needed to audit the result.
- Feed standard-defined times, positions, uncertainty, identity, and provenance
  into your own visualization or sensor-fusion adapter.

The core has no required third-party Python dependencies. It does not bundle a
radar simulator, network transport, GIS runtime, or fusion engine.

## Read a stream from Python

This example runs from the cloned repository and uses its bundled sample:

```python
from pathlib import Path

from stanag4607 import ContextualStreamDecoder, DwellSegment

data = Path("tests/fixtures/mission_dwell_hi_res_targets.gmti").read_bytes()
decoder = ContextualStreamDecoder()

for offset in range(0, len(data), 17):  # A file, socket, or pipe can supply chunks.
    for item in decoder.feed(data[offset : offset + 17]):
        if isinstance(item.event.value, DwellSegment):
            print("time:", item.dwell_time_utc)
            print("targets:", item.event.value.target_report_count)

decoder.finish()  # Raises on a truncated final packet.
```

For one complete packet, `decode_packet(raw).to_bytes() == raw` preserves its
original wire bytes, including unsupported segment payloads. See the
[conformance matrix](https://github.com/trane293/stanag4607/blob/main/docs/CONFORMANCE.md)
for the exact typed and validated fields.

## Choose a workflow

| I want to… | Start here |
| --- | --- |
| Check or visualize a sample | [Sample guide](https://github.com/trane293/stanag4607/blob/main/docs/SAMPLES.md) |
| Understand supported fields and validation | [Conformance matrix](https://github.com/trane293/stanag4607/blob/main/docs/CONFORMANCE.md) |
| Consume GMTI beside another sensor feed | [Architecture and fusion boundary](https://github.com/trane293/stanag4607/blob/main/docs/ARCHITECTURE.md) |
| Know what is not implemented | [Limitations](https://github.com/trane293/stanag4607/blob/main/docs/LIMITATIONS.md) |
| Evaluate an operational deployment | [Production-readiness checklist](https://github.com/trane293/stanag4607/blob/main/docs/PRODUCTION_READINESS.md) |

## Standards support at a glance

| Status | STANAG 4607 Edition 4 / AEDP-4607 Edition A Version 1 scope |
| --- | --- |
| **Implemented for the documented profile** | Bounded packet and segment framing; Mission; Dwell and Target Reports; Job Definition; Free Text; Processing History; Platform Location; Test and Status; recommended Job Request and Job Acknowledge; HRR fixed metadata and uncompressed scatterers; contextual stream events; software-verifiable validation |
| **Partial or opaque by design** | Job Definition geographic validation is incomplete; compressed HRR scatterers and registered extensions without published payload layouts remain lossless opaque bytes |
| **Not claimed** | General historical-edition conformance, automatic resynchronization after corruption, operational radar interoperability, network transport adapters, production visualization, or cross-sensor fusion |

The default packet-context rules follow Edition A Version 1. A narrow,
explicitly opt-in profile handles one observed Version 3.0 Job Definition
convention; it is not general Edition 3 support. No NATO certification or
complete operational conformance is claimed. Read the
[requirement trace](https://github.com/trane293/stanag4607/blob/main/docs/requirements/AEDP-4607-EDA-V1.md)
and [limitations](https://github.com/trane293/stanag4607/blob/main/docs/LIMITATIONS.md)
before depending on a particular field or producer profile.

STANAG 4607 describes GMTI exchange, not the maritime Automatic Identification
System (AIS).

## Design principles

- Keep the protocol core pure Python and dependency-free.
- Parse incrementally with explicit limits, failure, and finalization behavior.
- Preserve exact wire values and unknown data through applicable round trips.
- Separate non-destructive validation from decoding and producer-owned truth.
- Retain standard-defined time, geometry, uncertainty, identity, and provenance
  without embedding private fusion policy.
- Tie support claims to a named edition, requirement trace, and executable tests.

## Documentation

Start with the [sample guide](https://github.com/trane293/stanag4607/blob/main/docs/SAMPLES.md)
or browse the [documentation directory](https://github.com/trane293/stanag4607/tree/main/docs).
The public API is pre-1.0; review the
[API stability policy](https://github.com/trane293/stanag4607/blob/main/docs/API_STABILITY.md)
before depending on extension points. Standards documents and large sample
captures are recorded in manifests rather than copied into Git.

## Contributing

Development is specification-led and test-driven. See
[CONTRIBUTING.md](https://github.com/trane293/stanag4607/blob/main/CONTRIBUTING.md)
for setup, tests, standards provenance, and pull-request guidance.

## License

[MIT](https://github.com/trane293/stanag4607/blob/main/LICENSE). The bundled
synthetic fixture and any external samples or standards texts retain their own
terms; see [third-party notices](https://github.com/trane293/stanag4607/blob/main/THIRD_PARTY_NOTICES.md).
