# Releasing

Only a maintainer may release. Releases are built from a clean, reviewed commit;
standards PDFs, private captures, credentials, and local build products must not
be tracked.

Before a release, verify that the public branch contains the intended audited
source, no private samples or standards PDFs are tracked, and GitHub Actions
logs and repository settings can be shown publicly. A rewritten branch does
not guarantee that earlier remote objects or logs become inaccessible.
Private vulnerability reporting is enabled; review branch/tag rules before
inviting outside contributions. A public source repository and a PyPI
distribution are separate release milestones.

1. Choose a PEP 440 version and update both `project.version` in `pyproject.toml`
   and `stanag4607.__version__` in `src/stanag4607/__init__.py`.
2. Move relevant `CHANGELOG.md` entries into the dated version and check that
   every shipped feature is assigned to that version.
3. Review conformance claims, limitations, API changes, sample provenance, and
   `docs/API_STABILITY.md` against the actual implementation.
4. Run the complete checks from `CONTRIBUTING.md` in a clean environment,
   including the strict documentation build and tested example scripts.
5. Inspect the wheel and source archive. Install the wheel into a new environment
   and smoke-test `stanag4607 --help` plus one attributed fixture.
6. Register a PyPI pending trusted publisher before the first release, with
   project `stanag4607`, GitHub owner `trane293`, repository `stanag4607`,
   workflow `publish-to-pypi.yml`, and environment `pypi`. After first use, PyPI
   converts the pending publisher to a normal trusted publisher. Confirm the
   GitHub `pypi` environment requires `trane293` approval and accepts only `v*`
   tags. No API token is needed or permitted in Git, workflow text, command
   history, or a pull request.
7. Create a signed tag `v<version>` only after those checks pass, then publish a
   normal GitHub Release for that tag. The release workflow verifies that its
   source commit is reachable from `main` and its tag matches the package
   version, runs the full gates, builds both distributions, and pauses for
   environment approval before uploading to PyPI.
8. Verify the published metadata, wheel hash, import, CLI, and project links from
   a fresh installation before announcing the release. Confirm the rendered
   Read the Docs pages linked from the README and PyPI metadata are live.

Version `0.1.0` establishes the first alpha API baseline. A version number below
1.0 communicates that compatibility and conformance coverage are still evolving;
the distribution does not need a prerelease suffix merely to repeat that status.
