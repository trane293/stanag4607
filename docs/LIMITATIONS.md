# Current limitations

- Complete packets and 5-byte segment headers can be framed. Mission, Dwell,
  Target Report, Job Definition, Free Text, Test and Status, Processing History,
  Platform Location, Job Request, and Job Acknowledge payloads have typed support;
  reserved, undefined, and undocumented extension payloads remain opaque.
- `decode_packet_header()` intentionally accepts exactly the 32-byte header;
  `decode_packet()` accepts exactly one complete packet.
- Character fields are exposed as exact bytes. Annex A BCS repertoire validation
  covers implemented typed character fields; left-justified padding semantics are
  not inferred beyond the explicit all-space prohibition for Free Text fields.
- Structural decoding preserves reserved enumeration values but does not decide
  whether they are semantically acceptable for a particular operational profile.
- Incremental streams are packetized across arbitrary chunks, but malformed input
  fails closed. Automatic byte-scanning resynchronization is deliberately absent
  because the wire format has no magic marker and guessing a new boundary could
  silently create false GMTI data.
- Packet events decode supported segment values and retain exact packet/segment
  provenance. `ContextualStreamDecoder` carries bounded Mission/Job state across
  packets. `StreamContinuityValidator` detects locally decidable Dwell and HRR
  sequence faults using independent per-job state, but it does not infer whether
  revisit resets are legitimate or enforce periodic transmission requirements.
  Context insertion, repetition, replacement, and LRU eviction are explicit, but
  contexts are not expired by an invented wall-clock policy.
  Invalid Mission dates and event-time arithmetic outside Python's representable
  UTC range produce an `event_time_issue` and no absolute time; context remains
  available until replaced, evicted, or explicitly reset.
- Network transport adapters, production visualization, and fusion behavior do
  not exist. The local replay UI is only a demonstration. Typed standard-defined
  time, geometry, uncertainty, and target values are limited to the implemented
  segment profiles.
- HRR H1-H31 metadata is typed and exact. Uncompressed H32 scatterers expose exact
  typed magnitude, phase, and conditional range/Doppler indices while retaining
  the original byte region. H16=1 threshold-decomposition remains bounded and
  opaque because the edition names a 10x technique but does not define a complete
  decompression wire algorithm. H7 count agreement is enforced for sparse H23=3;
  broader count semantics are not inferred across every HRR/RDM data type.
- Table 3-13 labels H32.3/H32.4 as I16 with range 0-65535 but prints a contradictory
  one-byte width. This implementation uses two bytes, the only width compatible
  with both the declared form and range, and records that interpretation explicitly.
- Target points can be exported as dependency-free GeoJSON, but dwell footprints,
  uncertainty shapes, map rendering, spatial indexing, and coordinate-reference
  transformations are not implemented.
- The localhost demo is a bounded-DOM replay and validation view over one file.
  Its coordinate plot is deliberately dependency-free and is not a geographic
  basemap, operational UI, network ingest service, or fusion product. The server
  has no authentication or TLS; keep the default loopback host unless exposure is
  protected by infrastructure appropriate for the data.
- The CLI reads packet data incrementally and streams inspection/GeoJSON output.
  Validation examines the complete input while retaining at most 10,000 issues
  by default; `--max-issues` changes that explicit bound, and a truncated report
  includes the total issue count and omitted count. Validation aggregates every
  implemented typed validator plus conservative Dwell and HRR continuity checks.
- Binary-angle values provide exact rational degrees and exact wire round trips.
  Constructing a new encoded angle from an arbitrary decimal degree value is not
  implemented until the standard's rounding boundary is covered explicitly.
- Dwell and Target Report structures are decoded losslessly, including every
  optional field selected by D1. Typed accessors cover core Dwell time/geometry
  and all Target Report values. Direct and reduced-resolution target positions
  are available through exact binary-angle arithmetic; malformed incomplete
  locations return no reconstructed position, while SA32 latitude overflow is
  rejected explicitly.
- `validate_dwell()` checks paired scale factors and target locations, mutually
  exclusive location encodings, Dwell field groups, radial/wrap velocity and
  truth-tag pairs, target-uncertainty preconditions, D1 spare bits, and
  mechanically verifiable Table 3-9/3-10 ranges. It cannot determine whether an
  omitted conditional uncertainty was available to the producer. Stream
  continuity validation is deliberately conservative and does not infer whether
  sensor-specific revisit resets are legitimate.
- Complete-packet decoding defaults to 65,535 bytes and 4,096 segments for
  resource safety. The byte bound is checked before copying caller input.
  Applications must explicitly configure different bounds.
- Public samples include independently generated Edition 4 packets, AFRL
  public-release Version 3.0 simulated-exercise streams, and a Wireshark issue
  attachment whose P7 value marks it as operation/real data. That attachment
  decodes to 193 reports associated with platform `C-FNRC`, but its radar,
  producer, acquisition-chain, and redistribution provenance are not stated.
  Real-system interoperability therefore remains promising but unproven.
- General earlier-edition conformance is not claimed. One opt-in packet-context
  profile covers only the exact Version 3.0 Job Definition-only P10 convention
  observed in Wireshark issue 19566, requiring J1 to match P10. All other
  Edition 3 behavior remains preservation-oriented and validated against the
  current profile unless explicitly documented.
- Job Definition fields preserve all raw enumeration and No Statement values,
  and mechanically decidable field ranges have structured validation. Bounding
  area convexity across the antimeridian is not validated yet. P10 is validated
  against Dwell/HRR presence, but cross-packet job lifecycle is not tracked yet.
- Processing History structure and flags round-trip exactly, but sequence-number,
  nonzero Job ID, reserved processing bits, and BCS character fields have structured
  validation. No public operational Processing History sample is available.
- Platform Location structure and exact Mission-relative event time are available,
  with structured checks for L1, altitude, and speed ranges. Its tests use an
  independent synthetic vector because no public operational type-13 capture has
  been located.
- Recommended Job Request and Job Acknowledge structures and mechanically
  decidable validation are implemented from Chapter 4. No operational tasking
  partner or public capture is available, so workflow-level acknowledgement,
  cancellation, authorization, and scheduling interoperability is unproven and
  intentionally remains application policy.
- Registered extension IDs 128-132 remain opaque. Annex L names Advanced Dwell,
  Advanced Job Definition, Advanced Platform Location, Target Centroid, and
  Releasability, but explicitly provides no payload descriptions in this edition.
- The package is not NATO-certified and makes no claim of complete STANAG 4607
  conformance.
