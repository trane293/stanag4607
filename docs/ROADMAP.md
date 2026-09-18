# Roadmap and development state

## Current state

The Edition A Version 1 profile includes:

- bounded, lossless packet framing and incremental decoding across arbitrary
  chunks, with explicit truncation and fail-closed behavior;
- typed Mission, Dwell and Target Report, Job Definition, Free Text, Test and
  Status, Processing History, Platform Location, and recommended tasking
  segments;
- typed HRR fixed metadata and uncompressed scatterers, with compressed
  threshold-decomposition retained as opaque bytes;
- exact binary-angle and decimal values, contextual UTC time, bounded
  Mission/Job state, and conservative Dwell/HRR continuity diagnostics; and
- structured validation, GeoJSON target export, CLI commands, and a local
  replay view.

Typed events retain the original packet header, wire segment, and segment
index for downstream adapters. The official STANAG 4607 Edition 4,
AEDP-4607 Edition A Version 1, and AEDP-4607.1 texts are recorded in
`references/standards/manifest.json` and kept in a Git-ignored local archive.
The [conformance matrix](CONFORMANCE.md) gives field-level evidence and the
[limitations](LIMITATIONS.md) define the current interoperability boundary.

Every increment follows the goal-seeking TDD cycle in
`docs/DEVELOPMENT.md`: select one practical evidence-backed outcome, observe a
failing test, implement the minimum correct behavior, run complete gates, record
a clean commit, and reassess the next goal from the resulting state.

The [production-readiness assessment](PRODUCTION_READINESS.md) separates
library quality from the partner-specific evidence needed for field deployment.

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
4. Before the first PyPI release, complete the API, clean-wheel-install,
   documentation, security, and fixture-license audit in
   [Releasing](RELEASING.md). Keep field-deployment claims tied to the separate
   [production-readiness evidence](PRODUCTION_READINESS.md).

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
