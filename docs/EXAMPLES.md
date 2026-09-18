# Runnable examples

These examples use the attributed synthetic file included in the source
checkout. Run the commands from the repository root after
[installation](INSTALLATION.md). Both Python scripts are exercised in the test
suite against that exact file.

## Inspect targets with context

[View the complete script](https://github.com/trane293/stanag4607/blob/main/examples/inspect_targets.py).
It feeds file chunks to `ContextualStreamDecoder`, resolves the Dwell time using
Mission context, and prints available target locations:

```console
python examples/inspect_targets.py tests/fixtures/mission_dwell_hi_res_targets.gmti
```

Expected excerpt:

```text
2026-04-29T08:30:00+00:00: 3 targets
target 0: 57.100000, 24.500000 (high_resolution)
```

The printed decimal coordinates are approximate for display. The decoded
binary-angle objects retain exact wire values. A Dwell can legitimately omit a
complete target location, in which case the script prints
`location unavailable`.

## Verify byte-identical round trips

[View the complete script](https://github.com/trane293/stanag4607/blob/main/examples/round_trip.py).
It re-encodes each packet and compares bytes against the original file without
retaining the entire stream in memory:

```console
python examples/round_trip.py tests/fixtures/mission_dwell_hi_res_targets.gmti
```

Expected output:

```text
packets: 1
byte-identical: yes
```

Unknown segment payloads and reserved values are retained through packet
round trips. For operational conformance questions, continue with
[validation](CLI.md#validate) and the [conformance matrix](CONFORMANCE.md).

## Export GeoJSON

```console
stanag4607 geojson tests/fixtures/mission_dwell_hi_res_targets.gmti > targets.geojson
```

Use [target geometry and GeoJSON](GEOJSON.md) for the library API and the
conditions under which a point can be exported. The
[CLI guide](CLI.md) covers inspection, validation, standard input, and the
local demo.
