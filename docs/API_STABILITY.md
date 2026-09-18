# API stability

The package is pre-1.0. Public names exported by `stanag4607.__all__`, the
`stanag4607` console command, immutable decoded models, issue codes, and encoded
wire behavior form the supported API surface.

Patch releases may add validators, properties, issue codes, and support for new
segment types. Minor pre-1.0 releases may make necessary incompatible changes,
but each must be documented in `CHANGELOG.md` with a migration note. Removing or
renaming a public symbol, changing a field's unit/type, changing exception class,
or changing accepted wire data is incompatible and must not happen silently.

Internal names beginning with an underscore, exact error-message prose, CLI JSON
key order, and undocumented implementation details are not stable. Validation
issue `code` and `fields` values are stable machine interfaces; message prose may
be clarified without changing meaning. A truncated CLI validation report adds
`issue_count` and `issues_truncated`; consumers must tolerate these optional keys.

Decoders remain preservation-oriented. Adding a semantic diagnostic must not
turn previously decodable data into a decode failure unless accepting it is
unsafe or contradicts structural framing. Unknown segment payloads and reserved
values must continue to round-trip exactly.

Before a release, compare `stanag4607.__all__`, constructor signatures, issue
codes, CLI output schemas, and fixture round trips against the previous release.
The first published alpha establishes that baseline.
