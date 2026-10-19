# Quickstart

Get from zero to a useful dependency report in about two minutes.

> All commands on this page were executed against the repository's
> `test_project/` on 2026-10-19. Output shown here is illustrative; your
> project's numbers will differ.

## 1. Install

```bash
pip install pydependencycheck
```

Check the install:

```bash
pydependencycheck --version
```

If no wheel is available for your platform/architecture, build from source —
see [Compatibility](compatibility.md) and the
[installation guide](../.github/INSTALL.md).

## 2. Scan the project

Run from the project root (the directory containing `pyproject.toml`,
`requirements.txt`, `setup.py`, or `setup.cfg`):

```bash
pydependencycheck scan
```

Example output:

```text
Total dependencies: 7
  Direct: 7
  Transitive: 0
```

Use `--path/-p` to scan another directory, and `--format/-f` for
`table` (default), `json`, `markdown`, or `html`.

## 3. Ask why a dependency exists

```bash
pydependencycheck why requests
```

Example output:

```text
requests
  Version: ==2.32.0
  Source: test_project/requirements.txt

Introduced by:
  Commit: 09fa4f3
  Author: Georgi Mammen Mullassery
  Date: 2026-08-03 01:55:27
  Message: Initial PyDependencyCheck scaffold: Rust core + Python CLI, 5-phase roadmap
```

`why` needs the project to be a Git repository. See
[Provenance](provenance.md) for the full workflow and its limits.

## 4. Show the health score

```bash
pydependencycheck health
```

The score combines four factors (weights in
[Health score](health-score.md)). Use `--offline` to skip OSV/PyPI network
calls; note that an offline run **does not check vulnerabilities**.

## 5. Gate CI

```bash
pydependencycheck gate --min-health 50 --max-dead-deps 10
```

Exit codes and annotation behaviour are documented in
[CI gating](ci-gating.md).

## 6. Produce an SBOM

```bash
# CycloneDX 1.4
pydependencycheck export --format cyclonedx --output sbom.cdx.json

# SPDX 2.3
pydependencycheck export --format spdx --output sbom.spdx.json
```

Signed SBOMs require the `sbom` extra; see [SBOM](sbom.md).

## 7. Next steps

- [Provenance](provenance.md) — `why` and `trace`
- [Health score](health-score.md) — how the number is computed
- [CI gating](ci-gating.md) — GitHub Actions example
- [SBOM](sbom.md) — signing and verification
- [VEX](vex.md) — CycloneDX VEX export
- [Limitations](limitations.md) — what this tool cannot see
- [Alternatives](alternatives.md) — how it compares to other tools
