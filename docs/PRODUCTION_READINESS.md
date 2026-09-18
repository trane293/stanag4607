# Production readiness

## Current assessment

The library has production-quality engineering for its documented Edition 4 /
AEDP-4607 Edition A Version 1 profile, but operational deployment readiness is
not yet demonstrated. The distinction matters: synthetic interoperability can
prove deterministic wire behavior, bounds, and validation, but it cannot prove
compatibility with a particular radar producer or mission system.

## Completed evidence

- Every segment with a defined payload in the normative edition has a typed,
  lossless codec; undefined, reserved, and undocumented extension payloads remain
  safely opaque.
- Complete and incremental parsing is fail-closed and caller-bounded for packet
  bytes, segment counts, target counts, HRR bytes, and retained stream context.
- Validation is non-destructive and separates wire preservation from operational
  acceptance policy.
- Exact time components, binary angles, uncertainty, identity, sequence state,
  and original values remain available to private downstream adapters.
- The dependency-free core is strictly typed and exercised across supported Python
  versions in a least-privilege, commit-pinned CI workflow.
- Public synthetic Edition 4 packets are provenance-pinned and round-trip exactly;
  independently derived vectors cover the two recommended Chapter 4 segments.
- Local Version 3.0 evidence now includes the AFRL public-release Ten Targets
  exercise profiles plus a matching raw-stream/UDP capture pair submitted to
  Wireshark. The latter marks itself operation/real but lacks authenticated radar
  and producer provenance.
- Packaging, clean installation, CLI workflows, local visualization, documentation,
  and credential/history checks are part of the release audit.

## Evidence still required before field deployment

1. Validate against captures from the intended operational radar or simulator and
   record producer/version/profile provenance.
2. Confirm partner amendments, controlled extensions, expected packet-size limits,
   throughput, transport, and recovery policy.
3. Run soak/load tests against those representative rates and deployment resource
   budgets. Synthetic microbenchmarks alone are not a substitute.
4. Exercise corruption, truncation, reordering, restart, and continuity behavior at
   the actual transport boundary chosen by the product.
5. Perform a deployment threat model and security review of the surrounding network,
   storage, authentication, authorization, and observability components.
6. Obtain an authoritative algorithm or partner vectors before interpreting H16=1
   threshold-decomposition payloads; they remain bounded and lossless meanwhile.

## Deployment rule

Treat the package as ready for application integration and controlled evaluation.
Call a specific deployment production-ready only after its items above have evidence.
Do not weaken preservation, bounds, or diagnostics to accommodate a producer;
document the producer profile and add a failing interoperability test first.
