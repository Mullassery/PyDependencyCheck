# Competitive intelligence in roadmap and upgrade work

**Policy date:** 2026-10-19

Competitive findings are an input to product decisions, not a one-off report.
Every pending roadmap item, new feature, and routine dependency upgrade should
check the repository's [`AUDIT_FINDINGS.md`](AUDIT_FINDINGS.md) before work
starts, and record the decision in the PR or changelog.

## Required check before building

1. **Read `AUDIT_FINDINGS.md`.** Find the relevant competitor row and the
   ranked next actions. If the finding is stale, update it with a dated source.
2. **Name the competitor and the user problem.** A feature is not justified by
   "competitor has it". State the workflow it unlocks, who needs it, and how
   often. Mark unverified demand as a hypothesis.
3. **Prefer reuse over new code.** Check whether an existing Mullassery repo
   already provides the capability (see `BUNDLES.md` in the profile repo and
   the bundle role file in this repo, when present). Typical reuse:
   - crawling/fetching/robots/SSRF → **MudFish**
   - architecture maps / PR diffs → **CodeAtlas**
   - data-quality contracts / validation → **StatGuardian**
   - token counting / cost tables → **PyTokenCalc**
   - dependency graph / advisories / SBOM → **PyDeepMesh**
   - segmentation / CLV / churn → **ClusterAudienceKit**
   - activation / lineage / PII → **PyReverseETL**
   - fleet state sync → **SyncFleet** (only after conflict resolution)
4. **Choose one disposition:** build, integrate, defer, or reject. Write it
   down. A rejection with a reason is a successful outcome.
5. **For routine upgrades**, check whether the upgrade closes a known
   competitor gap or breaks a differentiated capability. Run the tests that
   cover the affected path; do not merge a green build that silently changes a
   user-visible contract.

## PR / changelog checklist

- [ ] Competitor and source URL/date recorded (or "no direct competitor").
- [ ] User impact and frequency stated; unverified demand labelled.
- [ ] Reuse check done against sibling repos/bundles.
- [ ] Failure mode and rollback considered (especially auth, PII, cost).
- [ ] Docs/roadmap status updated honestly.
- [ ] Tests or a manual verification command included.

## Review cadence

- Refresh the competitor row when a release changes the capability.
- Re-check the full `AUDIT_FINDINGS.md` at least quarterly and before a major
  release.
- If a finding is wrong or stale, correct it in the same PR that relies on it.

## Non-goals

- Copying features for parity.
- Adding a dependency just because a competitor uses it.
- Treating star counts or download counts as proof of user need.

## OSS gap analysis — 2026-10-24

Scope: PyDependencyCheck assessed against four maintained Python/supply-chain tools on manifest and lockfile coverage, environment auditing, advisory sources, unused-dependency detection, SBOM/VEX output, remediation, and CI gating. Multi-language scanning was assessed only to locate the boundary with PyDeepMesh and OWASP Dependency-Check.

### Comparable OSS projects

| Project | GitHub | License | Last activity | Why it is the comparison |
| --- | --- | --- | --- | --- |
| pip-audit | https://github.com/pypa/pip-audit | Apache-2.0 | v2.10.1, 2026-06-10 | Python vulnerability auditing of environments and requirements, with official Action and `--fix`; the direct overlap. |
| deptry | https://github.com/osprey-oss/deptry | MIT | 0.25.1, 2026-03-18 | The reference unused/missing/transitive dependency checker for Python; our closest hygiene competitor. |
| OWASP Dependency-Check | https://github.com/dependency-check/DependencyCheck | Apache-2.0 | v13.0.0, 2026-08-03 | Multi-language SCA using NVD/CPE with suppression files and SARIF; the governance comparison users name. |
| Syft | https://github.com/anchore/syft | Apache-2.0 | v1.55.0, 2026-10-19 | SBOM generation standard across filesystems and images; the benchmark for SBOM breadth and signing. |

### Capability comparison

| Capability | Ours | pip-audit | deptry | OWASP DC | Syft | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| Manifest and lockfile coverage | Partial | Partial | Partial | Yes | Yes | Large |
| Installed-environment audit | No | Yes | No | Partial | Yes | Large |
| Multiple advisory sources | Partial | Yes | No | Yes | No | Medium |
| Transitive dependency visibility | Partial | Yes | Yes | Yes | Partial | Medium |
| Unused/missing detection | Yes | No | Yes | No | No | Small |
| Git provenance (`why`/`trace`) | Yes | No | No | No | No | Ahead |
| License compliance | Yes | No | No | No | Yes | Small |
| CycloneDX/SPDX SBOM | Yes | Partial | No | No | Yes | Small |
| Signed SBOM | Yes | No | No | No | Yes | Ahead |
| CycloneDX VEX | Yes | No | No | No | No | Ahead |
| Automated remediation | Partial | Yes | No | No | No | Medium |
| SARIF output | No | No | No | Yes | No | Medium |
| CI annotations/gating | Yes | Yes | Yes | Yes | No | None |
| Aggregate health score | Yes | No | No | No | No | Ahead |
| Multi-ecosystem source scanning | No | No | No | Yes | Yes | Large |
| Container image scanning | No | No | No | No | Yes | Large |
| Offline/snapshot operation | Partial | No | Yes | Yes | Yes | Medium |

Nuance: our "manifest coverage" is requirements/constraints, PEP 621 and Poetry pyproject, and static setup.py/setup.cfg; `poetry.lock`, `uv.lock`, and `Pipfile.lock` are discovered but not parsed, so lockfile-only projects report zero dependencies. pip-audit audits installed environments and project/requirements resolution but does not parse every Python lockfile format. deptry is static and needs no network but does not scan for vulnerabilities. OWASP Dependency-Check's CLI output formats are HTML, XML, CSV, JSON, JUnit, SARIF, Jenkins, and GitLab, not SBOM. Syft catalogs and signs but delegates vulnerability matching to Grype; OWASP Dependency-Check scans source/build artifacts, not container images, and the table marks container image scanning accordingly. Our "offline" is a 7-day on-disk OSV cache, not a distributable snapshot.

### Gaps that matter (ranked)

1. **Lockfiles and installed environments are not audited** — `poetry.lock`, `uv.lock`, and `Pipfile.lock` are discovered but skipped, and a deployed virtualenv cannot be scanned. Users in modern uv/Poetry workflows get a false "0 dependencies" result; pip-audit covers environments and project resolution. S/M effort and the highest-priority correctness gap.
2. **Advisory breadth and offline trust** — we query OSV only, while pip-audit offers PyPI/OSV/ESMS and OWASP Dependency-Check maintains a local NVD database plus optional OSS Index. A 7-day cache can serve stale results to an offline `gate` with no explicit freshness state. M effort behind the existing OSV module.
3. **Remediation stops at exact `==` pins** — ranges, compatible releases, and lockfile-resolved versions produce no patch, and there is no conflict-aware upgrade path. pip-audit's `--fix` resolves and installs; ours is safe but narrow. M effort; preserve the dry-run default.
4. **Unused detection is a weaker version of deptry** — our AST import scan lacks deptry's configurable per-rule ignores, dependency-group handling, and Poetry/PDM/uv/notebook coverage. False positives erode trust in the health score. M effort.
5. **No SARIF and no official GitHub Action** — we emit GitHub annotations and a non-zero `gate`, but SARIF is absent and the Action is still planned. Security teams standardize on SARIF upload; competitors ship it. S effort.
6. **Wheel and Python-version coverage blocks adoption** — Linux/Windows users may need a Rust toolchain, and CI tests only Python 3.11 despite declaring 3.8+. A missing wheel is a harder failure than a missing feature. S/M effort.

### Where we are differentiated

- `why`/`trace` reconstruct real Git provenance — who introduced a dependency, when, and in which commit — which no compared tool does.
- Signed CycloneDX/SPDX SBOM plus CycloneDX 1.6 VEX, health scoring, and a CI gate in one Python-native CLI.
- A single workflow combines vulnerability findings, unused dependencies, license compatibility, and freshness into one score, where pip-audit and deptry are deliberately single-purpose.
- VEX defaults to `under_investigation` rather than asserting `not_affected` without runtime evidence.

### Disposition

- **Build:** lockfile parsers and installed-environment auditing; SARIF plus an official GitHub Action; additional advisory providers and a versioned offline snapshot; range-aware, conflict-checking remediation.
- **Integrate/reuse:** use PyDeepMesh as the multi-ecosystem advisory/graph engine instead of duplicating it; reuse its OSV provider and CycloneDX validation; keep provenance/signing here.
- **Defer/reject:** multi-ecosystem and container scanning, full runtime reachability, and automatic rewriting of version ranges without a resolver. Do not claim parity with OWASP Dependency-Check's NVD/CPE coverage.

### Sources

- https://github.com/pypa/pip-audit and its README CLI reference (accessed 2026-10-24)
- https://github.com/osprey-oss/deptry and https://deptry.com/ (accessed 2026-10-24)
- https://github.com/dependency-check/DependencyCheck and https://dependency-check.github.io/DependencyCheck/dependency-check-cli/arguments.html (accessed 2026-10-24)
- https://github.com/anchore/syft (accessed 2026-10-24)
- Repo files inspected: `README.md`, `COMPETITIVE_INTELLIGENCE.md`, `AUDIT_FINDINGS.md`, `docs/status.md`, `docs/alternatives.md`, `docs/commands.md`, `Cargo.toml`, `pyproject.toml`, `crates/pydep-security/src/osv.rs`, `crates/pydep-security/src/cache.rs`, `python/pydependencycheck/remediate.py`
