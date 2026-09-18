# Goal-seeking, test-driven development method

This project uses the same evidence-led development cycle proven in the sibling
`stanag4609` library. A roadmap supplies direction, but executable evidence and
current project state determine each increment.

## The cycle

### 1. Orient

Read `AGENTS.md`, this guide, `docs/ROADMAP.md`, the standards manifest, existing
requirement traces, support claims, limitations, and `docs/ARCHITECTURE.md`.
Inspect the current tests and public API before choosing work.

### 2. Select one practical goal

Choose the smallest high-value outcome that improves a credible GMTI workflow.
It must have:

- an authoritative standard edition and normative basis;
- software-verifiable acceptance criteria;
- representative or directly derived test data;
- a bounded implementation surface; and
- a clear reason a contemporary user needs it.

Do not select work merely because a segment, field, edition, or integration
exists. Prefer capabilities that unlock actual parsing, validation, generation,
streaming, conversion, simulation, or application integration.

### 3. Define proof and boundaries

Before implementation, record:

- the exact behavior and public outcome;
- requirement, section, table, or official-vector citations;
- valid, boundary, malformed, and truncated cases;
- arbitrary input chunking and resource bounds where streaming applies;
- lossless preservation and round-trip expectations;
- compatibility and error behavior; and
- what the increment deliberately does not claim; and
- how standard-defined time, geometry, uncertainty, identity, provenance, and
  stream state remain available to a private fusion adapter without introducing
  fusion policy into the library.

### 4. Red

Write the smallest test proving the missing behavior. Run it and confirm it
fails for the intended reason. A syntax error, missing fixture, unrelated
failure, or incorrectly configured environment is not a valid red test.

### 5. Green

Implement the smallest coherent, typed, bounded behavior that satisfies the
test. Do not add speculative abstractions or adjacent standard coverage.

### 6. Refactor and harden

Keep the tests green while improving names and structure. Add applicable tests
for malformed lengths and counts, numeric limits, truncation, unknown data,
arbitrary chunks, parser finalization, reset/recovery, and exact re-encoding.

### 7. Verify and review

Run focused tests throughout development, then every quality gate in
`AGENTS.md`. Review the diff for:

- disagreement with the normative text;
- accidental unbounded memory, CPU, recursion, or latency;
- misleading conformance language;
- loss of unknown wire data;
- API or wire compatibility changes;
- hidden optional dependencies;
- copied third-party behavior or restricted material;
- documentation that no longer matches executable behavior; and
- accidental cross-sensor policy or coupling that violates the private fusion
  boundary.

### 8. Record one clean increment

Update the requirement trace, support matrix, limitations, API documentation,
and roadmap as applicable. Commit one independently understandable and
reversible change using Conventional Commits.

### 9. Reassess

Evaluate the project again from its new state. Continue with the next practical,
evidence-backed gap while the active goal remains achievable. Do not blindly
execute an old checklist when new evidence changes priorities.

## Stopping conditions

Pause and document the exact restart point when further progress requires:

- an unavailable or ambiguous authoritative specification;
- representative data that does not exist or cannot lawfully be used;
- a product or interoperability choice only the project owner can make;
- credentials, publication, external writes, or broader authority;
- a real integration partner for behavior that cannot be validated locally; or
- speculative, archaic, or negligible-demand work.

Stopping at an honest boundary is part of the method. It prevents nominal
coverage from replacing correctness.

## Definition of done for a protocol increment

An increment is done only when the normative basis is traceable, the test was
observed failing before implementation, the implementation and all applicable
boundary tests pass, complete quality gates pass, public claims remain precise,
the fusion-readiness contract in `docs/ARCHITECTURE.md` is satisfied where
applicable, and the repository contains a clean commit and updated continuation
state.
