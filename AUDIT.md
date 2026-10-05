# Repository Audit — PyDependencyCheck

## Health

**GREEN.** This repo was already in unusually good shape before this pass
started — a prior "OSS maturity pass" (2026-09) had already added
CHANGELOG.md, SECURITY.md, CODE_OF_CONDUCT.md, dependabot.yml, a security-audit
CI job, and an honest ROADMAP_HONEST.md documenting real limitations. This
pass fast-forwarded onto that work (3 commits, including two real bug fixes
found via benchmarking against pallets/flask) and then focused on dependency
security and a verified-live CI gap.

## Before Audit (this pass's baseline, after fast-forward to `3fe7ec8`)

Open debt: 10
Critical: 0 · High: 1 · Medium: 7 · Low: 2

## After Audit

Open debt: 5
Critical: 0 · High: 1 (TD-0001, PyPI secret missing — needs human/repo-settings access) · Medium: 2 (TD-0005 ring/cc conflict, TD-0007 untested fallback module) · Low: 0 (TD-0010 verified resolved — artifacts were already correctly gitignored)

## Items Fixed

1. **TD-0002** — 6 of 7 `cargo audit` findings resolved: bumped `reqwest` 0.11→0.12 and `pyo3` 0.21→0.29, pulling current `rustls`/`h2`/`rustls-webpki` and resolving a real buffer-overflow CVE in pyo3.
2. **TD-0003** — Fixed the pyo3 0.29 API break (`PyModule::new_bound`→`new`) at all 4 call sites in `crates/pydep-py/src/lib.rs`. This was independently confirmed live as the exact cause of a currently-failing Dependabot PR (`dependabot/cargo/pyo3-0.29.3`).
3. **TD-0004** — Silenced 2 pyo3 0.29 deprecation warnings (`#[pyclass(skip_from_py_object)]`) after confirming via grep neither affected type is ever extracted from Python.
4. **TD-0006** — Fixed 7 ruff lint errors and reformatted 2 files with black (recurring formatting-drift pattern, previously only partially addressed by pinning black's version).

## Items Remaining

- **TD-0001** (P1) — PyPI publish CI job will fail on first tag push; no `PYPI_API_TOKEN` secret exists (confirmed via `gh secret list`). Needs repo-settings access this pass doesn't have.
- **TD-0005** (P2) — 1 residual `cargo-audit` finding (`ring` AES overflow-check panic, debug-build-only). `cargo update` hits a resolver conflict with `cc`; needs a dedicated dependency-update session, not a quick pin.
- **TD-0007** (P2) — `vulnerabilities.py`, an honestly-labeled but shipped, 0%-covered fallback module.
- **TD-0008** (P3, grouped under P2 in the register) — Several modules under 60% test coverage (`git_integration.py` 20%, `dashboard.py` 35%, others).
- **TD-0010** (P3) — Stray dev artifacts in the working tree, not verified as git-tracked.

## Future Phase Work

`setup.py`/`setup.cfg` parsing (TD-0009) — already honestly documented as a TODO stub in README.md/ROADMAP_HONEST.md prior to this pass; verified still accurate, no change needed.

## CI Status

All 3 workflows (`ci.yml`, `security-audit.yml`, `wheels.yml`) pass `actionlint` clean. Build-and-test matrix (Linux/macOS×2/Windows) green on `main`. Publish job untested in practice (no tag ever pushed) and will fail as-is (TD-0001).

## Test Status

Rust: 46/46 passing across 4 crates. Python: 154/154 passing, re-verified against the actual freshly-built `maturin` wheel (not just `cargo test`) after the dependency bumps — confirms the pyo3/reqwest upgrade didn't break runtime behavior, only fixed the compile-time API break. Coverage 64% overall, with real gaps (see Items Remaining).

## Build Status

`cargo clippy --workspace --all-targets`: 0 warnings (was 2 before this pass). `maturin build --release`: succeeds, produces a working abi3 wheel verified by reinstalling it and rerunning the full pytest suite against it.

## Security Status

7 of 8 `cargo-audit` findings resolved (6 errors + the pyo3 CVE; 1 low-impact advisory remains, documented). `SECURITY.md` (prior pass) not re-audited for content in this pass.

## Dependency Status

`reqwest` and `pyo3` both bumped to current major versions with zero downstream code breakage beyond the 4 expected pyo3 API-rename sites. 13 Dependabot branches exist; only the one blocking on a real compile error (pyo3) was triaged and fixed here.

## Final Assessment

This repo arrived already well-audited; this pass's genuine contribution is closing a real security gap (pyo3 buffer-overflow CVE + 6 other `cargo-audit` findings) that required fixing a live, currently-failing compile error — not just bumping a version number — and confirming with hard evidence (`gh secret list`, `gh run list`) that the previously-suspected PyPI publish gap is real and still open. Version bumped to 1.4.1 for this release; PyPI publish intentionally left to the coordinator to handle directly.
