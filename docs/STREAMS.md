# Live streams and context

Feed `ContextualStreamDecoder` any sequence of byte chunks. It frames packets,
emits typed segment events, and carries bounded Mission and Job Definition
context between packets.

```python
from pathlib import Path

from stanag4607 import ContextualStreamDecoder, DwellSegment

decoder = ContextualStreamDecoder()
with Path("tests/fixtures/mission_dwell_hi_res_targets.gmti").open("rb") as source:
    for chunk in iter(lambda: source.read(17), b""):
        for item in decoder.feed(chunk):
            if isinstance(item.event.value, DwellSegment):
                print(item.dwell_time_utc, item.event.value.target_report_count)
decoder.finish()
```

The same loop can consume bytes from a network receiver, file reader, or
message transport supplied by your application. The library handles protocol
packetization; your application decides how to receive and recover transport
data.

## Time and lifecycle

Dwell, Platform Location, and Test and Status times are Mission-relative
millisecond values. A valid Mission reference date lets the decoder expose
`event_time_utc` as an aware UTC `datetime`. Without that context it remains
`None`. Invalid dates or unrepresentable arithmetic produce
`event_time_issue` rather than an invented timestamp.

`context_update` reports new, repeated, replaced, and evicted Mission/Job
context. The caller can use those events to audit stream state. Context and
packet buffers have configurable bounds; inspect the
[stream API](api/streams.md) for their limits.

Call `finish()` after the final chunk. It reports an incomplete final packet.
Malformed input fails closed, and `reset()` starts again at a boundary known
to the caller. The format has no reliable magic marker for automatic
resynchronization.

For sequence diagnostics, feed each `item.event` to
`StreamContinuityValidator.observe()`. It reports locally decidable Dwell
and HRR index faults while retaining bounded per-job state. See
[conformance](CONFORMANCE.md) for the exact rules.
