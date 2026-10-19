# PyDependencyCheck

Dependency intelligence and supply-chain security for Python projects. Scan dependencies, track provenance, detect unused packages, check licenses, generate signed SBOMs, and gate CI builds.

> **Not to be confused with [PyDeepMesh](https://github.com/Mullassery/PyDeepMesh):** PyDeepMesh builds repository dependency graphs and matches advisories across ecosystems; PyDependencyCheck explains *why* each Python dependency exists, who added it, and whether it is used.

## Which project do I need?

Part of the Mullassery open-source family. These tools have similar names — here is the short version of who does what:

| If you need to… | Use |
| --- | --- |
| Build a repository's dependency graph and match it against vulnerability advisories (Python, Rust, Node, containers) | [PyDeepMesh](https://github.com/Mullassery/PyDeepMesh) |
| Understand *why* a Python dependency exists, who added it, and whether it is actually used | [PyDependencyCheck](https://github.com/Mullassery/PyDependencyCheck) |
| Statically analyze a **dbt** project (risky tests, test blast radius, cost) | [PyDBTGuard](https://github.com/Mullassery/PyDBTGuard) |
| Statically analyze **Apache Beam / Dataflow** pipelines (cost, hot keys, reliability) | [PyBeamGuard](https://github.com/Mullassery/PyBeamGuard) |
| Validate **Airflow** DAGs and dbt runs | [PyAirflowTester](https://github.com/Mullassery/PyAirflowTester) |
| Simulate cascading-failure **blast radius** across infrastructure, data pipelines, and AI systems | [PyBlastRadius](https://github.com/Mullassery/PyBlastRadius) |
| Check the **quality of the data itself** at runtime (schema, drift, anomalies) | [StatGuardian](https://github.com/Mullassery/StatGuardian) |
| Discover **devices, services, and vulnerabilities on a network** | [PyNetworkIntel](https://github.com/Mullassery/PyNetworkIntel) |
| Discover and score **API security** risk (real traffic, agent/MCP, Cedar policy) | [PyAPICheck](https://github.com/Mullassery/PyAPICheck) |
| Trace and root-cause **AI agent** failures | [PyAgentHound](https://github.com/Mullassery/PyAgentHound) |
| Diagnose **RAG retrieval** failures | [PyVectorHound](https://github.com/Mullassery/PyVectorHound) |
| Orchestrate **local, dependency-aware tasks** (DAG scheduler + content-addressed cache) | [PyTaskWireCheck](https://github.com/Mullassery/PyTaskWireCheck) |

[Browse all projects →](https://github.com/Mullassery?tab=repositories)

## What it is

PyDependencyCheck helps you understand not just *what* you depend on, but *why* it's there and whether your dependency set is healthy. It combines dependency parsing, graph analysis, OSV vulnerability scanning, Git provenance, and licensing checks into a single CLI. A Rust core powers parsing, graph algorithms, and vulnerability lookups, wrapped in Python.

## Features / Highlights

- **CI gating**: `pydependencycheck gate --min-health` exits non-zero with GitHub Actions annotations when thresholds fail.
- **Provenance**: `why` and `trace` show who added/changed a dependency and full git history.
- **Vulnerability scanning**: Checks against OSV (Open Source Vulnerabilities) in real time.
- **Unused dependency detection**: AST-based detection of unused packages in your codebase.
- **License compliance**: Check dependencies against your project's license for compatibility.
- **Signed SBOMs**: Export CycloneDX or SPDX with RSA-SHA256 signatures.
- **Health scoring**: Aggregates vulnerabilities, staleness, dead dependencies, and complexity into a single score.
- **Multi-format output**: Tables, JSON, HTML, or Markdown for integration with CI/reporting.

## Who it's for / Use cases

- **CI/CD enforcement**: Block merges when dependency health drops below acceptable thresholds.
- **Security auditing**: Identify vulnerable packages and understand their impact.
- **Dependency hygiene**: Find and remove unused dependencies to reduce attack surface.
- **Compliance reporting**: Generate signed SBOMs and license reports for audits.
- **Open-source maintenance**: Track when dependencies were added and why.

## What it is not

- **Not pip-audit**: Shares vulnerability scanning but also includes provenance, unused detection, licensing, SBOM signing, and gating. These are different tools with overlapping features.
- **Limited file discovery**: Focuses on `requirements.txt`, `pyproject.toml`, `setup.py`, `setup.cfg`. Projects that don't use these or have complex multi-project setups may need careful path handling.
- **Exact-pin remediation**: `remediate` only updates exact `==` pins to OSV fix versions; version ranges are not modified.
- **Transitive scope varies**: The `scan`/`health` view is based on parsed manifest files and detected dependencies; installed transitive resolution depends on context.

## Project status

PyDependencyCheck is in beta (v1.4.2). Core features (scanning, provenance, health scoring, vulnerability checks, licensing, SBOM export, CI gating) are implemented. See [CHANGELOG.md](CHANGELOG.md) for recent fixes and updates.

## Installation

```bash
pip install pydependencycheck
```

Optional extras:

```bash
pip install "pydependencycheck[sbom,otel,visualization]"
```

Requires Python 3.8+. Prebuilt wheels available for Linux, macOS, and Windows.

## Quick start

```bash
# Scan current project
pydependencycheck scan

# Check health score
pydependencycheck health

# Find out why a package is installed
pydependencycheck why requests

# Trace full history of a dependency
pydependencycheck trace requests

# Check license compliance
pydependencycheck licenses --project-license MIT

# Export signed CycloneDX SBOM
pydependencycheck export --format cyclonedx --output sbom.json

# Gate CI build
pydependencycheck gate --min-health 50
```

## Commands

| Command | Purpose |
|---|---|
| `scan` | Parse manifests and show dependency overview |
| `list` | List all detected dependencies |
| `why <pkg>` | Show git blame provenance |
| `trace <pkg>` | Show current status and git history |
| `health` | Compute aggregate health score |
| `licenses` | License classification and compatibility |
| `analyze` | Deep graph analysis |
| `remediate` | Suggest/apply fixes for vulnerable exact pins |
| `export` | Export SBOM in CycloneDX/SPDX (optionally signed) |
| `gate` | CI gate with exit code and annotations |

## Known issues and deferred work

**Blocked / failed:**
- Merge with/define boundary vs PyDeepMesh; SARIF + Action.

**Rejected / deferred:**
- Duplicate multi-ecosystem scanning.

Full shipped/blocked/rejected detail: [`QUEUE_STATUS.md`](QUEUE_STATUS.md).

## Queue status

Shipped, blocked/failed, and rejected work for this repository is documented in
[`QUEUE_STATUS.md`](QUEUE_STATUS.md).

## Documentation

- [Installation notes](.github/INSTALL.md)
- [CI gating with GitHub Actions](docs/ci-gating.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
