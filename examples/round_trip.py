"""Verify byte-identical decode/encode for every packet in a file.

Run from the repository root:
    python examples/round_trip.py tests/fixtures/mission_dwell_hi_res_targets.gmti
"""

from __future__ import annotations

import argparse
from pathlib import Path

from stanag4607 import PacketStreamDecoder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="STANAG 4607 packet file")
    args = parser.parse_args()

    decoder = PacketStreamDecoder()
    packet_count = 0
    identical = True
    with args.input.open("rb") as source, args.input.open("rb") as original:
        for chunk in iter(lambda: source.read(4096), b""):
            for packet in decoder.feed(chunk):
                encoded = packet.to_bytes()
                identical = identical and encoded == original.read(len(encoded))
                packet_count += 1
        decoder.finish()
        identical = identical and not original.read(1)

    print(f"packets: {packet_count}")
    print(f"byte-identical: {'yes' if identical else 'no'}")
    if not identical:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
