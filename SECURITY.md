# Security policy

STANAG 4607 input is untrusted binary data. Supported releases receive fixes for
memory/CPU amplification, unsafe subprocess or path handling, parser state
confusion, and validation bypasses within the documented profile.

Once the repository is public, report suspected vulnerabilities through GitHub's
**Report a vulnerability** form on the repository's Security page. If the form
is unavailable, open a public issue asking the maintainer to arrange a private
channel; do not include vulnerability details there. Do not include operational
captures, credentials, precise deployment details, or an exploit in a public
issue.

Include the affected version, entry point, smallest synthetic reproducer,
configured limits, observed impact, and suggested mitigation. Receipt and a
disclosure timeline should be agreed before public discussion.

The project cannot treat malformed-but-preserved wire values as vulnerabilities
by themselves. Decoding is preservation-oriented; applications must explicitly
run validators and enforce their own operational policy. See
`docs/LIMITATIONS.md` for current trust boundaries.
