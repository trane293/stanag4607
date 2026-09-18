# AEDP-4607 Edition A Version 1 requirement trace

This trace records implemented, testable behavior derived from the February 2024
normative publication. It does not reproduce the standard and does not imply NATO
certification.

## Packet header increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| PH-001 | Section 3.1 and Table 3-1 | Every packet begins with the fixed 32-byte packet header containing P1 through P10 in table order and width. | `tests/test_packet_header.py` |
| PH-002 | Section 2.3; Annex C section C-4.1 | Multi-byte integer and flag fields use big-endian byte order. | `tests/test_packet_header.py` |
| PH-003 | Sections 3.1.1 and 3.1.2 | P1 is two bytes and P2 is the unsigned size of the entire packet, with a minimum of 32 bytes. | `tests/test_packet_header.py` |
| PH-004 | Table 3-1; sections 3.1.3 through 3.1.10 | P3 through P10 retain their exact fixed-width character or unsigned integral wire values. | `tests/test_packet_header.py` |
| PH-005 | Sections 3.1.4, 3.1.6, and 3.1.7 | Reserved classification, security-code, and exercise-indicator bit patterns remain lossless; semantic validation is separate from structural decoding. | `tests/test_packet_header.py` |

### Deliberate boundary

This increment only decodes and encodes a complete packet-header value. It does not
yet frame entire packets, enforce relationships between P10 and contained segments,
validate the BCS character repertoire, or claim support for any message segment.

## Complete packet and segment-header increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| FR-001 | Section 2.1; section 2.2 and Figure 2-1 | A packet consists of one packet header followed by zero or more length-delimited message segments. | `tests/test_packet_framing.py` |
| FR-002 | Section 3.2 and Table 3-6 | Every segment begins with a 5-byte header containing a one-byte type and four-byte big-endian size. | `tests/test_packet_framing.py` |
| FR-003 | Section 3.2.2 | Segment size includes its 5-byte header, may not be smaller than that header, and may not exceed the packet body. | `tests/test_packet_framing.py` |
| FR-004 | Section 3.1.2; implementation guide Annex G sections G.9.2-G.9.3 | Declared packet size must match the complete externally supplied packet, including all headers and segments. | `tests/test_packet_framing.py` |
| FR-005 | Section 3.2.1 and Table 3-6 | Reserved and extension segment type values remain skippable and losslessly available to applications. | `tests/test_packet_framing.py` |
| FR-006 | Library safety profile | The caller-configured packet-size bound is enforced against supplied input before the complete decoder materializes it. | `tests/test_packet_framing.py` |

### Safety profile

The default decoder accepts packets up to 65,535 bytes, matching the minimum
packet-size capability described for Common Core Requirements in implementation
guide Annex G. Callers may explicitly select a different bound. Segment count is
also caller-bounded so adversarial streams cannot create unbounded object graphs.

This increment frames complete in-memory packets only. Incremental stream buffering,
recovery after malformed input, and typed segment payloads remain separate work.

## Incremental packet stream increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| ST-001 | Section 2.1 | Consecutive packets can be separated using each packet's P2 size without relying on transport chunk boundaries. | `tests/test_stream.py` |
| ST-002 | Sections 2.1-2.2 | Arbitrarily fragmented input produces the same packets and exact wire bytes as complete input. | `tests/test_stream.py` |
| ST-003 | Section 3.1.2 | A declared packet size beyond the configured bound is rejected after the header and before buffering its body. | `tests/test_stream.py` |

The standard deliberately leaves physical transmission and error correction to lower
layers (section 2.2). Consequently, terminal truncation, parser failure, reset, and
buffer bounds are library safety contracts rather than NATO conformance claims.

## Mission Segment increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| MS-001 | Section 3.3 and Table 3-7 | A Mission Segment body contains M1-M7 in a fixed 39-byte layout. | `tests/test_mission.py` |
| MS-002 | Sections 3.3.1-3.3.4 | Mission plan, flight plan, and platform configuration retain their exact fixed-width BCS wire bytes; platform type remains an unsigned enumeration value. | `tests/test_mission.py` |
| MS-003 | Sections 3.3.5-3.3.7 | Reference year, month, and day remain distinct integer fields and month/day obey their table ranges. | `tests/test_mission.py` |

## Binary angle primitives

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| AN-001 | Annex C section C-4.6 and Table C-6 | BA16 and BA32 are unsigned integers scaled by exactly 360 / 2^n degrees. | `tests/test_angles.py` |
| AN-002 | Annex C section C-4.7 and Table C-7 | SA16 and SA32 are signed two's-complement integers scaled by exactly 180 / 2^n degrees. | `tests/test_angles.py` |
| AN-003 | Annex C worked examples | BA16 bits `0101100100011100` decode to 125.31005859375 degrees and SA16 bits `1100111001100110` decode to -34.8760986328125 degrees. | `tests/test_angles.py` |

## Dwell existence mask increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| DM-001 | Section 3.4.1 and Figure 3-1 | D1 is an 8-byte high-order-byte-first mask mapping bit 63 to D2 through bit 16 to D32.18. | `tests/test_dwell_mask.py` |
| DM-002 | Table 3-9 and Figure 3-1 | D2-D9 and D24-D27 are mandatory and their absence is mechanically reportable. | `tests/test_dwell_mask.py` |
| DM-003 | Section 3.4.1 Figure 3-2 | Prefix `FF3F` denotes D2-D9 and D12-D17, excluding D10-D11. | `tests/test_dwell_mask.py` |
| DM-004 | Tables 3-9 and 3-10 | The mask deterministically computes the encoded Dwell-body and per-target widths. | `tests/test_dwell_mask.py` |
| DM-005 | Section 3.4.1 | Sixteen spare low-order bits are retained exactly even though conforming producers set them to zero. | `tests/test_dwell_mask.py` |

## Dwell and Target Report structural increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| DW-001 | Table 3-9 | Present D2-D31 values are consumed in field order using their exact specified widths. | `tests/test_dwell.py` |
| DW-002 | Section 3.4.1; Table 3-10 | Each of D5 Target Reports repeats the D32 fields selected by D1, in field order and exact width. | `tests/test_dwell.py` |
| DW-003 | Section 3.4.1 exception | When D5 is zero, D32 mask bits consume no bytes and produce no target reports. | `tests/test_dwell.py` |
| DW-004 | Sections 3.4.2-3.4.9 and 3.4.24-3.4.27 | Core indices, flags, count, milliseconds, signed altitude, coordinates, and dwell extents are exposed without losing encoded values. | `tests/test_dwell.py` |
| DW-005 | Tables 3-9 and 3-10 | Truncation, trailing data, absent mandatory fields, zero-width target records, and excessive target counts are rejected deterministically. | `tests/test_dwell.py` |
| DW-006 | Table 3-10; sections 3.4.32.1-3.4.32.18 | Every selected Target Report value is exposed with its specified signedness and unit, including exact half-decibel radar cross section, while absence remains distinguishable from a zero value. | `tests/test_dwell.py` |
| DW-007 | Sections 3.4.10-3.4.11 and 3.4.32.2-3.4.32.5; AEDP-4607.1 Annex E section E.7 | Direct coordinates remain exact BA32/SA32 values; reduced coordinates are reconstructed from D10/D11, D24/D25, and D32.4/D32.5 using exact raw integer arithmetic and modulo-2^32 longitude wrap. | `tests/test_dwell.py` |
| DW-008 | Table 3-9; sections 3.4.10-3.4.31 | Every optional Dwell value is exposed with the specified signedness, unit, and binary-angle form while absence remains distinct from an encoded zero. | `tests/test_dwell.py` |

## Dwell conformance validation increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| DV-001 | Section 3.4.1 | The sixteen spare bits in D1 must be zero. | `tests/test_dwell_validation.py` |
| DV-002 | Sections 3.4.10-3.4.23 | D10-D11, D12-D14, D15-D17, D18-D20, and D21-D23 obey their specified all-or-none presence groups. | `tests/test_dwell_validation.py` |
| DV-003 | Sections 3.4.10-3.4.11 and 3.4.32.2-3.4.32.5 | High-resolution target coordinates are paired and mutually exclusive with paired reduced-resolution coordinates; D10/D11 are present if and only if reduced coordinates are present. | `tests/test_dwell_validation.py` |
| DV-004 | Sections 3.4.32.7-3.4.32.8 and 3.4.32.16-3.4.32.17 | Radial/wrap velocity and truth-tag application/entity fields are sent in pairs. | `tests/test_dwell_validation.py` |
| DV-005 | Table 3-10; section 3.4.32.11 | Target classification probability is between 0 and 100 percent. | `tests/test_dwell_validation.py` |
| DV-006 | Table 3-9 | Dwell time, altitude, sensor position uncertainty, speed, track uncertainty, and constrained attitude fields obey the numeric ranges not already guaranteed by their wire types. | `tests/test_dwell_validation.py` |
| DV-007 | Table 3-10; sections 3.4.32.12-3.4.32.15 | Target uncertainties require D12-D14; height uncertainty additionally requires D32.6; radial-velocity uncertainty additionally requires D32.7; mechanically bounded height and velocity-uncertainty values obey their ranges. | `tests/test_dwell_validation.py` |

Validation reports structured issues and leaves the losslessly decoded value intact.
Producer-side availability, stream continuity, and packet-context rules are outside
this increment.

## Job Definition Segment increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| JD-001 | Section 3.7 and Table 3-14 | A Job Definition Segment contains mandatory J1-J28 in one fixed 68-byte payload. | `tests/test_job_definition.py` |
| JD-002 | Sections 3.7.6-3.7.13 | The four clockwise bounding-area points retain exact alternating SA32 latitude and BA32 longitude values. | `tests/test_job_definition.py` |
| JD-003 | Sections 3.7.15-3.7.26 and Table 3-14 | Nominal values expose specified units while preserving each exact encoded value and distinguishing No Statement sentinels. | `tests/test_job_definition.py` |
| JD-004 | Sections 3.7.1-3.7.5, 3.7.14, and 3.7.27-3.7.28 | Job, sensor, filtering, priority, radar-mode, terrain-model, and geoid-model values remain available without discarding reserved enumerations. | `tests/test_job_definition.py` |

## Job Definition validation increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| JV-001 | Sections 3.7.1, 3.7.4-3.7.5; Table 3-14 | J1 is nonzero, J4 reserved bits are zero, and J5 is 1-99 or the End of Job value 255. | `tests/test_job_validation.py` |
| JV-002 | Sections 3.7.16-3.7.19, 3.7.23, and 3.7.25; Table 3-14 | Nominal uncertainty and probability fields obey their stated maxima while exact No Statement sentinels remain valid. | `tests/test_job_validation.py` |

## Packet Job ID context increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| PV-001 | Section 3.1.10 | P10 is nonzero when Dwell or HRR segments are present and zero when neither segment type is present. | `tests/test_packet_validation.py` |
| PV-002 | Non-normative Wireshark issue 19566 interoperability evidence | The opt-in Version 3.0 Job Definition profile suppresses PV-001 only for one type-5-only packet whose J1 equals its nonzero P10; the Edition A default and every other tested packet shape remain strict. | `tests/test_packet_validation.py` |

## Typed application event increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| EV-001 | Sections 2.1-2.2 and Table 3-6 | Segments are surfaced in packet wire order and dispatched according to S1 without altering unsupported payloads. | `tests/test_events.py` |

`SegmentEvent` packet-header and segment-index provenance is an application API
contract rather than a NATO conformance claim.

## Contextual stream increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| CT-001 | Section 3.3; sections 3.3.5-3.3.7 and 3.4.6 | D6 is resolved from midnight UTC on M5-M7 using exact millisecond arithmetic only when a valid Mission date is available for the packet's platform and mission. | `tests/test_context_stream.py` |
| CT-002 | Sections 3.1.8-3.1.10 and 3.7.1 | Mission and Job context is keyed by the exact P8/P9 identifiers and J1/P10 job identity rather than an invented cross-sensor entity. | `tests/test_context_stream.py` |
| CT-003 | Application safety/provenance contract | Mission and Job insertions are identified as new, repeat, or replacement operations; the previous value and any deterministic LRU eviction key remain available on the triggering event. | `tests/test_context_stream.py` |
| CT-004 | Application safety/provenance contract | Invalid Mission dates and unrepresentable Mission-relative event-time arithmetic return no absolute time and an explicit structured diagnostic without discarding valid decoder context. | `tests/test_context_stream.py` |

Cache limits, lifecycle/eviction updates, packet indexes, reset behavior, and
preservation of an unknown absolute time are application safety/provenance contracts
rather than NATO conformance claims.

GeoJSON export is also an application adapter, not a STANAG 4607 wire-conformance
claim. Its tests prove that direct and reduced target coordinates reach a common
visualization form while retaining raw integer coordinates and their encoding mode.

The inspect, validate, and GeoJSON command-line workflows are likewise application
contracts. Their integration tests use an attributed public Edition 4 sample and
exercise the same bounded decoders and structured validators as the Python API.
Validation continues counting findings across the complete stream while retaining
only the caller-configured maximum number in its JSON report; this is a resource
safety contract rather than a wire-format requirement.

## Processing History Segment increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| PR-001 | Section 3.14 and Table 3-21 | C1 declares 1-255 fixed Processing Records after the 21-byte original-dataset identity, and payload size agrees exactly with that count. | `tests/test_processing_history.py` |
| PR-002 | Section 3.14.6 and Table 3-22 | Each C6 record is 23 bytes and preserves its ordered sequence, modifying-system identity, mission/job IDs, and processing flags. | `tests/test_processing_history.py` |

## Platform Location Segment increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| PL-001 | Section 3.15 and Table 3-24 | A Platform Location Segment contains L1-L7 in a fixed 23-byte layout with exact integer and binary-angle forms. | `tests/test_platform_location.py` |
| PL-002 | Sections 3.15.1-3.15.7 | Location time, WGS 84 ellipsoid position/altitude, track, speed, and vertical velocity expose their stated units without losing encoded values. | `tests/test_platform_location.py` |
| PL-003 | Sections 3.3.5-3.3.7 and 3.15.1 | L1 resolves from midnight UTC on the applicable Mission date using exact millisecond arithmetic, and remains unresolved without valid context. | `tests/test_context_stream.py` |

## Practical optional-segment validation increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| OV-001 | Sections 3.14.5-3.14.6 and Tables 3-21 through 3-23 | Original/modifying Job IDs are nonzero, record sequence numbers count from one in order, and reserved C6.6 bits are zero. | `tests/test_optional_segment_validation.py` |
| OV-002 | Table 3-24 | L1, L4, and L6 obey the semantic ranges not guaranteed by their encoded integer forms. | `tests/test_optional_segment_validation.py` |

## Conservative stream continuity increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| SC-001 | Sections 3.4.2-3.4.4 | D3 counts sequentially within a revisit (including its allowed wrap), a changed revisit begins at D3=0, and no additional Dwell follows D4=1 within the same revisit. | `tests/test_continuity.py` |
| SC-002 | Sections 3.5.2-3.5.4 | H3 counts sequentially within an HRR revisit (including its allowed wrap), a changed revisit begins at H3=0, and no additional HRR Dwell follows H4=1 within that revisit. Type-2 and type-3 sequences for the same job are independent. | `tests/test_continuity.py` |

The bounded per-job state and decision not to diagnose D2 resets are application
safety policies. Section 3.4.2 and AEDP-4607.1 Annex F explicitly make reset and
revisit interpretation dependent on whether an area is actually being revisited and
on sensor-specific behavior.

## Test and Status Segment increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| TS-001 | Section 3.12 and Table 3-20 | A Test and Status Segment contains T1-T6 in a fixed 14-byte layout; T5 bits 7-3 identify hardware failures, T6 bits 7-4 identify exceeded operational limits, and spare bits are zero. | `tests/test_test_status.py` |
| TS-002 | Sections 3.3.5-3.3.7 and 3.12.4 | T4 resolves from midnight UTC on the applicable Mission date using exact millisecond arithmetic, and remains an exact raw value independently of validation. | `tests/test_context_stream.py`, `tests/test_test_status.py` |

Table 3-20 prints T2/T3 as 1-65535 while AEDP-4607.1 Annex G requires their
first generated values to be zero and prints hexadecimal ranges beginning at zero.
The codec therefore preserves the full unsigned 16-bit domain and does not report
zero as invalid. This is an explicit resolution of contradictory source text, not a
claim that both statements can simultaneously constrain the wire value.

## Recommended Chapter 4 tasking segments

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| JR-001 | Chapter 4; section 4.1 and Table 4-1 | Type 101 contains mandatory R1-R26 in an exact 79-byte layout, including exact request identity, four SA32/BA32 points, requirements, UTC start components, timing, sensor identity, and request flag. | `tests/test_tasking.py` |
| JR-002 | Sections 4.1.1-4.1.25 and Table 4-1 | R1/R2/R25 use BCS; R3, R15-R20, and R26 obey mechanically decidable ranges while leap second 60 remains representable. | `tests/test_tasking_validation.py` |
| JA-001 | Chapter 4; section 4.2 and Table 4-2 | Type 102 contains mandatory A1-A25 in an exact 79-byte layout, including Job ID, correlated request identity, sensor/job parameters, four SA32/BA32 points, status, UTC start components, and nationality. | `tests/test_tasking.py` |
| JA-002 | Sections 4.2.1-4.2.25 and Table 4-2 | A2/A3/A5/A25 use BCS; A1, A6, A18, and A19-A24 obey mechanically decidable ranges while leap second 60 remains representable. | `tests/test_tasking_validation.py`, `tests/test_cli.py` |
| JA-003 | Sections 4.1.14-4.1.19 and 4.2.19-4.2.24 | Valid non-leap-second components expose timezone-aware UTC datetimes; leap-second 60 remains exact in the raw component tuple rather than being coerced into Python's datetime range, and impossible calendar dates are diagnosed. | `tests/test_tasking.py`, `tests/test_tasking_validation.py` |

Chapter 4 defines these segments as recommended rather than mandatory. The tests
establish structural and local semantic behavior only; scheduling, authorization,
request correlation policy, and partner interoperability are not inferred.

Annex L registers extension segment identifiers 128-132 but marks their payload
descriptions “TO BE PROVIDED.” Those identifiers therefore remain lossless opaque
segments until an authoritative layout is available.

## Free Text Segment increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| FT-001 | Section 3.8 and Table 3-19 | A Free Text Segment contains exact 10-byte F1 and F2 identities followed by 1-65515 bytes of F3 text in a payload of 21-65535 bytes. | `tests/test_free_text.py` |
| FT-002 | Annex A; AEDP-4607.1 Annex G section G.9.8 | F1-F3 contain only BCS bytes and no generated field consists entirely of spaces; diagnostics do not alter received bytes. | `tests/test_free_text.py`, `tests/test_cli.py` |

## Character validation increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| CV-001 | Section 2.3 and Annex A | Implemented alphanumeric packet, Mission, Job Definition, and Processing History fields contain only BCS codes 0x20-0x7E plus LF, FF, and CR; validation preserves exact received bytes. | `tests/test_character_validation.py`, `tests/test_cli.py` |

## HRR Existence Mask increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| HM-001 | Section 3.5.1 and Figure 3-4 | H1 is a five-byte high-order-byte-first mask mapping bits 39-10 to H2-H31, bits 9-6 to H32.1-H32.4, and retaining six low-order spare bits. | `tests/test_hrr_mask.py` |
| HM-002 | Figure 3-4 and Table 3-12 | Mandatory H2-H4, H8, H10-H14, H16-H19, H23-H26, and H32.1 mask bits are mechanically reportable and selected fixed fields determine the pre-scatterer byte count. | `tests/test_hrr_mask.py` |

## Signed binary-decimal increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| BD-001 | Annex C section C-4.5 and Table C-5 | B16/B32 values use sign magnitude, eight integer bits, and respectively seven or 23 fractional bits while preserving the exact sign bit, including negative zero. | `tests/test_binary_decimals.py` |
| BD-002 | Section 3.5 and Annex C section C-4.5 | H32 uses sign magnitude with 15 integer and 16 fractional bits and round-trips every exact encoded value. | `tests/test_binary_decimals.py` |

## HRR fixed-metadata increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| HR-001 | Section 3.5 and Table 3-12 | Every H1-selected H2-H31 field is consumed in wire order at its exact width and re-encoded without changing H32 bytes. | `tests/test_hrr.py` |
| HR-002 | Sections 3.5.2-3.5.31 and Annex C section C-4.5 | Indices, counts, flags, quarter-decibel quantities, B16/B32/H32 values, origins, types, masks, byte widths, extents, and electrical lengths expose exact values and stated units while optional absence remains distinct from zero. | `tests/test_hrr.py` |
| HR-003 | Library safety profile | Direct HRR decoding checks a caller-configured H32 byte bound before copying the scatterer region. | `tests/test_hrr.py` |
| HR-004 | Sections 3.5.25-3.5.26 and 3.5.32; Table 3-13 | For H16=0, H32 records expose exact one/two-byte magnitude, optional one/two-byte phase, and mask-selected I16 range/Doppler indices; every record re-encodes byte-identically. | `tests/test_hrr.py` |
| HR-005 | Sections 3.5.7 and 3.5.32 | Uncompressed H32 bytes contain only complete records, and H7 equals the total record count for sparse H23=3 data. Diagnostics preserve received bytes. | `tests/test_hrr_validation.py` |

Table 3-13 prints one byte for H32.3/H32.4 while declaring both fields I16 with a
0-65535 range. Two-byte decoding is the only interpretation compatible with the
declared form and range. H16=1 threshold decomposition remains opaque: the edition
names the technique but does not define a complete decompression wire algorithm.
The independent synthetic sample also uses identical H6/H8/H23 metadata with two
different record counts, so it is not used to invent universal count semantics.

## HRR fixed-metadata validation increment

| Trace ID | Normative source | Software-verifiable requirement | Evidence |
|---|---|---|---|
| HV-001 | Sections 3.5.4-3.5.9, 3.5.15, 3.5.21-3.5.23, and Table G-6 | H4 is binary; H6 or H7 is present; H5, H9, H15, H21, H22, and sparse indices obey their H23 data-type conditions. | `tests/test_hrr_validation.py` |
| HV-002 | Sections 3.5.11-3.5.19, 3.5.22-3.5.26, 3.5.30-3.5.31 | Exact decimal values, compression/weighting/data-type enumerations, processing-mask spare bits, magnitude/phase byte widths, and electrical lengths obey their mechanically decidable ranges. | `tests/test_hrr_validation.py` |
| HV-003 | Sections 3.5.26 and 3.5.32.2 | H32.2 is selected exactly when H26 declares one or two phase bytes. | `tests/test_hrr_validation.py` |
