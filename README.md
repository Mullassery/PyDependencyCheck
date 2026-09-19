# PyDependencyCheck

## Problem

Most dependency tooling tells you *what* you depend on. It rarely tells you *why* a
package is there, whether it's actually still used, whether it's vulnerable right now,
or whether your CI should block a merge over it — and generating a signed SBOM or a
license-compliance report usually means stitching together several separate tools.

## Solution

Dependency intelligence and supply-chain security for Python projects. A Rust core
(dependency parsing, graph algorithms, OSV vulnerability scanning) wrapped in a Python
CLI: scan dependencies, see who introduced them and why, find unused packages, check
license compliance, generate signed SBOMs, and gate CI builds on a real health score.

[![PyPI](https://img.shields.io/pypi/v/pydependencycheck)](https://pypi.org/project/pydependencycheck)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)
[![CI](https://github.com/Mullassery/PyDependencyCheck/actions/workflows/ci.yml/badge.svg)](https://github.com/Mullassery/PyDependencyCheck/actions/workflows/ci.yml)

## Use cases

- **Gating a CI pipeline on dependency health** — `pydependencycheck gate --min-health 50`
  exits non-zero and prints real GitHub Actions annotations, so a PR fails the same way
  a test failure would. See [CI gating](#ci-gating-with-github-actions) below.
- **Investigating why a package is in your tree** — `why requests` / `trace requests`
  give git-blame provenance and full history, useful when auditing an unfamiliar
  project or figuring out who to ask about a dependency.
- **Auto-patching known-vulnerable pins** — `remediate --apply` (or `--pr` to open a
  real GitHub PR) bumps exactly-pinned vulnerable packages to their OSV `fix_version`.
  Only handles exact `==` pins today — a range like `>=2.0,<3.0` isn't touched.
- **Producing a signed SBOM for compliance** — `export --format cyclonedx --sign` for
  CycloneDX/SPDX output with an RSA-SHA256 signature.
- **Not yet a good fit for:** projects that only ship `setup.py`/`setup.cfg` with no
  `requirements.txt`/`pyproject.toml` (unsupported — see
  [What's not working](#whats-not-working--open-issues)); teams relying on the CI
  workflow's automated PyPI publish step (currently broken — see the same section).

## Installation

```bash
pip install pydependencycheck
```

For SBOM signing (needs `cryptography`) or OpenTelemetry export:

```bash
pip install "pydependencycheck[sbom,otel]"
```

Requires Python 3.8+. Prebuilt wheels are published for Linux, macOS (Intel/Apple Silicon), and Windows; see [.github/INSTALL.md](.github/INSTALL.md) if you need to build from source.

## Quick start

```bash
# Scan the current project (--path defaults to ".")
pydependencycheck scan

# Why is this package installed, and who added it?
pydependencycheck why requests

# Full git history for a dependency (added/upgraded/downgraded over time)
pydependencycheck trace requests

# Real health score: live vulnerabilities, staleness, dead deps, complexity
pydependencycheck health

# License compliance report, checked against your project's license
pydependencycheck licenses --project-license MIT

# Export a signed CycloneDX SBOM
pydependencycheck export --format cyclonedx --output sbom.json

# Gate a CI build: exits non-zero if health/vulnerabilities/dead-deps fail thresholds
pydependencycheck gate --min-health 50
```

## Commands

| Command | What it does |
|---|---|
| `scan` | Parse dependency files, report direct/transitive counts (table, JSON, HTML, or Markdown) |
| `list` | Table of all detected dependencies |
| `why PACKAGE` | Git-blame provenance: who added it, in which commit |
| `trace PACKAGE` | Current status plus full git history for that dependency |
| `health` | Computed health score (vulnerabilities, staleness, dead deps, complexity) |
| `licenses` | License classification + compatibility check per dependency |
| `export` | SBOM export (CycloneDX or SPDX), optionally signed |
| `gate` | CI gate: real exit code based on health/vulnerability/dead-dep thresholds |
| `remediate` | Patch vulnerable dependencies to their OSV `fix_version`, optionally as a real git branch/commit + GitHub PR |
| `snapshot` | Save or inspect a dependency snapshot |
| `history` | Timeline of saved snapshots |
| `drift` | Diff the current scan against a saved baseline |

Run `pydependencycheck COMMAND --help` for the full option list on any command (most support `--path`, and `scan`/`export`/`licenses`/`health`/`gate` support `--offline`/`--path` variants where relevant).

### Health scoring

`health` (and `gate`) combine four real, independently-computed factors:

```bash
pydependencycheck health
```

```
Dependency Health Score: 87/100 (Excellent)
               Health Score Breakdown
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Factor          ┃ Score   ┃ Status               ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ Overall Health  │ 87/100  │ ████████░░ Excellent │
│ Vulnerabilities │ 100/100 │ ██████████ Excellent │
│ Maintenance     │ 100/100 │ ██████████ Excellent │
│ Quality         │ 40/100  │ ████░░░░░░ Poor      │
│ Complexity      │ 95/100  │ █████████░ Excellent │
└─────────────────┴─────────┴──────────────────────┘
```

Vulnerabilities and staleness require live network calls (OSV.dev and PyPI's JSON API); pass `--offline` to skip them and get a deterministic score from local data only (dead-dependency detection and graph complexity). The "Quality" factor is currently a single metric, not yet an aggregate of multiple signals — see [What's not working](#whats-not-working--open-issues).

### Automated remediation

`remediate` turns an OSV.dev vulnerability finding into an actual patch --
not just a report:

```bash
# Dry run: prints a unified diff for every affected file, changes nothing
pydependencycheck remediate

# Write the fixed versions to requirements.txt/pyproject.toml for real
pydependencycheck remediate --apply

# Create a real git branch + commit for the fix, push it, and open a GitHub
# PR via the `gh` CLI (if installed and authenticated)
pydependencycheck remediate --pr
```

```
2 fixable vulnerable package(s):
  requests: 2.25.0 -> 2.33.0  [GHSA-9hjg-9r4m-mvj7, PYSEC-2023-74, ...]
  flask: 2.0.0 -> 2.3.2  [GHSA-m2qf-hxjv-5gpq]

--- requirements.txt ---
--- a/requirements.txt
+++ b/requirements.txt
@@ -1,2 +1,2 @@
-requests==2.25.0
-flask==2.0.0
+requests==2.33.0
+flask==2.3.2
```

Only exact `==` pins in `requirements.txt`/`constraints.txt`/`pyproject.toml`
are patched (a range like `>=2.0,<3.0` doesn't name one concrete version to
bump). With `--pr` but no `gh` CLI available, the branch is still created
and pushed for real -- open the PR manually.

### SBOM export and signing

```bash
# Generate keys once
python3 -c "from pydependencycheck.sbom import SBOMSigner; SBOMSigner().generate_keys('signing-key.pem')"

# Export a signed SBOM
pydependencycheck export --format cyclonedx --sign --key signing-key.pem --output sbom.json
```

The SBOM carries a SHA-256 integrity hash and (when `--sign` is used) an RSA-SHA256 signature over the document, verifiable with `SBOMSigner.verify_sbom()`.

### CI gating with GitHub Actions

```yaml
name: Dependency Check
on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - run: pip install pydependencycheck
      - run: pydependencycheck scan --save-snapshot
      - run: pydependencycheck gate --min-health 50
      - run: pydependencycheck export --format cyclonedx --output sbom.json

      - uses: actions/upload-artifact@v3
        with:
          name: sbom
          path: sbom.json
```

`gate` prints `::error`/`::warning`/`::notice` GitHub Actions annotations automatically when `GITHUB_ACTIONS` is set, and always sets the process exit code (1 on failure), so it works as a real CI gate on any CI system, not just GitHub Actions.

### OpenTelemetry

```bash
pydependencycheck health --otel
```

Defaults to a `console` exporter backed by the real OpenTelemetry SDK (`ConsoleSpanExporter`/`ConsoleMetricExporter`) -- genuine spans and metrics printed to stdout, no collector required, and verified by tests. Pass `--otel-exporter otlp|jaeger|prometheus` to ship to real infrastructure if you have it configured; if the corresponding exporter package isn't installed, it falls back to `console` rather than silently doing nothing. These three backends are real code paths but aren't verified end-to-end against a live collector in this project's own test suite — see [`ROADMAP_HONEST.md`](ROADMAP_HONEST.md).

## Architecture

Rust workspace (`crates/`) does the heavy lifting, exposed to Python via PyO3:

- `pydep-parser` -- PEP 508 requirements/pyproject.toml parsing (extras, markers, every version operator)
- `pydep-graph` -- dependency graph construction, cycle detection, topological sort (petgraph)
- `pydep-ast` -- import extraction and dead-dependency detection
- `pydep-security` -- OSV.dev vulnerability queries and risk scoring
- `pydep-py` -- PyO3 bindings tying it together as `pydependencycheck._pydependencycheck`

The Python package (`python/pydependencycheck/`) is the CLI, plus SBOM generation, license analysis, git integration, SQLite-backed snapshot storage, and OpenTelemetry instrumentation.

## What's working now (verified)

**46 Rust tests** (`cargo test --workspace`, re-verified 2026-09-20: 15+7+9+15
passed across the four crates with tests) + **153 Python tests** (`pytest
tests/`) covering the CLI end-to-end, SBOM signing/verification, license
classification, health scoring, `remediate`'s full plan/apply/branch/commit/
push/PR path (against a real `gh` binary and a real local git remote, not
mocks), and the SQLite storage layer. Re-verified 2026-09-20: **136 pass
unconditionally; the other 17 are OpenTelemetry-integration tests that
`pytest.mark.skipif` skips unless `opentelemetry-api`/`opentelemetry-sdk` are
installed.** `ci.yml`'s `python-tests` job does not install those packages,
so a real CI run shows "136 passed, 17 skipped," not "153 passed" — install
`pydependencycheck[otel]` locally to actually exercise those 17. Wheels build
successfully for Linux, macOS (Intel/ARM), and Windows (re-verified: `maturin
develop --release` succeeds on macOS arm64). See
[`ROADMAP_HONEST.md`](ROADMAP_HONEST.md) for the full built-and-verified /
built-but-unverified / not-built breakdown.

## What's not working / open issues

- **The automated PyPI publish CI job has never succeeded.** Both real release-tag
  pushes to date (`v1.0.0`, `v1.4.0`) failed at the "Publish to PyPI" step: no
  `PYPI_API_TOKEN` secret is configured, so the action falls back to OIDC trusted
  publishing, which then fails because the workflow has no `permissions: id-token:
  write` block. **The current PyPI release (v1.4.0, matches this repo's version with no
  drift) was published manually via `twine`, not through this CI job.** Not yet fixed —
  needs either a `PYPI_API_TOKEN` secret or a properly configured Trusted Publisher on
  PyPI's side. See [`ROADMAP_HONEST.md`](ROADMAP_HONEST.md) for the full failure log
  detail.
- **`setup.py`/`setup.cfg`-only projects (no `requirements.txt` or `pyproject.toml`)
  are not parsed** — AST parsing of `setup.py` and INI parsing of `setup.cfg` are
  literal `TODO` stubs (`crates/pydep-parser/src/setup.rs`,
  `python/pydependencycheck/scanner.py`), and are consequently also not covered by
  `remediate`.
- **The health-score "Quality" factor is a single metric today** — aggregating
  multiple quality signals is tracked as future work
  (`python/pydependencycheck/scanner.py`).
- **OTLP/Jaeger/Prometheus OTEL exporters aren't verified end-to-end** against a real
  collector in this project's own tests — only the fallback-to-console behavior is
  tested. See [OpenTelemetry](#opentelemetry) above.
- **Fixed this release, disclosed for anyone on an older version:**
  `check_vulnerabilities()` was passing the full PEP 508 specifier (e.g. `"==2.25.0"`)
  to OSV.dev instead of the bare version -- OSV's range matching silently fell back to
  exact-string matching against nothing, meaning `health`/`gate` reported **zero
  vulnerabilities for essentially every exactly-pinned dependency** on any version
  before this fix. Also fixed: `fix_version` could come back as a raw git commit hash
  instead of a PyPI version when an advisory's `affected[].ranges` listed a GIT-type
  range before its ECOSYSTEM range (both in `crates/pydep-security/src/osv.rs`; see
  `fix_version_ignores_git_range_and_uses_ecosystem_range` for the regression test).
- No open GitHub issues at the time of this writing.

## Requirements

Python 3.8+ on Linux (x86_64), macOS (Intel/ARM), or Windows (x86_64).

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.

When using PyDependencyCheck, include this attribution:
> Powered by PyDependencyCheck (https://github.com/Mullassery/PyDependencyCheck)

## Support

- Issues: https://github.com/Mullassery/PyDependencyCheck/issues
- Discussions: https://github.com/Mullassery/PyDependencyCheck/discussions
- Email: mullassery@gmail.com
