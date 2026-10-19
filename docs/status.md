# Project status

**Version:** 1.5.0 · **Status:** beta · **Updated:** 2026-10-19

This page is the current, user-facing status summary. For the long engineering
snapshot and historical detail, see
[`ROADMAP_HONEST.md`](../ROADMAP_HONEST.md), [`QUEUE_STATUS.md`](../QUEUE_STATUS.md),
and [`AUDIT_FINDINGS.md`](../AUDIT_FINDINGS.md).

## Verified working (2026-10-19)

- Manifest scanning: `requirements.txt`, `constraints.txt`, `pyproject.toml`
  (PEP 621 + Poetry), static `setup.py`/`setup.cfg`.
- OSV vulnerability checks; PyPI staleness; AST unused-dependency detection;
  license classification.
- `why`/`trace` Git provenance.
- Health score and `gate` with GitHub Actions annotations.
- CycloneDX 1.4 and SPDX 2.3 SBOM export; RSA-SHA256 signing; CycloneDX 1.6 VEX.
- Snapshots, drift, and history.
- Optional OpenTelemetry (console exporter verified; remote exporters not
  verified end-to-end).

## Known gaps

| Gap | Impact | Status |
|---|---|---|
| Lockfiles (`poetry.lock`, `uv.lock`, `Pipfile[.lock]`) discovered but not parsed | Scans of lockfile-only projects report 0 dependencies | Open (verified) |
| No reachability analysis | Vulnerability noise; VEX defaults to `under_investigation` | Open |
| Exact-pin-only remediation | Version ranges are not rewritten | By design |
| PEP 440 edge cases (`.postN`, `.devN`, local, 4+ parts) | May fall back to exact-string OSV matching | Open (tracked) |
| No GitHub Action / SARIF | CI integration requires a manual step | Open |
| Wheel coverage varies by release | Linux/Windows users may need to build from source | Open (verified for 1.5.0) |
| CI tests Python 3.11 only | 3.8–3.10 declared but untested in CI | Open |
| Wheel job uses `pytest ... \|\| true` | Wheel tests cannot fail the build | Open |
| PyPI Trusted Publisher registration | Publish job may still require manual upload | Pending human step |

## Rejected / deferred

- **Multi-ecosystem and container scanning** — owned by sibling projects
  (PyDeepMesh) and dedicated scanners; duplicating it is out of scope.
- **Benchmarks** — not published until a reproducible methodology exists.

## How to help

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) and the open gaps above. Good first
areas: lockfile parsing, action/SARIF integration, and Python-version CI matrix.
