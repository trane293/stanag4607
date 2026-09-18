# Python API

The public API is exported from `stanag4607`. These pages group it by the task
you are building:

| Task | Reference |
| --- | --- |
| Decode one packet, inspect headers, preserve bytes | [Packets and framing](packets.md) |
| Consume chunks, carry Mission/Job context, check continuity | [Streams and events](streams.md) |
| Read typed GMTI reports and exact geometry | [Segments and geometry](segments.md) |
| Check requirements or export target points | [Validation and export](validation.md) |

Names in `stanag4607.__all__`, the command-line interface, issue codes, and
wire behavior follow the [pre-1.0 stability policy](../API_STABILITY.md).
For the intended learning path, start with the
[quickstart](../QUICKSTART.md) or [examples](../EXAMPLES.md).
