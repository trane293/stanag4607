"""Print timestamped STANAG 4607 target locations from a file.

Run from the repository root:
    python examples/inspect_targets.py tests/fixtures/mission_dwell_hi_res_targets.gmti
"""

from __future__ import annotations

import argparse
from pathlib import Path

from stanag4607 import ContextualStreamDecoder, DwellSegment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="STANAG 4607 packet file")
    args = parser.parse_args()

    decoder = ContextualStreamDecoder()
    with args.input.open("rb") as source:
        for chunk in iter(lambda: source.read(4096), b""):
            for item in decoder.feed(chunk):
                dwell = item.event.value
                if not isinstance(dwell, DwellSegment):
                    continue
                timestamp = item.dwell_time_utc.isoformat() if item.dwell_time_utc else "unknown"
                print(f"{timestamp}: {dwell.target_report_count} targets")
                for index in range(dwell.target_report_count):
                    location = dwell.target_location(index)
                    if location is None:
                        print(f"target {index}: location unavailable")
                        continue
                    # Decimal display is approximate; the model retains exact binary angles.
                    latitude = float(location.latitude.degrees)
                    longitude = float(location.longitude.degrees)
                    print(
                        f"target {index}: {latitude:.6f}, {longitude:.6f} "
                        f"({location.encoding})"
                    )
    decoder.finish()


if __name__ == "__main__":
    main()
