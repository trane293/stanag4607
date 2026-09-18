# Packets and segments

Use `decode_packet()` when you have exactly one complete STANAG 4607 packet.
Use `PacketStreamDecoder` when packet boundaries do not line up with file,
socket, or pipe reads.

Every packet contains a 32-byte header and zero or more length-delimited
segments. The packet model keeps headers, segment order, and original payload
bytes available for a byte-identical `to_bytes()` round trip.

```python
from pathlib import Path

from stanag4607 import decode_packet, iter_packet_events

raw = Path("tests/fixtures/mission_dwell_hi_res_targets.gmti").read_bytes()
packet = decode_packet(raw)
print(packet.header.platform_id, len(packet.segments))
assert packet.to_bytes() == raw

for event in iter_packet_events(packet):
    print(event.segment_index, type(event.value).__name__)
```

`iter_packet_events()` decodes supported segment bodies in wire order.
Each event also retains the packet header and original segment. An extension
whose payload layout is unavailable remains an opaque `Segment` that can
still be inspected and re-encoded.

Character fields are exact bytes. Validation checks their repertoire without
changing them. For the implemented fields and requirement evidence, see
[conformance](CONFORMANCE.md).

The [packet API](api/packets.md) documents limits, models, and decoding
functions. For chunked input, continue with
[live streams and context](STREAMS.md).
