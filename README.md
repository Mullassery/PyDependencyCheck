# PyDependencyCheck

**Dependency Intelligence and Governance Platform for Python**

> Git Blame + Dependency Graph + Security Scanner + License Auditor for your Python projects

PyDependencyCheck goes deeper than traditional dependency scanners. It answers the questions that matter:

- **Why** is this dependency installed?
- Which **package introduced** it?
- Is it **actually being used**?
- Is it **safe** (vulnerabilities, maintenance)?
- What **licenses** does it bring?
- What happens if we **remove it**?
- How much **bloat** does it create?

## Quick Start

```bash
# Install from PyPI
pip install pydependencycheck

# Scan a project
pydependencycheck scan .

# Ask why a dependency exists
pydependencycheck why requests

# Trace its lineage
pydependencycheck trace urllib3

# Find unused dependencies
pydependencycheck unused

# Check health score
pydependencycheck health --report-json
```

## Features

### Core (v0.1)
- ✅ Dependency parsing (requirements.txt, pyproject.toml, setup.py)
- ✅ Complete dependency graph construction
- ✅ Git blame for each dependency (who, when, why)
- ✅ Interactive HTML visualization with D3.js
- ✅ JSON export for CI/CD integration

### Usage Analysis (v0.2)
- 🔄 AST-based import detection
- 🔄 Dead dependency identification
- 🔄 License detection (SPDX)
- 🔄 Removal impact analysis

### Security (v0.3)
- 🔄 OSV integration (CVE database)
- 🔄 Transitive vulnerability propagation
- 🔄 Health score (0-100)
- 🔄 Bloat analysis

### Drift Tracking (v0.4)
- 🔄 Historical snapshots
- 🔄 Drift detection vs baseline
- 🔄 Temporal analysis
- 🔄 Audit trail

### Enterprise (v1.0)
- 🔄 Interactive dashboard
- 🔄 Multi-project scanning
- 🔄 GitHub Actions integration
- 🔄 SBOM/CycloneDX export
- 🔄 Custom reporter plugins

## Architecture

```
Rust Core (Performance)          Python Layer (UX)
├─ pydep-parser                 ├─ CLI (Click)
├─ pydep-graph                  ├─ Reporters (JSON, HTML, SBOM)
├─ pydep-ast                    ├─ Visualization (D3.js)
├─ pydep-security               ├─ Git integration
└─ pydep-py (PyO3)              └─ Storage (SQLite)
```

**Why Rust?** Graph operations, dependency resolution, and code analysis are CPU-bound. We get 10-100x speedups on large projects.

**Why Python?** CLI flexibility, ecosystem integrations (GitPython, Pydantic), and reporting templates.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — Design decisions, storage schema, CI/CD strategy
- [Roadmap](docs/ROADMAP.md) — Feature phases, timeline, success metrics
- [CLI Reference](docs/CLI.md) — All commands and options
- [Contributing](CONTRIBUTING.md) — Development setup, testing, releases

## Building from Source

```bash
# Requirements: Rust 1.75+, Python 3.8+

git clone https://github.com/Mullassery/pydependencycheck
cd pydependencycheck

# Build with maturin
pip install maturin
maturin develop --release

# Run tests
pytest tests/
cargo test --workspace
```

## License

MIT License — See [LICENSE](LICENSE) for details

## Support

- GitHub Issues: [Report bugs](https://github.com/Mullassery/pydependencycheck/issues)
- GitHub Discussions: [Ask questions](https://github.com/Mullassery/pydependencycheck/discussions)

---

**Status:** Alpha (v0.1.0) — Core dependency parsing and visualization. Vulnerabilities and drift tracking coming in v0.2-v0.3.
