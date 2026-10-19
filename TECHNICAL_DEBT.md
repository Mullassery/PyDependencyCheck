# Complete Technical Debt Register — PyDependencyCheck

## Executive Summary

Total items: 10
Open: 5 · Resolved (this pass): 5 · Future/Deferred: 1
Critical: 0 · High: 1 · Medium: 5 · Low: 4

This repo already had an unusually thorough prior audit (the 2026-09 "OSS
maturity pass": CHANGELOG.md, SECURITY.md, CODE_OF_CONDUCT.md, dependabot.yml,
security-audit.yml, and an honest ROADMAP_HONEST.md already existed before
this pass started). This audit fast-forwarded onto that work first, then
focused on dependency security, lint drift, and verifying the known PyPI
publish gap from prior memory.

## P0 — Critical

None found.

## P1 — High

| ID | Category | Description | Source | Status | Fix |
|---|---|---|---|---|---|
| TD-0001 | CI_CD | PyPI publish job (`wheels.yml` `publish` job) referenced `secrets.PYPI_API_TOKEN`, but `gh secret list` confirmed **no secrets are configured on this repo at all**. The job has never actually run (only triggers on `refs/tags/v*`, and no version tag has ever been pushed), but it was guaranteed to fail the moment one was. | CI_FAILURE (verified live via `gh secret list` + `gh run list`) | **FIXED (workflow)** — migrated to PyPI Trusted Publishing (OIDC): the `publish` job now grants `id-token: write` and passes no `password`, so it no longer depends on an unconfigured repo secret. Remaining human step: register a Trusted Publisher for `Mullassery/PyDependencyCheck` (workflow `wheels.yml`, job `publish`) on PyPI — out of scope here (no PyPI-project-settings access). |

## P2 — Medium

| ID | Category | Description | Source | Status | Fix |
|---|---|---|---|---|---|
| TD-0002 | SECURITY, DEPENDENCY | `cargo audit`: 7 vulnerabilities across `h2` (RUSTSEC-2026-0258), `rustls-webpki`×3 (RUSTSEC-2026-0104/0098/0099), `pyo3` (RUSTSEC-2025-0020, buffer overflow), plus 1 unmaintained-crate warning (`rustls-pemfile`, RUSTSEC-2025-0134). | SOURCE_CODE (`cargo audit`) | **FIXED** this pass | Bumped `reqwest` 0.11→0.12 and `pyo3` 0.21→0.29. See CHANGELOG.md [1.4.1]. |
| TD-0003 | COMPATIBILITY | `pyo3` 0.29 removed the `_bound`-suffixed APIs (`PyModule::new_bound`); 4 call sites in `crates/pydep-py/src/lib.rs` failed to compile. This was also the live cause of a currently-failing Dependabot PR (`dependabot/cargo/pyo3-0.29.3`, run `37265564380`, confirmed failing 2026-10-05). | CI_FAILURE (verified live) | **FIXED** this pass | Renamed to `PyModule::new`. Dependabot PR should now be mergeable/closeable as redundant. |
| TD-0004 | DEPRECATION | Two `#[pyclass]` structs (`PySeverity`, `Vulnerability` in `crates/pydep-py/src/security.rs`) triggered pyo3 0.29 deprecation warnings for auto-derived `FromPyObject` on `Clone` types. | SOURCE_CODE | **FIXED** this pass | Added `#[pyclass(skip_from_py_object)]` — verified via grep that neither type is ever extracted from a Python argument, only constructed in Rust and returned. |
| TD-0005 | SECURITY, DEPENDENCY | `ring` 0.17.9 (RUSTSEC-2025-0009, AES overflow-check panic — debug-build-only impact, needs `overflow-checks=true` which release profiles don't set). `cargo update -p ring --precise 0.17.14` fails: resolver reports a conflict with `cc`'s locked version despite `ring 0.17.14` nominally satisfying rustls's `^0.17` requirement. | SOURCE_CODE (`cargo audit` + `cargo update` dry-run, verified live) | OPEN | Needs a wider, careful `cargo update` (or `cargo update --aggressive`) session with full re-test, not a one-line pin — deferred to avoid destabilizing the lockfile in this pass. |
| TD-0006 | LINT, DEVEX | 7 ruff errors (5 import-sort, 2 `F841` unused-variable from the `cryptography = pytest.importorskip(...)` idiom) + 2 files failing `black --check` (`scanner.py`, `tests/test_scanner.py`). Same recurring formatting-drift pattern the OSS maturity pass already flagged once (commit `ecf6207`: "pin black version to stop recurring formatting drift"). | SOURCE_CODE | **FIXED** this pass | `ruff check --fix` + manual fix of the 2 `F841`s (drop the unused assignment, call `pytest.importorskip` for its side effect only) + `black` reformat. Recurrence suggests pre-commit hooks for black/ruff aren't actually enforced locally — architecture/DevEx gap, not re-fixed here. |
| TD-0007 | TEST_DEBT | `python/pydependencycheck/vulnerabilities.py` — 0% test coverage (123 statements). Confirmed via grep this module is **not dead code accidentally** — it's an honestly-labeled, intentionally-unused pure-Python OSV fallback (its own docstring says so), superseded by the faster Rust `pydep-security` path. Still: zero coverage on a module that ships in the package and is part of the public API surface. | TEST_FAILURE (coverage report) | OPEN | Either add minimal tests for the fallback path, or move it to an `extras`/example rather than shipping untested in the main package — product decision, not fixed here. |
| TD-0008 | TEST_DEBT | Several modules under 60% coverage: `git_integration.py` 20%, `dashboard.py` 35%, `telemetry.py` 58%, `cli.py` 60%, `scanner.py` 59%. | TEST_FAILURE (coverage report) | OPEN | Needs dedicated test-writing session per module; not attempted here to avoid a rushed, low-value coverage-padding pass. |

## P3 — Low

| ID | Category | Description | Source | Status | Fix |
|---|---|---|---|---|---|
| TD-0009 | PARSER, ROADMAP | `setup.py`/`setup.cfg` static parsing. | VERIFIED (fixture with `setup.py` + `setup.cfg`, 2026-10-19; 5 dependencies detected) | **RESOLVED in v1.5.0** | Static `install_requires`/`extras_require` parsing shipped (Rust parser + Python AST/configparser fallback). Dynamic metadata (e.g. `read_requirements()`) is intentionally not executed and warns. |
| TD-0010 | ARCHITECTURE | Root directory has local dev artifacts (`.coverage`, `dist/`, `target/`, `venv/`). | INFERRED, **VERIFIED RESOLVED** | RESOLVED | Confirmed via `git add -A` + `.gitignore`: all are correctly gitignored, not tracked in git. No action needed. |

## Explicit TODOs

None remaining for TD-0009; the former TODO comments were removed when static
`setup.py`/`setup.cfg` parsing shipped in v1.5.0.

## Stubs

None for `setup.py`/`setup.cfg` (TD-0009 resolved in v1.5.0).

## Resolved Historical Issues (from prior passes, verified still fixed)

- License classifier mismatch (Proprietary vs Apache-2.0) — fixed in prior OSS maturity pass, verified still correct.
- Codecov upload with no `coverage.xml` generated — fixed in prior pass, verified `--cov-report=xml` present in `ci.yml`.
- Black version pinning to stop formatting drift (`ecf6207`) — the pin exists, but formatting drift recurred anyway (TD-0006), suggesting the pin alone doesn't prevent drift without an enforced pre-commit hook.

## CI/CD Debt

- TD-0001 (PyPI publish secret missing — HIGH; workflow migrated to OIDC Trusted Publishing, only the PyPI-side publisher registration remains)
- `actionlint` run clean across all 3 workflow files (`ci.yml`, `security-audit.yml`, `wheels.yml`) — no syntax/schema issues.
- `wheels.yml` has a documented, reasonable workaround for macOS runner capacity issues (cross-compiling the Intel wheel from Apple Silicon) — not debt, good practice already in place.

## Test Debt

TD-0007, TD-0008 (see P2/P3 tables above). Rust side: 46/46 tests passing across all 4 crates with sub-second runtime — no Rust test debt found.

## Dependency Debt

TD-0002 (fixed), TD-0005 (open, ring/cc resolver conflict). 13 Dependabot branches were not individually triaged in this pass beyond the pyo3 one (TD-0003) that was blocking on a real compile error.

## Security Debt

TD-0002 (fixed, 6 of 7 cargo-audit findings), TD-0005 (open, 1 remaining). `SECURITY.md` already exists from the prior pass with a real vulnerability-reporting process — not re-audited for content accuracy in this pass.

## Architecture Debt

TD-0010 (stray dev artifacts, low priority, unverified).

## Performance Debt

None found in this pass — not deeply profiled; this audit focused on correctness/security/CI given time constraints.

## Documentation Debt

The v1.5.0 documentation refresh added `docs/` (quickstart, provenance,
health-score, ci-gating, sbom, vex, commands, compatibility, limitations,
alternatives) and corrected stale claims in README/SECURITY. Remaining gap:
`docs/commands.md` is maintained by hand and should be generated from `--help`
once the CLI surface stabilizes.
