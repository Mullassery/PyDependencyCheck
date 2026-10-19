# Limitations

This page states what PyDependencyCheck does **not** do. Read it before relying
on a green result.

## Scope of scanning

- **Manifest-based, not environment-based.** The scanner reads
  `requirements.txt`, `pyproject.toml` (PEP 621 and Poetry), `constraints.txt`,
  `setup.py`, and `setup.cfg`. It does not audit an installed virtual
  environment the way `pip-audit` does. `scan` reports declared dependencies;
  in the repository's own `test_project/` it reports `Transitive: 0`.
- **Lockfiles are discovered but not parsed (verified 2026-10-19).**
  `poetry.lock`, `uv.lock`, `Pipfile`, and `Pipfile.lock` are found by the
  scanner, but `_parse_file` logs `Unsupported file type` and they contribute
  **zero** dependencies. A scan of a project with only lockfiles reports
  `Total dependencies: 0`. Use the manifest (`pyproject.toml`,
  `requirements.txt`) as the source until lockfile parsing ships.
- **Transitive resolution depends on context.** A clean scan does not prove the
  full installed graph is clean. Use a lockfile-aware or environment-aware tool
  if you need the resolved graph.
- **No multi-ecosystem or container scanning.** This tool is Python-specific.
  For containers or multi-language repositories, use a dedicated scanner
  (for example OSV-Scanner or Syft/Grype).
- **Dynamic `setup.py` metadata is not executed.** Static `install_requires`
  and `extras_require` are parsed (verified in v1.5.0); calls such as
  `install_requires=read_requirements()` are reported as warnings rather than
  silently treated as "no dependencies".

## Vulnerability matching

- **No reachability analysis.** OSV advisories are matched to declared
  versions; the tool cannot tell whether a vulnerable code path is actually
  used. Expect noise and triage with VEX.
- **PEP 440 edge cases.** Versions with `.postN`, `.devN`, local-version
  suffixes, or four or more numeric components may fall back to exact-string
  matching rather than range matching. See `ROADMAP_HONEST.md` for the tracked
  gap.
- **Offline mode does not check vulnerabilities.** `--offline` skips OSV and
  PyPI, so the resulting health score is a local hygiene score only.

## Remediation

- **Exact pins only.** `remediate` updates `==` pins to the OSV fixed version.
  Version ranges are not rewritten. Review the printed diff before using
  `--apply`.
- **`--pr` requires `git` and (optionally) an authenticated `gh` CLI.** Without
  `gh` it can still create a branch and commit, but cannot open a PR.

## Provenance

- Requires a Git repository and sufficient history; shallow clones limit
  results.
- Evidence is the blamed manifest line, not a package-manager transaction log.
- See [Provenance](provenance.md).

## SBOM / VEX

- SBOMs describe declared dependencies, not embedded files or container layers.
- `--sign` requires the `sbom` extra (`cryptography`); without it, signing is
  skipped with a warning.
- VEX default state is `under_investigation`; the tool does not claim
  `not_affected` without evidence. See [VEX](vex.md).

## Maturity

- **Beta (v1.5.0).** The CLI can change between minor releases.
- Single maintainer; no formal security SLA. See `SECURITY.md`.
- No official GitHub Action or SARIF output yet; `gate` is designed to run as a
  step.

## Naming

PyDependencyCheck is **not** affiliated with OWASP Dependency-Check, and it is
**not** PyDeepMesh. See [Alternatives](alternatives.md) for the comparison.
