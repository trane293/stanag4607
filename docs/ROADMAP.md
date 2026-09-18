# Roadmap and development state

## Current state

This repository now implements bounded, lossless structural decoding and
encoding of complete packets, the fixed 32-byte packet header, and 5-byte
segment headers. A fail-closed, bounded incremental decoder handles arbitrary
stream chunks and terminal truncation. Mission Segments are typed and preserve
the reference date needed by later time-bearing reports. Exact BA16/BA32 and
SA16/SA32 values preserve raw coordinate bits and expose rational degrees. The
complete Dwell and Target Report structures are decoded losslessly with typed,
unit-explicit accessors for every field, including exact target coordinates for
both direct and reduced-bandwidth representations. Structured, non-destructive
Dwell validation covers the principal field-presence groups and classification
probability. Job Definition J1-J28 supplies exact task, radar-mode,
bounding-area, earth-model, and nominal-uncertainty context. Free Text, Test and
Status, Processing History, and Platform Location cover the practical optional
application segments. HRR fixed metadata H1-H31 and uncompressed H32 scatterer
records are typed and validated, with independent per-job continuity state;
threshold-decomposition remains bounded, lossless, and opaque. Reserved and
unsupported payloads remain opaque. Recommended Chapter 4 Job Request and Job
Acknowledge messages are typed and validated without embedding scheduling or
authorization policy. Typed segment events retain
their exact packet header, segment
index, and wire segment for downstream adapters. A bounded contextual stream
decoder carries Mission/Job state across arbitrary chunks and resolves exact
millisecond Dwell, Test and Status, and Platform Location timestamps to UTC when a
valid Mission date is known. Complete
target positions export to dependency-free GeoJSON with raw-coordinate
provenance for sample visualization. Mission/Job context lifecycle changes and
deterministic LRU evictions are observable by downstream adapters. A lightweight
localhost replay UI demonstrates live validation and located targets using the
same public APIs; it is not a production visualization or fusion layer. The current
official baseline, STANAG 4607 Edition 4 with AEDP-4607 Edition A Version 1 and its
AEDP-4607.1 implementation guide, has been acquired from NATO's public database
and stored in the local Git-ignored standards archive.

Every increment follows the goal-seeking TDD cycle in
`docs/DEVELOPMENT.md`: select one practical evidence-backed outcome, observe a
failing test, implement the minimum correct behavior, run complete gates, record
a clean commit, and reassess the next goal from the resulting state.

The current go/no-go assessment and operational evidence gaps are maintained in
`docs/PRODUCTION_READINESS.md`. Further protocol expansion is evidence-led and
does not block publishing the documented, limited open-source profile.

Parallax FR-001 is resolved by structured contextual time diagnostics: invalid
Mission dates and overflowing Mission-relative arithmetic no longer escape from
the stream decoder, and a later valid Mission context recovers deterministically.
Parallax FR-002 is resolved by an explicit opt-in compatibility profile for the
exact Version 3.0 Job Definition-only P10/J1 convention observed in Wireshark
issue 19566. The Edition A default is unchanged; general historical-edition
support remains out of scope.

## Product architecture constraint

The future closed-source product will correlate STANAG 4607 GMTI with STANAG
4609 FMV and additional sensor feeds. This repository must preserve every
standard-defined time, geometry, uncertainty, identity, provenance, and stream
state needed by the product's adapter, using stable bounded event APIs.

Cross-sensor association and fusion remain outside this repository. Do not add
a universal observation model, matching rules, fusion windows, confidence
policy, fused tracks, threat scoring, or product storage here. Apply the review
contract in `docs/ARCHITECTURE.md` to each protocol increment.

## Next increments

1. Confirm whether any amendments, controlled extensions, or implementation
   constraints apply to the first intended interoperability partner.
2. Obtain an authoritative threshold-decomposition algorithm or partner vectors
   before interpreting compressed H16=1 H32 payloads.
3. Seek source authentication for the public Version 3.0 operation/real capture
   and a current Edition A Version 1 operational or official corpus. Retain the
   current synthetic, AFRL exercise, and unauthenticated capture corpora as
   non-normative interoperability evidence.
4. Before a public package release, run the API, clean-wheel-install,
   documentation, security, and fixture-license audit in `docs/RELEASING.md`.
   A public source snapshot is separate from PyPI publication and from claims
   of operational deployment readiness.

## Questions to resolve with the project owner or first design partner

- Which interoperability partner and operational profile matter first?
- What additional representative data may lawfully be used in automated tests?
- Which deployment environments and throughput bounds matter?

## Explicit non-goals until instructed

- AIS maritime message support.
- A management platform or hosted service.
- Production UI, basemap, database, or message-bus choices.
- Broad historical-edition compatibility.
- Claims of NATO certification or complete conformance.
- Cross-sensor association, track fusion, or the private product domain model.
