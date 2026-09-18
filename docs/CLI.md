# Command line

The `stanag4607` command inspects, validates, and exports packet streams
incrementally. Install the package before running these examples. Unless
specified otherwise, paths are relative to the repository root.

## Inspect

```console
stanag4607 inspect tests/fixtures/mission_dwell_hi_res_targets.gmti
```

The command emits one JSON object per segment. Each record includes packet and
segment indices and the decoded type; recognized Dwell segments also include a
target count and UTC time when Mission context permits one. To read from a
pipe, pass `-` as the input path:

```console
stanag4607 inspect -
```

## Validate

```console
stanag4607 validate tests/fixtures/mission_dwell_hi_res_targets.gmti
stanag4607 validate --max-issues 1000 tests/fixtures/mission_dwell_hi_res_targets.gmti
```

The JSON report contains `valid` and `issues`. Issue retention is bounded
(10,000 by default); a truncated report also includes the total issue count
and omitted count. The command uses the current Edition A validation profile.
The [conformance matrix](CONFORMANCE.md) lists its checks.

## Export locations

```console
stanag4607 geojson tests/fixtures/mission_dwell_hi_res_targets.gmti > targets.geojson
```

Output is one GeoJSON FeatureCollection. Only targets with a complete
reconstructable location become Point features. See
[target geometry and GeoJSON](GEOJSON.md).

## Replay a file locally

```console
stanag4607 demo tests/fixtures/mission_dwell_hi_res_targets.gmti --interval 0.5
```

Open `http://127.0.0.1:8768/` and stop with Ctrl-C. The demo server has no
authentication or TLS, so keep the default loopback host for local use.
