# Architecture

PyDependencyCheck is a Python CLI backed by a Rust core exposed through PyO3.
The Rust extension is `pydependencycheck._pydependencycheck`; the Python package
is `pydependencycheck`.

## Layers

```text
Python CLI / orchestration (python/pydependencycheck/)
        │
        ├── cli.py            Click commands, exit codes, annotations
        ├── scanner.py        File discovery, parsing orchestration
        ├── health.py         Health factors and score
        ├── git_integration.py Provenance (why/trace)
        ├── licenses.py       License classification
        ├── sbom.py           CycloneDX/SPDX generation + RSA signing
        ├── vex.py            CycloneDX VEX
        ├── remediate.py      Exact-pin patch generation
        ├── storage.py        SQLite snapshots/history
        ├── telemetry.py      Optional OpenTelemetry
        └── reporters.py      Table/JSON/Markdown/HTML output
        │
        ▼
PyO3 bindings (crates/pydep-py/src/lib.rs)
        │
        ├── pydep-parser     requirements/constraints/pyproject/setup parsing
        ├── pydep-graph      DAG construction, cycles, transitive closure
        ├── pydep-ast        tree-sitter import/usage/dead-code analysis
        └── pydep-security   OSV client, caching, CVSS/risk scoring
```

## Request flow (scan)

1. `scanner.py` discovers dependency files (skipping `.git`, virtualenvs, and
   build/cache directories).
2. Each file is routed to the Rust parser when supported; otherwise a Python
   fallback parses it. `setup.py`/`setup.cfg` fall back to AST/configparser
   when the Rust parser finds nothing.
3. Dependencies are merged and de-duplicated, retaining their source files.
4. `pydep-ast` analyzes imports to find unused dependencies.
5. `health.py` optionally queries OSV (vulnerabilities) and PyPI (staleness)
   and computes the weighted score.

## Where to add features

| Change | Location |
|---|---|
| New manifest format | `crates/pydep-parser` + `scanner.DEPENDENCY_FILES` |
| New output format | `reporters.py` / `sbom.py` |
| New health factor | `health.py` (adjust weights and tests) |
| New CI integration | `github_actions.py` / `cli.gate` |
| New optional dependency | `pyproject.toml` extras + guarded import + docs |

## Design constraints

- Rust core is optional at runtime: the Python package has fallbacks
  (`HAS_RUST_BACKEND`).
- Optional integrations must degrade with an actionable error, not crash.
- The tool must remain usable offline, with an explicit warning that
  vulnerability checks are skipped.

See [Contributing](../CONTRIBUTING.md) for build/test commands and
[Limitations](limitations.md) for current scope.
