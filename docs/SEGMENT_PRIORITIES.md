# Segment support priorities

AEDP-4607.1 Annex G section G.7 defines Mission (type 1), Dwell (type 2), and
Job Definition (type 5) as the Common Core Requirement. All three are implemented.
Remaining work is prioritized by current application value and available evidence,
not by segment number or nominal coverage.

| Priority | Segment | Rationale |
|---|---|---|
| Implemented core | Mission, Dwell, Job Definition | Required by the Annex G Common Core and exercised by attributed public Edition 4 samples. |
| Implemented practical | Processing History (12) | Preserves the lineage of filtering, classification, registration, and other modifications, including multi-stage AI enrichment. |
| Implemented practical | Platform Location (13) | Carries platform state while the sensor is not collecting, preserving track continuity for live applications. |
| Implemented practical | Test and Status (10) | Exposes job-specific sensor health, hardware failures, and exceeded operational limits for live monitoring. |
| Implemented practical | Free Text (6) | Preserves operator and system annotations losslessly while validating the standard's Basic Character Set. |
| Implemented practical profile | HRR (3) | H1-H31 fixed metadata and uncompressed H32 records are typed and a public synthetic packet is pinned; compressed threshold-decomposition remains bounded and opaque pending a defined algorithm or partner vector. |
| Implemented recommended | Job Request (101), Job Acknowledge (102) | Chapter 4 fixed structures and mechanical validation are implemented; end-to-end tasking policy and interoperability remain partner-owned. |
| Out of scope | Reserved types 4, 7-9, 11, 14-100, 103-255 | The normative edition reserves these values; opaque framing already preserves them safely. |

This order should change when a design partner, representative corpus, or
authoritative amendment supplies stronger evidence. A claimed segment is not complete
until its parser, encoder, malformed-input behavior, bounds, trace, and realistic
round-trip tests are all present.
