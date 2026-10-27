# Troubleshooting

## Installation

### No wheel for my platform

Check the [PyPI files for your version](https://pypi.org/project/pydependencycheck/#files).
If no wheel matches, build from source:

```bash
pip install maturin
git clone ../PyDependencyCheck
cd PyDependencyCheck
maturin build --release
pip install target/wheels/pydependencycheck-*.whl
```

You need a Rust toolchain (1.75+) and Python headers. See
[Compatibility](compatibility.md) and [`.github/INSTALL.md`](../.github/INSTALL.md).

### `ModuleNotFoundError: pydependencycheck._pydependencycheck`

The compiled extension is missing or was built for another Python/architecture.
Reinstall the wheel, or run `maturin develop --release` in a virtualenv.

### Version mismatch after a source checkout

`__version__` comes from installed package metadata. If you edited
`pyproject.toml`, reinstall (`pip install -e .` or `maturin develop`) so the
metadata matches.

## Runtime

### OSV/PyPI requests time out

The tool queries OSV.dev and PyPI. Check network/proxy access. For a local-only
run, use `health --offline` or `gate --offline`, but remember that offline mode
does **not** check vulnerabilities.

### `why`/`trace` show no history

Check that the project is a Git repository and that history is not shallow
(`git rev-parse --is-shallow-repository`). Re-clone with full history if needed.

### `--sign` produced no signatures

Install the `sbom` extra (`pip install "pydependencycheck[sbom]"`) and confirm
`cryptography` imports. Signing is skipped with a warning when it is absent.

### `Unsupported file type: poetry.lock` (or `uv.lock`, `Pipfile`)

Known limitation in v1.5.0: lockfiles are discovered but not parsed. Use
`pyproject.toml`/`requirements.txt` as the scanned source. See
[Limitations](limitations.md).

### `gate` fails unexpectedly

`gate` fails on critical vulnerabilities, health below 50, health below
`--min-health`, or too many unused dependencies. Run `pydependencycheck health`
first and tune thresholds. See [CI gating](ci-gating.md).

### `export --sign` fails to load the key

The key must be an unencrypted PEM RSA private key. `--sign` also requires
`--key`. See [SBOM](sbom.md).

## Getting help

- Check [FAQ](faq.md) and [Limitations](limitations.md).
- Open an issue at <../PyDependencyCheck/issues>.
- For security issues, follow `SECURITY.md` (do not open a public issue).
