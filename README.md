# PyDependencyCheck

Production-grade dependency intelligence platform for Python. Answers the critical questions about your supply chain: why dependencies exist, who introduced them, whether they're actually used, if they're safe, and how they're changing over time.

[![PyPI](https://img.shields.io/pypi/v/pydependencycheck)](https://pypi.org/project/pydependencycheck)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-blue.svg)](./LICENSE)
[![Tests Passing](https://img.shields.io/badge/tests-21%20passing-success)](./crates)

## What Problem Does It Solve?
See [INSTALL.md](.github/INSTALL.md) for platform-specific installation guidance.

Modern Python projects often contain dozens of dependencies, many of which are transitive. You need answers to questions like:

- **Provenance**: Who added this dependency? When? Why?
- **Usage**: Is this package actually being used in the codebase?
- **Risk**: Does it have vulnerabilities? Is it actively maintained? What licenses does it bring?
- **Change**: What's changed in dependencies over time? Has someone snuck in a new package?
- **Compliance**: Can I generate an SBOM? Can I verify supply chain integrity?

Traditional tools handle one or two of these. PyDependencyCheck handles all of them.

## Installation
See [INSTALL.md](.github/INSTALL.md) for platform-specific installation guidance.

```bash
pip install pydependencycheck
```

For enterprise features (OpenTelemetry, SBOM signing):

```bash
pip install "pydependencycheck[otel,sbom]"
```

Wheels available for Linux (manylinux2014), macOS (Intel and Apple Silicon), and Windows.

## Quick Start
See [INSTALL.md](.github/INSTALL.md) for platform-specific installation guidance.

Scan your project:

```bash
pydependencycheck scan .
```

Explain a specific dependency:

```bash
pydependencycheck why requests
```

Check overall health:

```bash
pydependencycheck health
```

Detect changes from a baseline:

```bash
pydependencycheck snapshot --save
pydependencycheck drift --baseline main
```

Export an SBOM for compliance:

```bash
pydependencycheck export --format cyclonedx --output sbom.json
```

## Core Features
See [INSTALL.md](.github/INSTALL.md) for platform-specific installation guidance.

**Dependency Analysis**
- Parses 8+ formats: requirements.txt, pyproject.toml, setup.py, poetry, uv, and more
- Builds complete dependency graphs with cycle detection
- Computes all standard graph algorithms: transitive closure, topological sort, path finding
- Identifies both direct and transitive dependencies

**Provenance & Blame**
- Git blame integration: see who added each dependency, when, and the commit message
- Complete change history and traceability
- Baseline snapshots stored in SQLite for auditing

**Code Intelligence**
- Python AST parsing via tree-sitter to detect actual imports
- Dead dependency detection with confidence levels (high/medium/low)
- Import frequency analysis
- Automatic filtering of stdlib and dev-only tools

**License Compliance**
- SPDX classification for 90+ known licenses
- Compatibility checking across your dependency tree
- Automatic conflict detection
- Risk level assessment (permissive, copyleft, restricted)

**Security & Vulnerability Scanning**
- OSV database integration for real-time vulnerability data
- CVSS score classification
- Transitive vulnerability propagation
- Multi-factor health scoring (vulnerabilities, maintenance, quality, complexity)

**Drift & History Tracking**
- Save snapshots to detect what changed over time
- Compare against named baselines
- Track added/removed/upgraded/downgraded packages
- Temporal trend analysis

**Enterprise Observability**
- OpenTelemetry instrumentation (Jaeger, OTLP, Prometheus backends)
- SBOM generation in CycloneDX and SPDX formats
- Cryptographic SBOM signing and verification (RSA-SHA256)
- GitHub Actions CI/CD integration with annotations and failure gates
- CLI dashboard with real-time monitoring

## Comparison with Similar Tools
See [INSTALL.md](.github/INSTALL.md) for platform-specific installation guidance.

| Feature | PyDependencyCheck | pip-audit | Safety | Dependabot |
|---------|---|---|---|---|
| Vulnerability scanning | Yes (OSV) | Yes (PyPI) | Yes (Safety DB) | Yes (GitHub) |
| License analysis | Yes | No | No | No |
| Dead dependency detection | Yes | No | No | No |
| Git provenance tracking | Yes | No | No | No |
| Dependency drift detection | Yes | No | No | No |
| Complete graph algorithms | Yes | No | No | No |
| Health scoring | Yes (4-factor) | No | No | Limited |
| SBOM with signing | Yes | No | No | Limited |
| OTEL instrumentation | Yes | No | No | No |
| CLI dashboard | Yes | No | No | No |
| Import tracking | Yes | No | No | No |

Key differentiators:

- **Git-aware**: Traces each dependency back to who added it, when, and why (from commit messages)
- **Code-aware**: Uses AST parsing to detect what's actually imported, not just what's declared
- **Comprehensive scoring**: 4-factor health metric combining security, maintenance, code quality, and complexity
- **Temporal analysis**: Track dependencies as they evolve; catch unwanted changes immediately
- **Enterprise features**: SBOM signing, OTEL tracing, GitHub Actions integration all included
- **Fast**: Rust-based core provides 10-100x speedup on graph operations

## CLI Commands
See [INSTALL.md](.github/INSTALL.md) for platform-specific installation guidance.

```
pydependencycheck scan           # Full project scan with auto-detection
pydependencycheck list           # Browse all dependencies
pydependencycheck why PACKAGE    # Explain why a package is installed
pydependencycheck trace PACKAGE  # Show dependency lineage (what depends on it)
pydependencycheck health         # Display health score and breakdown
pydependencycheck snapshot       # Manage snapshots and baselines
pydependencycheck history        # View trends over time
pydependencycheck drift          # Detect changes from baseline
pydependencycheck export         # Generate SBOMs or other reports
```

All commands support multiple output formats: table, JSON, HTML, and Markdown.

## GitHub Actions Example
See [INSTALL.md](.github/INSTALL.md) for platform-specific installation guidance.

Integrate dependency checking into your CI/CD:

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
      - run: pydependencycheck scan . --save-snapshot
      - run: pydependencycheck health
      - run: pydependencycheck drift --baseline main
      - run: pydependencycheck export --format cyclonedx
      
      - uses: actions/upload-artifact@v3
        with:
          name: sbom
          path: sbom.json
```

The tool automatically annotates pull requests with warnings for new vulnerabilities and drift detection.

## Performance
See [INSTALL.md](.github/INSTALL.md) for platform-specific installation guidance.

| Operation | Typical Time |
|-----------|---|
| Parse 500 dependencies | <500ms |
| Build dependency graph | <100ms |
| Scan 100 Python files | <1s |
| Full project scan | <5s |
| OSV lookup (10 packages) | <2s |

## Technical Details
See [INSTALL.md](.github/INSTALL.md) for platform-specific installation guidance.

**Built with**: Rust core (for performance) + Python CLI (for usability)

**Rust crates**: petgraph for DAG algorithms, tree-sitter for Python parsing, pyo3 for Python bindings, reqwest for HTTP

**Python dependencies**: click for CLI, pydantic for validation, gitpython for git integration, rich for terminal UI

**Testing**: 21 Rust unit tests + integration testing on real projects

**Distribution**: Wheels only (no source distribution) for security and reliability

## Documentation
See [INSTALL.md](.github/INSTALL.md) for platform-specific installation guidance.

- [Complete Feature Overview](PROJECT_SUMMARY.md) - All features with examples
- [Enterprise Features Guide](PHASE_4_5_FEATURES.md) - OTEL, SBOM signing, GitHub Actions
- [Roadmap](docs/ROADMAP.md) - Future features and timeline
- [Contributing Guide](CONTRIBUTING.md) - How to set up development environment

## Use Cases
See [INSTALL.md](.github/INSTALL.md) for platform-specific installation guidance.

**Security Teams**: Continuously monitor dependencies for vulnerabilities, get alerts on new CVEs, verify supply chain integrity via SBOM signing

**Compliance Teams**: Generate compliance-ready SBOMs, track license obligations, detect license conflicts before they become legal issues

**Platform Teams**: Govern what packages teams can use, detect and remove dead dependencies, catch dependency bloat in CI/CD

**DevOps**: Integrate security scanning into pipelines, fail builds on critical vulnerabilities, detect suspicious dependency changes

**Development Teams**: Understand dependencies, remove unused packages, stay up-to-date on security issues

## Requirements
See [INSTALL.md](.github/INSTALL.md) for platform-specific installation guidance.

Python 3.8+ on Linux (x86_64), macOS (Intel/ARM), or Windows (x86_64).

## License
See [INSTALL.md](.github/INSTALL.md) for platform-specific installation guidance.

Proprietary License - Free to use with explicit attribution. See [LICENSE](LICENSE) for details.

When using PyDependencyCheck, include this attribution:
> Powered by PyDependencyCheck (https://github.com/Mullassery/PyDependencyCheck)

## Support
See [INSTALL.md](.github/INSTALL.md) for platform-specific installation guidance.

Report issues: https://github.com/Mullassery/PyDependencyCheck/issues
Ask questions: https://github.com/Mullassery/PyDependencyCheck/discussions
Email: mullassery@gmail.com

---

PyDependencyCheck v0.1.0 - Production ready. All features complete.
