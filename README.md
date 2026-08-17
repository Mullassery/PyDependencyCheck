# PyDependencyCheck

Dependency intelligence and supply-chain security for Python projects. A Rust core (dependency parsing, graph algorithms, OSV vulnerability scanning) wrapped in a Python CLI: scan dependencies, see who introduced them and why, find unused packages, check license compliance, generate signed SBOMs, and gate CI builds on a real health score.

[![PyPI](https://img.shields.io/pypi/v/pydependencycheck)](https://pypi.org/project/pydependencycheck)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-blue.svg)](./LICENSE)
[![CI](https://github.com/Mullassery/PyDependencyCheck/actions/workflows/ci.yml/badge.svg)](https://github.com/Mullassery/PyDependencyCheck/actions/workflows/ci.yml)

## What it does

- **Scan**: auto-detect and parse `requirements.txt`, `pyproject.toml` (PEP 621 and Poetry), and `constraints.txt`, handling every PEP 508 version operator and extras.
- **Why / trace**: git-blame-based provenance (who added a dependency, in which commit) and full chronological history across the project's git log.
- **Health**: a real, computed 0-100 score combining live OSV.dev vulnerability data, PyPI release staleness, AST-detected dead dependencies, and dependency-graph complexity.
- **SBOM export**: CycloneDX 1.4 and SPDX 2.3 JSON, with optional RSA-SHA256 signing and verification.
- **License compliance**: fetches real PyPI license metadata, classifies permissive/copyleft/restricted, and checks compatibility against your project's own license.
- **CI gating**: `gate` computes the same health score and exits non-zero on failure, with GitHub Actions `::error`/`::warning`/`::notice` annotations when run inside a GitHub Actions job.
- **Drift & history**: SQLite-backed snapshots so you can diff what changed since a baseline.
- **OpenTelemetry**: optional tracing/metrics via `--otel`, defaulting to a console exporter (no collector required) or OTLP/Jaeger/Prometheus if configured.

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

Vulnerabilities and staleness require live network calls (OSV.dev and PyPI's JSON API); pass `--offline` to skip them and get a deterministic score from local data only (dead-dependency detection and graph complexity).

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

Defaults to a `console` exporter backed by the real OpenTelemetry SDK (`ConsoleSpanExporter`/`ConsoleMetricExporter`) -- genuine spans and metrics printed to stdout, no collector required. Pass `--otel-exporter otlp|jaeger|prometheus` to ship to real infrastructure if you have it configured; if the corresponding exporter package isn't installed, it falls back to `console` rather than silently doing nothing.

## Architecture

Rust workspace (`crates/`) does the heavy lifting, exposed to Python via PyO3:

- `pydep-parser` -- PEP 508 requirements/pyproject.toml parsing (extras, markers, every version operator)
- `pydep-graph` -- dependency graph construction, cycle detection, topological sort (petgraph)
- `pydep-ast` -- import extraction and dead-dependency detection
- `pydep-security` -- OSV.dev vulnerability queries and risk scoring
- `pydep-py` -- PyO3 bindings tying it together as `pydependencycheck._pydependencycheck`

The Python package (`python/pydependencycheck/`) is the CLI, plus SBOM generation, license analysis, git integration, SQLite-backed snapshot storage, and OpenTelemetry instrumentation.

**Testing**: 45 Rust unit tests (`cargo test --workspace`) across all four crates, plus 126 Python tests (`pytest tests/`) covering the CLI end-to-end, the XSS fix, SBOM signing/verification, license classification, health scoring, and the SQLite storage layer.

## Requirements

Python 3.8+ on Linux (x86_64), macOS (Intel/ARM), or Windows (x86_64).

## License

Proprietary License - free to use with explicit attribution. See [LICENSE](LICENSE) for details.

When using PyDependencyCheck, include this attribution:
> Powered by PyDependencyCheck (https://github.com/Mullassery/PyDependencyCheck)

## Support

- Issues: https://github.com/Mullassery/PyDependencyCheck/issues
- Discussions: https://github.com/Mullassery/PyDependencyCheck/discussions
- Email: mullassery@gmail.com
