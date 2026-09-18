# Architecture and private fusion boundary

## Decision

`stanag4607` is an independent open-source protocol library. It will accurately
decode, validate, preserve, encode, and stream contemporary STANAG 4607 GMTI
data. It must expose enough standard-defined fidelity for downstream correlation
with STANAG 4609 FMV and future sensor libraries, but it does not perform
cross-sensor fusion.

The governing rule is:

> Make the standards library fusion-ready, not fusion-aware.

This preserves the library's usefulness and interoperability while keeping the
product's cross-sensor reasoning, operational model, and accumulated integration
knowledge in private middleware.

## Intended system boundary

```text
STANAG 4609 bytes -> stanag4609 -> private 4609 adapter --+
                                                         |
STANAG 4607 bytes -> stanag4607 -> private 4607 adapter --+-> private fusion platform
                                                         |
future sensor bytes -> open protocol library -> adapter -+
```

The open libraries own wire truth. Private adapters translate standard-specific
events into the product's internal canonical observation model. The private
platform owns association and meaning across sources.

Neither open library should depend on the private model, on another sensor
library, or on a shared abstraction created prematurely. If a small public
interchange protocol is later justified by multiple implemented adapters, make
that a separately reviewed package rather than placing it inside one standard's
namespace.

## Open-source responsibilities

The STANAG 4607 library owns:

- exact, bounded packet and segment framing;
- typed standard-specific values;
- canonical encoding and lossless preservation;
- strict and preservation-oriented validation modes;
- incremental streams with explicit limits and lifecycle behavior;
- exact time values and their standard-defined clock semantics;
- geometry with datum, coordinate system, altitude reference, and units;
- accuracy, uncertainty, covariance, quality, and validity fields;
- source, mission, platform, sensor, dwell, report, and target identifiers;
- sequence, omission, continuity, reset, and discontinuity evidence;
- raw-value provenance and unknown extensions; and
- stable hooks through which an application adapter consumes events.

These are protocol-correctness requirements. They are valuable independently of
the private product and should be tested from authoritative standards.

## Private middleware responsibilities

The private product owns:

- its canonical cross-sensor observation and track schema;
- clock-offset estimation and temporal alignment policy;
- spatial transformations chosen for operational analysis;
- measurement-to-track, track-to-track, and cross-sensor association;
- target identity resolution and duplicate suppression;
- confidence, reliability, and source-trust scoring;
- classification and ontology reconciliation;
- fused track lifecycle, prediction, and intent or threat assessment;
- customer-specific rules, thresholds, and workflows;
- persistence, indexing, query, tenancy, authorization, and audit; and
- evaluation data, performance tuning, deployment, and integrations.

Do not add these behaviors to `stanag4607` for convenience. An example may show
how to consume a standard-specific event, but it must not become a reference
fusion algorithm or expose the private product schema.

## Fusion-readiness contract

Every public decoded model or event should be reviewed against the following
questions when the normative standard supplies the underlying fact:

1. Can a consumer recover the exact source time without floating-point loss?
2. Is the clock domain and timestamp provenance explicit?
3. Are event time and caller-observed reception time distinguishable?
4. Are coordinates inseparable from datum, units, altitude reference, validity,
   and unavailable/special-value state?
5. Are accuracy, uncertainty, covariance, and quality retained rather than
   flattened into a nominal position?
6. Are all relevant source and report identifiers available without inventing a
   cross-sensor entity ID?
7. Can a consumer detect sequence gaps, omissions, resets, and discontinuities?
8. Can unknown extensions and original encoded values survive a round trip?
9. Can events be consumed incrementally with bounded memory and explicit
   finalization/recovery behavior?
10. Is the API free of fusion windows, matching thresholds, confidence policy,
    operational ontology, or other product-owned decisions?

Failing one of these checks becomes part of the acceptance criteria for the
protocol increment that introduces the affected model.

## Relationship with `stanag4609`

The libraries should share principles, not runtime coupling. They may use
similar conventions for immutable models, exact time, bounded iterators,
preservation modes, issues, and lifecycle methods where those conventions fit
both standards. They must not force GMTI reports and FMV metadata into the same
type hierarchy.

Correlation belongs in private adapters because the two standards express time,
sensor state, observations, and identity differently. Keeping those differences
visible prevents a convenient public abstraction from silently destroying the
information required for correct fusion later.

## Deferred decision: common interchange package

Do not create a shared `sensor-core` package now. Reconsider only after at least
two standards libraries and their private adapters exist and repeated,
semantically identical primitives are demonstrated. At that point, extract only
stable mechanics that do not reveal or constrain fusion policy. Until then,
duplication of a few small exact-value primitives is safer than premature
cross-standard coupling.

