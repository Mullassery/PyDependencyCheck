# PyDependencyCheck Roadmap

## Phase Overview

```
v0.1.0 ━━━━━━━ Core Parsing & Graph (4 weeks)
v0.2.0 ━━━━━━━ Usage Analysis & Licenses (4 weeks)
v0.3.0 ━━━━━━━ Security & Health Score (4 weeks)
v0.4.0 ━━━━━━━ Drift Tracking (4 weeks)
v1.0.0 ━━━━━━━ Enterprise Dashboard & Hardening (6+ weeks)
```

---

## Phase 1: Core MVP (v0.1.0) — 4 weeks
**Status:** 🟢 IN PROGRESS (Scaffolding complete)

### Features
-  Dependency parsing (requirements.txt, pyproject.toml, setup.py)
-  Dependency graph construction (petgraph DiGraph)
-  Git blame per dependency (who added it, when)
-  Interactive HTML report with D3.js
-  JSON export for CI/CD
-  Basic CLI (scan, list, why, trace, blame)

### Deliverables
| Component | Status | Effort | Owner |
|---|---|---|---|
| Parser crate (requirements, pyproject, setup) | 🟡 70% | 1.5 wks | TBD |
| Graph crate (DAG, cycles, transitive closure) | 🟡 50% | 1 wk | TBD |
| PyO3 bindings | 🟡 40% | 0.5 wks | TBD |
| CLI (Click commands) | 🟡 30% | 1 wk | TBD |
| HTML reporter (D3.js) | 🟢 0% | 0.5 wks | TBD |
| Git integration | 🟡 20% | 0.5 wks | TBD |
| Testing + CI/CD | 🟡 50% | 0.5 wks | TBD |

### Success Criteria
- Parse 100+ real Python projects without errors
- Generate dependency graph in <2s
- Git blame latency <100ms
- HTML reports are interactive and shareable
- CI passes on all platforms (Linux, macOS, Windows)

### Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| PyO3 version conflicts | Low | Medium | Pin exact PyO3 version; test matrix |
| petgraph insufficient | Low | High | Benchmark with 10k+ nodes; fallback plan |
| Tree-sitter Python grammar issues | Low | Medium | Validation against known imports |

---

## Phase 2: Usage Analysis & Licenses (v0.2.0) — 4 weeks
**Status:** 🟡 IN PROGRESS — import scanning + dead dependency detection shipped in v1.2.0

### Features
- ✅ Import scanning to detect what's actually used (`pydependencycheck/scanner.py::analyze_usage`,
  backed by `crates/pydep-py/src/ast.rs::scan_imports`). Note: this is regex-based line scanning
  (`crates/pydep-ast/src/imports.rs`), not tree-sitter — despite the module doc comment's original
  claim. Works for the common import forms (`import x`, `from x import y`, aliases, simple dynamic
  imports) but can miss import statements split across unusual multi-line formatting.
- ✅ Dead dependency detection (heuristic) — `find_dead_dependencies()`, confidence-tagged
  (High = never imported, Medium = imported exactly once). Delegates to the existing
  `UsageAnalysis::find_potential_dead_deps` heuristics in `pydep-ast/src/usage.rs`.
- 🔄 License detection from PyPI metadata
- 🔄 License compliance checking (MIT, GPL, etc.)
- 🔄 Removal impact analysis
- 🔄 Extended CLI (usage, unused, licenses, impact) — Python API exists (`analyze_usage`,
  `find_dead_dependencies`); no CLI subcommands wired to them yet.

### New CLI Commands
```bash
pydependencycheck usage --show-coverage
pydependencycheck unused --confidence high
pydependencycheck licenses --format html
pydependencycheck impact --remove pandas
```

### Key Questions Answered
- Which packages are never imported?
- What licenses are included? Are they compatible?
- What breaks if we remove Flask?
- What % of dependencies are actually used?

### Success Criteria
- Detect 95%+ of actual imports (validated against pip show)
- <10% false positives on dead packages
- Categorize 1000+ licenses correctly
- Impact analysis passes test cases

### Effort Estimate
- AST parsing (tree-sitter integration): 1.5 wks
- Lineage tracking: 1.5 wks
- License detection (PyPI JSON API): 0.5 wks
- Reporters + testing: 1 wk

---

## Phase 3: Security & Health Score (v0.3.0) — 4 weeks
**Status:** 🟡 IN PROGRESS — OSV live querying shipped in v1.1.0

### Features
- ✅ OSV integration — live api.osv.dev querying with real semver range matching
  (`crates/pydep-security/src/osv.rs`), exposed via `check_vulnerabilities()`.
  Offline weekly snapshot download (`osv-db.db`) not yet built — every query
  currently hits the live API (cached locally, see below).
- 🔄 Transitive vulnerability propagation
- 🔄 Health score (0-100): vulnerabilities, maintenance, bloat
- 🔄 Bloat score: dependency count, size
- 🔄 Vulnerability chains visualization
- 🔄 Performance profiling (which deps slow startup?)

### OSV Strategy
1. **Offline:** Download `osv-db.db` weekly (~50MB) — not yet implemented
2. **Local cache:** ~/.pydep/osv-cache/ (7-day TTL) — ✅ implemented
3. **Online fallback:** api.osv.dev (rate limited) — ✅ implemented as the primary path

### Health Score Formula
```
health_score = 100
              - (critical_vulns * 20)
              - (high_vulns * 10)
              - (stale_packages * 2)
              - (dead_deps * 1)
              - min(transitive_depth / 10, 5)  // max penalty 5
              - (bloat_score / 5)
```

### New CLI Commands
```bash
pydependencycheck health --report-json
pydependencycheck vuln --show-chains
pydependencycheck bloat --top 10
pydependencycheck perf --slow-startup
```

### Success Criteria
- Detect all public CVEs for top 100 packages
- Health score correlates with GitHub stars/activity
- Vulnerability propagation matches manual audit
- Bloat analysis identifies optimization targets

### Effort Estimate
- OSV client + caching: 1 wk
- Risk propagation algorithm: 1 wk
- Health score calculation: 0.5 wks
- Reporters + validation: 1.5 wks

---

## Phase 4: Drift Tracking & History (v0.4.0) — 4 weeks
**Status:** 🔴 NOT STARTED

### Features
- 🔄 Snapshot history (last 30 scans, archive older)
- 🔄 Drift detection (compare baseline vs current)
- 🔄 Temporal analysis (when was pkg X added/removed?)
- 🔄 Baseline configuration (.pydependencycheck.yaml)
- 🔄 Audit trail (correlate deps with features/bugs)
- 🔄 Alert policies (fail if health drops, deps added, etc.)

### Storage
- Snapshots: ~/.pydep/cache.db
- Baselines: .pydependencycheck.yaml (in project root)
- Archive: ~/.pydep/archive/ (monthly compressed)

### New CLI Commands
```bash
pydependencycheck snapshot save --as production
pydependencycheck snapshot diff production
pydependencycheck history pkg:flask
pydependencycheck monitor --baseline main  # CI mode
pydependencycheck drift --threshold 5
```

### Success Criteria
- Capture snapshot in <2s overhead
- Detect drift with zero false positives
- Query 1-year history in <100ms
- Alert policies integrate with GitHub Actions

### Effort Estimate
- SQLite migrations + ORM: 1 wk
- Snapshot comparison: 1 wk
- Drift detection: 0.5 wks
- Temporal queries: 0.5 wks
- Time-series visualization: 1 wk

---

## Phase 5: Enterprise & Hardening (v1.0.0) — 6+ weeks
**Status:** 🔴 NOT STARTED

### Features
- 🔄 Optional FastAPI dashboard
  - Project list + inventory
  - Vulnerability timeline
  - Health trends
  - Drift notifications
- 🔄 Multi-project orchestration
- 🔄 GitHub Actions integration (PR comments)
- 🔄 SBOM export (CycloneDX 1.4)
- 🔄 Custom reporter plugins
- 🔄 Performance optimization (parallel scanning)
- 🔄 Security hardening + penetration testing
- 🔄 Signed releases + SBOMs

### New CLI Commands
```bash
pydependencycheck server --port 8000
pydependencycheck scan-org --github-token XXX
pydependencycheck export --format cyclonedx --output sbom.json
pydependencycheck plugins list
```

### GitHub Actions Integration
```yaml
- name: PyDependencyCheck
  uses: Mullassery/pydependencycheck@v1
  with:
    baseline: main
    fail-on-drift: true
    fail-on-critical: true
```

### Success Criteria
- Dashboard loads in <3s for 1000 projects
- Parallel scan: 10 projects in <30s
- CycloneDX exports pass validation
- Security audit: zero critical findings
- 95%+ test coverage

### Effort Estimate
- FastAPI dashboard: 2 wks
- GitHub Actions workflow: 0.5 wks
- SBOM generation: 0.5 wks
- Plugin system: 0.5 wks
- Performance tuning: 1 wk
- Security audit: 1 wk
- Documentation + polish: 1 wk

---

## Milestones

| Milestone | Target | Deliverable |
|---|---|---|
| **v0.1.0 Alpha** | Week 4 | Core parsing + graph + blame |
| **v0.1.1 Beta** | Week 5 | Bug fixes, test coverage >80% |
| **v0.1.2 RC** | Week 6 | Final perf tuning, CI stability |
| **v0.1.0 Release** | Week 6 | PyPI wheels, documentation |
| **v0.2.0 Release** | Week 10 | Usage analysis + licenses |
| **v0.3.0 Release** | Week 14 | Security + health scores |
| **v0.4.0 Release** | Week 18 | Drift tracking |
| **v1.0.0 Release** | Week 24+ | Enterprise features |

---

## Known Limitations

### v0.1-v0.3
- No support for Pipfile, poetry.lock, uv.lock (v0.2)
- Dead code detection is heuristic (high false-positive risk)
- No semantic analysis (miss indirect imports)
- Single-machine scanning only

### Planned for v1.0+
- Distributed scanning
- ML-based dead code detection
- Default to fully offline: OTEL telemetry is already opt-in/local-only (`telemetry.py`, disabled by default, no remote exporter) so that critique item was already false, but OSV/PyPI vulnerability lookups (`crates/pydep-security/src/osv.rs`) hit live network APIs unless `--offline` is passed explicitly — consider flipping the default so "local-first" is true out of the box, not just via a flag.
- Supply chain attestation (SLSA)
- Private package registry support

**Done:** Automated PR remediation patches — `pydependencycheck remediate`
(`python/pydependencycheck/remediate.py`) now computes real patches from
OSV `fix_version` data, and with `--pr` creates a real git branch/commit,
pushes it, and opens a GitHub PR via the `gh` CLI when available. Fixing
this also surfaced and fixed a real, more severe pre-existing bug it
depended on: `check_vulnerabilities()` was passing the full PEP 508
specifier (`"==2.25.0"`) to OSV instead of the bare version, so OSV's
semver matching silently failed and `health`/`gate` reported zero
vulnerabilities for virtually every exactly-pinned dependency (see
README's Known Issues for detail).

---

## Success Metrics

| Metric | v0.1 | v0.3 | v1.0 |
|---|---|---|---|
| **Projects scanned** | 50+ real-world | 500+ | 5,000+ |
| **Parse accuracy** | 95%+ | 98%+ | 99%+ |
| **Performance (median)** | <5s | <10s | <30s (multi-project) |
| **Test coverage** | >70% | >85% | >95% |
| **Vulnerability detection** | - | CVE DB parity | Real-time OSV sync |
| **Enterprise adoptions** | 0 | 5-10 pilots | 50+ |

---

## Dependencies

- **Rust:** petgraph, tree-sitter, tokio, pyo3, serde
- **Python:** click, pydantic, gitpython, networkx, jinja2, rich, requests
- **CI/CD:** maturin, cibuildwheel, GitHub Actions
- **Data:** OSV database, PyPI JSON API

---

## Feedback & Changes

Submit feature requests and design discussions via:
- [GitHub Issues](https://github.com/Mullassery/pydependencycheck/issues)
- [GitHub Discussions](https://github.com/Mullassery/pydependencycheck/discussions)
