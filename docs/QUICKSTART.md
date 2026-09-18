# Quickstart

In a few minutes you will inspect a GMTI packet, check its validity, export
target coordinates, and open the local replay view.

## 1. Install the source checkout

Follow [installation](INSTALLATION.md), then stay in the repository root. The
commands below use its bundled synthetic fixture:

```console
python -m pip install .
```

## 2. Inspect and validate

```console
stanag4607 inspect tests/fixtures/mission_dwell_hi_res_targets.gmti
stanag4607 validate tests/fixtures/mission_dwell_hi_res_targets.gmti
```

The Dwell inspection record contains `"target_count": 3` and
`"dwell_time_utc": "2026-04-29T08:30:00+00:00"`. Validation returns:

```json
{"issues": [], "valid": true}
```

Validation reports the software-verifiable rules in the
[conformance matrix](CONFORMANCE.md) without rewriting the packet.

## 3. Export target locations

```console
stanag4607 geojson tests/fixtures/mission_dwell_hi_res_targets.gmti > targets.geojson
```

Open `targets.geojson` in a GIS tool or inspect it as JSON. It contains three
Point features, their observation time, and the raw coordinate values behind
each exported position. Longitude and latitude are in GeoJSON order.

## 4. Replay in the local demo

```console
stanag4607 demo tests/fixtures/mission_dwell_hi_res_targets.gmti
```

Open `http://127.0.0.1:8768/` and stop the server with Ctrl-C. The page shows
validity, segment activity, and a simple coordinate plot. Keep the default
loopback address because the demo server has no authentication or TLS.

![Replay of the bundled synthetic sample with target points and activity](assets/screenshots/local-demo.png)

## 5. Use the Python API

Run the [tested target-location example](EXAMPLES.md#inspect-targets-with-context)
to print UTC time and each location. If your input arrives in chunks, start
with [live streams and context](STREAMS.md).

For other files, replace the fixture path in the CLI commands. The CLI also
accepts standard input as `-`, for example `stanag4607 inspect -`. The
[sample guide](SAMPLES.md) explains which public captures are useful and why
older versions are not normative Edition A evidence.
