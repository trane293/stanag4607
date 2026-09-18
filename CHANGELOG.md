# Changelog

This project follows Semantic Versioning and records user-visible changes here.

## Unreleased

### Added

- Structured contextual time diagnostics for invalid Mission dates and
  unrepresentable Mission-relative UTC arithmetic.
- An opt-in Version 3.0 Job Definition packet-context compatibility profile,
  verified against the local SHA-256-pinned Wireshark issue 19566 stream while
  preserving strict Edition A validation by default.
- A dependency-free localhost replay UI for live validation, segment activity,
  and target-position visualization over public sample or user-supplied files.
- Exact typed uncompressed HRR H32 scatterer records, record-size diagnostics, and
  sparse H7 count validation while retaining compressed payloads losslessly.
- Exact typed Chapter 4 Job Request and Job Acknowledge segments with structured
  validation and CLI/live-demo integration.
- Fusion-ready UTC conveniences for ordinary tasking timestamps, exact leap-second
  component preservation, and calendar-date diagnostics.

## 0.1.0 - 2026-09-12

### Added

- Bounded complete and incremental packet framing with lossless unknown segments.
- Typed Mission, Dwell/Target Report, Job Definition, Free Text, Test and Status,
  Processing History, and Platform Location segments.
- Exact binary angles, Mission-relative UTC context, conservative Dwell continuity
  diagnostics, non-destructive validation, GeoJSON export, and CLI workflows.
- Exact signed B16/B32/H32 decimals and lossless HRR H1-H31 fixed metadata with a
  bounded opaque H32 scatterer region.
- Non-destructive HRR validation for data-type field relationships, numeric ranges,
  byte-width declarations, flags, enumerations, and reserved bits.
- Independent bounded Dwell and HRR continuity state per platform, mission, and job.
- Bounded CLI validation reports with configurable retained-issue limits and exact
  truncation counts.
- Explicit Mission/Job context lifecycle events for new, repeated, replaced, and
  LRU-evicted context.
- Attributed Apache-2.0 synthetic Edition 4 interoperability fixtures.

### Security

- Packet and segment counts, target counts, stream buffers, and retained contexts
  are caller-bounded; complete packet input is checked before copying.
