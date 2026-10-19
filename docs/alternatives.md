# Alternatives and how PyDependencyCheck compares

This page is written problem-first. It is **not** a benchmark, and it does not
claim that one tool is "best". Every competitor fact below was taken from the
vendor/project's official documentation on **2026-10-19**; features change, so
re-check before relying on a row.

Sources:

- OWASP Dependency-Check — <https://owasp.org/www-project-dependency-check/>
- pip-audit — <https://github.com/pypa/pip-audit>
- deptry — <https://github.com/osprey-oss/deptry>
- OSV-Scanner — <https://github.com/google/osv-scanner>
- Syft — <https://github.com/anchore/syft>
- Dependabot alerts — <https://docs.github.com/en/code-security/dependabot/dependabot-alerts/about-dependabot-alerts>

## Pick by problem

| Your problem | Start with | Why |
|---|---|---|
| "Which Python packages have known CVEs?" | pip-audit or OSV-Scanner | Mature, widely used, environment/lockfile aware |
| "Which dependencies are unused or missing?" | deptry | Focused, fast, MIT |
| "Why is this dependency here and who added it?" | **PyDependencyCheck** | `why` / `trace` reconstruct Git provenance |
| "Signed SBOM + VEX for an audit" | **PyDependencyCheck** or Syft | PyDependencyCheck adds Python-specific provenance and VEX; Syft covers containers |
| "Multi-language/container scanning" | OSV-Scanner or Syft/Grype | Not supported by PyDependencyCheck |
| "Zero-config GitHub alerts and updates" | Dependabot | GitHub-native |
| "One health number to gate merges" | **PyDependencyCheck** | Weighted score + `gate` annotations |

## Feature comparison (verified columns only)

Legend: ✅ stated in reviewed official docs · — not stated (not proof of
absence) · ❌ out of scope/verified absent.

| Capability | PyDependencyCheck | pip-audit | deptry | OWASP DC | OSV-Scanner | Syft | Dependabot |
|---|---|---|---|---|---|---|---|
| Python vulnerability scan | ✅ | ✅ | — | ✅ | ✅ | — | ✅ |
| Unused/missing dependencies | ✅ | — | ✅ | — | — | — | — |
| Git provenance (`why`/who) | ✅ | — | — | — | — | — | — |
| License compliance | ✅ | — | — | — | ✅ | SBOM data | — |
| SBOM export | ✅ CDX 1.4 / SPDX 2.3 | ✅ CDX | — | — | — | ✅ CDX/SPDX | — |
| Signed SBOM | ✅ RSA-SHA256 | — | — | — | — | ✅ in-toto | — |
| VEX export | ✅ CDX 1.6 | — | — | — | — | — | — |
| Guided remediation | ✅ exact pins | ✅ `--fix` | — | — | ✅ experimental | — | ✅ updates |
| CI annotations | ✅ GH Actions | via Action | — | ✅ | ✅ | — | ✅ |
| GitHub Action | ❌ (planned) | ✅ | — | ✅ | ✅ | — | n/a |
| Multi-ecosystem / containers | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| License | Apache-2.0 | Apache-2.0 | MIT | Apache-2.0 | Apache-2.0 | Apache-2.0 | GitHub service |

## Why not just pip-audit?

pip-audit is excellent at vulnerability auditing of environments and
requirements files and has an official GitHub Action. PyDependencyCheck does
not replace it. The difference is the question: pip-audit answers "is this
installed/declared package vulnerable?", while PyDependencyCheck additionally
answers "why is it here, who added it, is it used, and how healthy is the
dependency set?" — and can emit a signed SBOM/VEX and a health gate.

## Why not OWASP Dependency-Check?

OWASP Dependency-Check is a multi-language SCA flagship with broad build-tool
integrations. PyDependencyCheck is a Python-focused CLI. The names are similar,
but the projects are unrelated. If you need Java/.NET/container coverage via
NVD/CPE, OWASP Dependency-Check is the broader tool.

## Why not deptry?

deptry is the leaner, MIT-licensed choice if you only want unused/missing
dependency detection. PyDependencyCheck includes unused detection as one of four
health factors, alongside vulnerabilities, staleness, and provenance.

## Why not OSV-Scanner / Syft?

Use them when you need multi-ecosystem, container, lockfile, or offline-database
scanning. Use PyDependencyCheck when you need Python-specific provenance,
signed SBOM/VEX, and a CI health gate without a separate platform.

## What PyDependencyCheck does not do

See [Limitations](limitations.md): no reachability, no multi-language/container
scanning, exact-pin-only remediation, manifest-based scope.
