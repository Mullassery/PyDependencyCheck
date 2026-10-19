# Compatibility

## Python

- Declared: **Python 3.8+** (`requires-python = ">=3.8"`).
- CI currently runs the Python test suite on **3.11 only**. Older versions are
  declared but not exercised in CI; report an issue if you hit a 3.8-specific
  problem.

## Platforms and wheels

Wheels are built with PyO3 `abi3-py38`, so a single wheel per platform works
across Python 3.8+.

**As of 2026-10-19**, PyPI release **1.5.0** contains:

| File | Platform |
|---|---|
| `pydependencycheck-1.5.0-cp38-abi3-macosx_11_0_arm64.whl` | macOS Apple Silicon |
| `pydependencycheck-1.5.0.tar.gz` | source distribution |

The wheel workflow is configured for Ubuntu x86_64, macOS arm64, macOS x86_64
(cross-compiled), and Windows x86_64, but a given release may not include every
platform. **Check the files on the PyPI release page before assuming a wheel
exists for your platform.**

If no wheel matches, build from source — see
[`.github/INSTALL.md`](../.github/INSTALL.md). You will need a Rust toolchain
(1.75+) and `maturin`.

## Interchange formats

| Artifact | Format | Spec version |
|---|---|---|
| CycloneDX SBOM | JSON | 1.4 |
| SPDX SBOM | JSON | 2.3 |
| VEX | CycloneDX JSON | 1.6 |

## Optional extras

| Extra | Provides | Used by |
|---|---|---|
| `sbom` | `cryptography` | `export --sign` |
| `otel` | OpenTelemetry API/SDK/exporters | `health --otel` |
| `visualization` | `plotly`, `matplotlib` | dashboard/plots |
| `dev` | pytest, coverage, black, ruff, mypy | contributing |
| `docs` | Sphinx | documentation builds |

Install extras together, for example:

```bash
pip install "pydependencycheck[sbom,otel]"
```

## Data sources and network

- OSV.dev for vulnerabilities.
- PyPI JSON API for release dates and license metadata.
- No source code is uploaded; requests contain package names/versions.

Offline mode (`health --offline`, `gate --offline`) makes no network calls but
does not check vulnerabilities.
