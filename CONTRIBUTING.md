# Contributing

Contributions are welcome when they improve a practical, evidence-backed STANAG
4607 workflow. Read `AGENTS.md`, `docs/DEVELOPMENT.md`, `docs/CONFORMANCE.md`, and
`docs/LIMITATIONS.md` before changing protocol behavior.

## Development setup

```console
pyenv install --skip-existing 3.10.13
pyenv local 3.10.13
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## Branches and commits

Use a short branch named `feat/<topic>`, `fix/<topic>`, `docs/<topic>`, or
`chore/<topic>`. Keep commits independently reversible and use Conventional
Commit subjects such as `feat: decode test status segments` or
`fix: reject oversized packet input before copying`.

Do not mix protocol behavior with unrelated cleanup. Do not commit standards
PDFs, private captures, generated build output, credentials, or proprietary
fusion logic.

## Protocol changes

Behavioral changes must follow red-green-refactor TDD:

1. Cite the exact edition, section, table, or official vector in the test.
2. Add the smallest test and observe it fail for the intended reason.
3. Implement the smallest coherent behavior that makes it pass.
4. Add malformed, boundary, round-trip, arbitrary-chunk, and resource-bound tests
   where applicable.
5. Update the requirement trace, conformance matrix, limitations, and roadmap.

Third-party implementations and samples are interoperability evidence, never
normative sources. Preserve unknown data and exact encoded values unless an
explicit strict validator reports them.

## Required checks

```console
ruff check .
mypy src
pytest --cov=stanag4607 --cov-branch --cov-report=term-missing
python -m build
python -m twine check dist/*
```

## Pull requests

Use a title matching the Conventional Commit subject. The description should
state the user-visible outcome, normative citations, observed failing test,
resource/security considerations, compatibility impact, samples used and their
provenance, documentation changes, and exact verification commands. Reviewers
should reject untraceable conformance claims, unbounded input handling, lost raw
values, hidden dependencies, and cross-sensor fusion policy.

