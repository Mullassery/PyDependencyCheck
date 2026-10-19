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
| 1.5.x (latest) | Yes |
| < 1.5 | No |

## Known, Currently Open Security-Relevant Gaps

Disclosed here instead of left implicit — see
[ROADMAP_HONEST.md](ROADMAP_HONEST.md) for full detail:

- **Release publishing may still be manual.** The `.github/workflows/wheels.yml`
  `publish` job now uses PyPI Trusted Publishing (OIDC) and requires no
  `PYPI_API_TOKEN` secret. It still requires a one-time Trusted Publisher
  registration for this repository on PyPI. Until that registration is
  confirmed, a release may have been built and uploaded manually by the
  maintainer, so releases are not guaranteed to be reproducibly built by CI.
- **Wheel coverage varies by release.** The wheel workflow is configured for
  Linux, macOS, and Windows, but a given PyPI release may not include every
  platform. Check
  [Compatibility](docs/compatibility.md) before assuming a wheel exists.
- **Dynamic `setup.py` metadata is not executed.** Static `install_requires`
  and `extras_require` are parsed (v1.5.0+), but calls such as
  `install_requires=read_requirements()` are reported as warnings rather than
  resolved.

## This Tool's Own Dependencies

This project scans *other* projects' dependencies for known vulnerabilities.
`.github/workflows/security-audit.yml` runs `cargo audit` and `pip-audit` in
CI, and `.github/dependabot.yml` covers automated updates. There is currently
no `pydependencycheck gate` step against this repository itself — see
`ROADMAP_HONEST.md` for the tracked gap.
