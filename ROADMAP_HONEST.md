# PyDependencyCheck — Honest Status

**Current Version:** v1.4.0 (matches the version live on PyPI — no drift)
**Last Updated:** 2026-09-11

This file exists to say plainly what's built-and-verified, what's built-but-unverified,
what's not built yet, and what's actively broken in CI/release infrastructure —
`README.md` documents the intended public API; this file is the "have we actually
verified this" companion, kept up front so future roadmap planning starts from reality
instead of from what the README merely claims.

## 🟢 Built & verified (real implementation, real test coverage)

- **Dependency parsing** — `requirements.txt`, `pyproject.toml` (PEP 621 + Poetry),
  `constraints.txt`; every PEP 508 version operator and extras (`crates/pydep-parser`).
- **Health scoring** — 4 real, independently-computed factors (vulnerabilities via
  OSV.dev, staleness via PyPI's JSON API, dead dependencies via AST import analysis,
  dependency-graph complexity).
- **`remediate`** — dry-run diff, `--apply` (writes real file changes, tested against a
  real tmp project), and `--pr` (creates a real git branch + commit against a real repo
  fixture, pushes to a real local bare remote, and invokes the actual `gh` binary via
  subprocess against a fake `gh` executable on `PATH` — not a mock of `subprocess.run`).
- **SBOM export** — CycloneDX 1.4 and SPDX 2.3, with RSA-SHA256 signing/verification.
- **License compliance** — real PyPI license metadata fetch, permissive/copyleft/
  restricted classification, compatibility check.
- **CI gating (`gate`)** — real GitHub Actions `::error`/`::warning`/`::notice`
  annotations, real non-zero exit code.
- **Drift/snapshot/history** — SQLite-backed, diffs against a saved baseline.
- **OpenTelemetry, console exporter** — genuine OTEL SDK spans/metrics to stdout,
  verified by tests that capture real console output in a fresh subprocess.
- **OSV vulnerability matching bug (fixed this release)** — `check_vulnerabilities()`
  was passing the full PEP 508 specifier (e.g. `"==2.25.0"`) to OSV.dev instead of the
  bare version, so `health`/`gate` silently reported zero vulnerabilities for
  essentially every exactly-pinned dependency. Fixed, with a regression test
  (`crates/pydep-security/src/osv.rs`).
- **46 Rust tests** (`cargo test --workspace`) + **153 Python tests** (`pytest tests/`),
  all passing as of the 2026-09-11 CI run on `main`. Wheels build successfully for
  Linux/macOS (Intel+ARM)/Windows.

## 🟡 Built but not independently verified

- **OTLP/Jaeger/Prometheus OTEL exporters** — real code paths exist
  (`--otel-exporter otlp|jaeger|prometheus`), and the fallback-to-console behavior *when
  the exporter package is missing* is tested. But no test actually verifies data
  reaching a real OTLP collector/Jaeger/Prometheus backend — that would need real
  infrastructure in CI, which doesn't exist here. Treat these three as "should work,
  unverified end-to-end" rather than "confirmed."

## 🔴 Not built / not yet functional

- **`setup.py`/`setup.cfg`-only projects are not parsed.** Both AST parsing of
  `setup.py` (`crates/pydep-parser/src/setup.rs:7`) and INI parsing of `setup.cfg`
  (`crates/pydep-parser/src/setup.rs:14`) are literal `// TODO` stubs — projects using
  only these (no `requirements.txt`/`pyproject.toml`) aren't scanned at all, and
  consequently aren't covered by `remediate` either.
- **Health score "Quality" factor is a single metric**, not yet an aggregate of
  multiple quality signals (`python/pydependencycheck/scanner.py`).

## ⚠️ CI/CD — current errors

- **The PyPI publish job has never succeeded on a real release tag.** Both real
  release-tag pushes to date — `v1.0.0` and `v1.4.0` — failed at the "Publish to PyPI"
  step (`.github/workflows/wheels.yml`, job `publish`, gated on
  `refs/tags/v*`). Root cause, from the actual failed-run logs: no `PYPI_API_TOKEN`
  secret is configured on this repo, so `pypa/gh-action-pypi-publish` falls back to
  OIDC trusted publishing — which then fails because the workflow has no `permissions:
  id-token: write` block at the job level (`OpenID Connect token retrieval failed:
  ... the ACTIONS_ID_TOKEN_REQUEST_TOKEN environment variable was unset`). **v1.4.0 is
  live on PyPI today only because it was uploaded manually via `twine`**, not through
  this CI job. Two ways to actually fix this (not yet done, needs a maintainer
  decision): (a) add a `PYPI_API_TOKEN` repo secret and keep password-based publish, or
  (b) register this project for PyPI Trusted Publishing and add `permissions:
  id-token: write` to the `publish` job. Until one of these happens, every future
  release needs a manual `twine upload`.

## Tracking this for future roadmap planning

The categories above (built & verified / built but unverified / not built / CI errors)
are the four buckets worth checking before adding anything new to the roadmap — a
feature that looks "done" in the README can still be sitting in one of the bottom two.
