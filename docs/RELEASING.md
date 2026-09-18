# Releasing

Only a maintainer may release. Releases are built from a clean, reviewed commit;
standards PDFs, private captures, credentials, and local build products must not
be tracked.

Before making the source repository public, verify that its only advertised
branch contains the intended audited snapshot, no private samples or standards
PDFs are tracked, and GitHub Actions logs and repository settings can be shown
publicly. A rewritten branch does not guarantee that earlier remote objects or
logs become inaccessible. Enable private vulnerability reporting and branch/tag
rules before inviting outside contributions. Public source availability is not
itself a PyPI release or an operational-conformance claim.

1. Choose a PEP 440 version and update both `project.version` in `pyproject.toml`
   and `stanag4607.__version__` in `src/stanag4607/__init__.py`.
2. Move relevant `CHANGELOG.md` entries from Unreleased to the dated version.
3. Review conformance claims, limitations, API changes, sample provenance, and
   `docs/API_STABILITY.md` against the actual implementation.
4. Run the complete checks from `CONTRIBUTING.md` in a clean environment.
5. Inspect the wheel and source archive. Install the wheel into a new environment
   and smoke-test `stanag4607 --help` plus one attributed fixture.
6. Create a signed tag `v<version>` only after those checks pass.
7. Prefer PyPI trusted publishing from a protected release environment. Never put
   a PyPI API token in Git, workflow text, command history, or a pull request.
8. Verify the published metadata, wheel hash, import, CLI, and project links from
   a fresh installation before announcing the release.

Version `0.1.0` establishes the first alpha API baseline. A version number below
1.0 communicates that compatibility and conformance coverage are still evolving;
the distribution does not need a prerelease suffix merely to repeat that status.
