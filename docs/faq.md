# FAQ

### Is this OWASP Dependency-Check?

No. The names are similar, but the projects are unrelated. OWASP
Dependency-Check is a multi-language SCA tool; PyDependencyCheck is a
Python-specific CLI focused on provenance, health, signed SBOMs/VEX, and CI
gating. See [Alternatives](alternatives.md).

### Is this pip-audit?

No. pip-audit audits Python environments/requirements for known
vulnerabilities. PyDependencyCheck also does that against OSV, but adds Git
provenance (`why`/`trace`), unused-dependency detection, license checks, signed
SBOM/VEX, and a health gate. They can be used together.

### Does it upload my code?

No. It sends package names/versions to OSV.dev and PyPI's JSON API. Source code
is not transmitted. Offline mode makes no network calls (but skips
vulnerability checks).

### Does it support Poetry / uv / Pipenv?

- `pyproject.toml` (PEP 621 and Poetry) is parsed.
- `requirements.txt` and `constraints.txt` are parsed.
- `setup.py` and `setup.cfg` static declarations are parsed.
- `poetry.lock`, `uv.lock`, `Pipfile`, and `Pipfile.lock` are **discovered but
  not parsed** in v1.5.0; they emit an `Unsupported file type` warning and
  contribute no dependencies. See [Limitations](limitations.md).

### Why does `scan` report zero transitive dependencies?

The scanner is manifest-based. It does not resolve the installed graph. See
[Limitations](limitations.md).

### Can it scan containers or non-Python projects?

No. Use OSV-Scanner, Syft/Grype, or OWASP Dependency-Check for those.

### Does `why` require Git?

Yes. Provenance is reconstructed from Git history. See
[Provenance](provenance.md).

### How do I sign an SBOM?

Install `pydependencycheck[sbom]`, generate an RSA key, and pass `--sign --key`.
See [SBOM](sbom.md) for the exact commands and verification snippet.

### Is it production-ready?

It is **beta (v1.5.0)**, maintained by one person, with no security SLA. The
core commands are implemented and tested, but the CLI may change between minor
releases. See [Limitations](limitations.md) and `SECURITY.md`.

### Why did `gate` fail?

It fails on any critical vulnerability, health below 50, health below
`--min-health`, or unused dependencies above `--max-dead-deps`. See
[CI gating](ci-gating.md).
