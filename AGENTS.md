# Agent development instructions

These instructions apply to the entire repository. Read this file before making
changes, then read the documents linked under **Required context**.

## Objective

Build a standards-accurate, production-quality, pure-Python toolkit for
contemporary STANAG 4607 Ground Moving Target Indicator (GMTI) data. This is a
separate project from `stanag4609`; reuse its engineering lessons and public
design principles, but do not couple the packages or copy FMV-specific code.

Prioritize correctness, interoperability, bounded live processing, clear
evidence, and useful developer workflows over feature count. Do not chase
archaic, obscure, unavailable, or untestable profiles merely to increase
claimed coverage. Add support when authoritative text, credible current usage,
and representative tests justify it. Record unsupported or externally owned
behavior honestly rather than guessing.

STANAG 4607 is a GMTI data standard. It is not the Automatic Identification
System (AIS) maritime standard. Do not add AIS behavior under this package name.

The repository has an implemented, evidence-backed Edition 4 / AEDP-4607
Edition A Version 1 profile. Do not extend its support claims without an
authoritative specification, an explicit requirement trace, and executable
conformance evidence. General historical-edition conformance and operational
radar interoperability are not claimed.

## Required context

Before changing code, read the relevant portions of:

- `docs/ROADMAP.md` for current priorities and the handoff state;
- `docs/DEVELOPMENT.md` for the goal-seeking TDD method;
- `docs/CONFORMANCE.md` for standards-support claims;
- `references/standards/manifest.json` and the relevant edition-specific trace
  under `docs/requirements/` for standards provenance;
- `docs/LIMITATIONS.md` and `docs/PRODUCTION_READINESS.md` for explicit non-claims;
- `docs/ARCHITECTURE.md` for the public protocol/private fusion boundary;
- `docs/API_STABILITY.md` and `CONTRIBUTING.md` for compatibility and review; and
- `docs/RELEASING.md` before changing versions, tags, or distributions.

When changing implemented protocol behavior, update the requirement trace,
conformance matrix, limitations, and public API docs in the same increment as
appropriate. Never claim certification or full support without auditable
evidence for the stated profile.

## TDD is mandatory

Always use test-driven development for behavioral changes:

1. Identify the exact requirement, defect, or user-visible outcome. For
   protocol behavior, cite the authoritative edition and requirement, section,
   table, or official vector.
2. Write the smallest failing test and run it to confirm the intended failure.
3. Implement the smallest coherent behavior that makes the test pass.
4. Add boundary, malformed-input, lossless round-trip, arbitrary-chunk, and
   resource-limit tests wherever applicable.
5. Run focused tests during development, then the full quality gates before
   committing.

Do not implement protocol behavior first and add tests afterward. Documentation,
comment-only changes, release metadata refreshes, and repair of a broken test
harness are the only ordinary exceptions; explain the exception in the commit
or pull-request description.

Third-party implementations can expose interoperability questions, but are never
normative sources and must not be copied.

## Goal-seeking development cycle

Development proceeds as a persistent sequence of small, evidence-backed goals,
using the detailed method in `docs/DEVELOPMENT.md`. For each goal:

1. Re-read the roadmap, current support claims, limitations, and relevant
   standards evidence.
2. Choose the highest-value unresolved outcome that is practical, testable, and
   supported by authoritative text or representative data.
3. Define its acceptance evidence and stopping boundary before implementation.
4. Follow the mandatory red-green-refactor TDD cycle above.
5. Run focused and repository-wide quality gates, then review correctness,
   security, resource bounds, compatibility, and documentation.
6. Make one clean commit and update the roadmap or evidence ledger.
7. Reassess the next goal from the new state rather than following a stale task
   list mechanically.

Continue this cycle autonomously while useful, in-scope, evidence-backed work
remains. Stop and record the blocker when progress would require unavailable
standards, missing representative data, a material product decision, expanded
authority, or speculative work without credible demand.

## Fusion-ready boundary

This library will be an open-source standards implementation beneath a separate
sensor-fusion product. Read `docs/ARCHITECTURE.md` before designing public
models or event APIs.

Make the library **fusion-ready, not fusion-aware**. Its public values and
events must retain the standard-defined facts a downstream adapter needs:

- exact observation and report times, their clock domains, precision, and
  provenance, without floating-point loss;
- reception time only when supplied by the caller, kept distinct from event
  time;
- coordinate reference system, datum, altitude reference, units, and special
  or unavailable values;
- standard-provided accuracy, uncertainty, covariance, quality, and validity;
- mission, platform, sensor, stream, packet, dwell, report, and target identity;
- sequence, continuity, omission, reset, and discontinuity state; and
- a lossless reference to original values and unknown data.

Do not implement a universal cross-sensor `Observation` model in this package
without an explicit product decision. Expose standard-specific typed values and
stable bounded event/adapter boundaries instead.

The following belong outside this repository and must not leak into the public
protocol API: cross-sensor association, identity resolution, clock-offset
estimation, fusion windows, track fusion, trust scoring, classification
reconciliation, duplicate suppression, prediction, threat scoring, operational
ontology, storage/query models, and customer-specific policy. Those are owned by
private middleware consuming this package and `stanag4609` through adapters.

## Engineering invariants

- Keep the core pure Python with no mandatory runtime dependencies. Codec, GIS,
  visualization, and transport runtimes belong behind optional extras or
  adapters.
- Treat every input byte as untrusted and bound lengths, counts, buffers, and
  incremental parser state, retained histories, and recovery work.
- Preserve unknown or reserved wire data losslessly when safe; strict validation
  must be explicit.
- Separate framing, packet models, segment codecs, validation, streaming state,
  and application adapters.
- Keep standard-specific semantics intact instead of normalizing away time,
  geometry, uncertainty, identity, or provenance needed by downstream fusion.
- Use immutable typed values for decoded public models unless mutation is a
  deliberate builder operation.
- Define truncation, discontinuity, backpressure, malformed input, and terminal
  `finish()` behavior for live APIs. Keep event time distinct from receive and
  processing time.
- Preserve exact time, geometry, uncertainty, identity, metadata, and unknown
  bytes through applicable round trips. Avoid speculative abstractions: prefer
  a small typed API backed by an end-to-end workflow.
- Preserve pre-1.0 API compatibility according to `docs/API_STABILITY.md` and
  deliberately document public export changes.
- Keep standards documents and large datasets out of Git unless redistribution
  rights are confirmed; record identity and provenance in manifests.
- State full, partial, experimental, and planned support honestly. Never imply
  NATO certification.

## Required evidence before implementation

Before implementing a protocol slice:

1. Obtain the exact authoritative STANAG 4607 edition and amendments.
2. Record its source, publication metadata, local filename, and SHA-256 in
   `references/standards/manifest.json`.
3. Establish whether the text may be redistributed; local presence does not
   imply permission to commit it.
4. Create an edition-specific requirement trace under `docs/requirements/`.
5. Identify official vectors or representative, lawfully usable GMTI data.
6. Define the narrow practical profile and its explicit non-claims.
7. Define how decoded events expose fusion-relevant standard facts without
   importing private fusion policy or a cross-sensor domain model.

## Quality gates

Run these before committing behavior:

```console
ruff check .
mypy src
pytest --cov=stanag4607 --cov-branch --cov-report=term-missing
python -m build
python -m twine check dist/*
```

The repository-wide branch-coverage floor is 90%. Protocol parsers, encoders,
validators, and state machines should exceed that floor with focused tests.

## Change discipline

- Use small, reviewable Conventional Commits.
- Use the branch and pull-request conventions in `CONTRIBUTING.md`.
- Do not combine protocol behavior, unrelated cleanup, and generated artifacts
  in one increment.
- Never weaken a test, bound, validator, or claim to make a gate pass.
- Leave the worktree clean when stopping.
- Record open questions and stopping points in `docs/ROADMAP.md`.

## Practical stopping rule

Stop expanding and document the boundary when remaining work lacks an
authoritative accessible specification, representative data, credible current
demand, or software-verifiable behavior; belongs in an optional adapter or
deployment; or needs a real design partner. A smaller evidence-backed profile
is preferable to broad but unreliable nominal support.
