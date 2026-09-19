# Security Policy

## Reporting a Vulnerability

Email **mullassery@gmail.com** with details (what/where/how to reproduce).
There is no PGP key, dedicated security inbox, or bug bounty program for this
project — it's maintained by one person in their spare time. Expect an
acknowledgment within a few days, not a formal SLA.

Please do not open a public GitHub issue for a security vulnerability until
it's been triaged privately.

## Supported Versions

Only the latest release on PyPI is supported. There is no backport policy —
fixes land on `main` and ship in the next release.

| Version | Supported |
|---|---|
| 1.4.x (latest) | Yes |
| < 1.4 | No |

## Known, Currently Open Security-Relevant Gaps

Disclosed here instead of left implicit — see
[ROADMAP_HONEST.md](ROADMAP_HONEST.md) for full detail:

- The automated PyPI publish CI job (`.github/workflows/wheels.yml`, job
  `publish`) has never succeeded on a real release tag — no `PYPI_API_TOKEN`
  secret and no `permissions: id-token: write` for OIDC trusted publishing.
  Every release to date has been uploaded manually via `twine` by the
  maintainer, from their own machine. This is a supply-chain-integrity gap
  worth knowing about: releases are not reproducibly built and published by
  CI, they're built and published locally.
- `setup.py`/`setup.cfg`-only projects are not parsed at all
  (`crates/pydep-parser/src/setup.rs`), so this tool cannot audit dependencies
  declared only that way — don't assume a clean scan means no vulnerable
  pins if your project uses that layout.

## This Tool's Own Dependencies

This project scans *other* projects' dependencies for known vulnerabilities;
it doesn't currently run that same scan against itself in CI (no
`pydependencycheck gate` step, `cargo audit`, or `pip-audit` job exists yet —
see `ROADMAP_HONEST.md` for the tracked gap and `.github/dependabot.yml` for
the automated update coverage that does exist).
