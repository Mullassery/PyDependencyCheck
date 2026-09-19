# PyDependencyCheck — Honest Status

**Current Version:** v1.4.0 (matches the version live on PyPI — no drift)
**Last Updated:** 2026-09-20

This file exists to say plainly what's built-and-verified, what's built-but-unverified,
what's not built yet, and what's actively broken in CI/release infrastructure —
`README.md` documents the intended public API; this file is the "have we actually
verified this" companion, kept up front so future roadmap planning starts from reality
instead of from what the README merely claims.

## 🟢 Built & verified (real implementation, real test coverage)

- **Dependency parsing** — `requirements.txt`, `pyproject.toml` (PEP 621 + Poetry),
  `constraints.txt`; every PEP 508 version operator and extras (`crates/pydep-parser`).
- **Health scoring** — 4 real, independently-computed factors (vulnerabilities via
  OSV.dev, staleness via PyPI's JSON API, dead dependencies via AST import analysis,
  dependency-graph complexity).
- **`remediate`** — dry-run diff, `--apply` (writes real file changes, tested against a
  real tmp project), and `--pr` (creates a real git branch + commit against a real repo
  fixture, pushes to a real local bare remote, and invokes the actual `gh` binary via
  subprocess against a fake `gh` executable on `PATH` — not a mock of `subprocess.run`).
- **SBOM export** — CycloneDX 1.4 and SPDX 2.3, with RSA-SHA256 signing/verification.
- **License compliance** — real PyPI license metadata fetch, permissive/copyleft/
  restricted classification, compatibility check.
- **CI gating (`gate`)** — real GitHub Actions `::error`/`::warning`/`::notice`
  annotations, real non-zero exit code.
- **Drift/snapshot/history** — SQLite-backed, diffs against a saved baseline.
- **OpenTelemetry, console exporter** — genuine OTEL SDK spans/metrics to stdout,
  verified by tests that capture real console output in a fresh subprocess.
- **OSV vulnerability matching bug (fixed this release)** — `check_vulnerabilities()`
  was passing the full PEP 508 specifier (e.g. `"==2.25.0"`) to OSV.dev instead of the
  bare version, so `health`/`gate` silently reported zero vulnerabilities for
  essentially every exactly-pinned dependency. Fixed, with a regression test
  (`crates/pydep-security/src/osv.rs`).
- **46 Rust tests** (`cargo test --workspace`) — re-run 2026-09-20, all 46 pass,
  plus `cargo clippy --workspace -- -D warnings` and `cargo fmt --check` both clean.
- **153 Python tests** (`pytest tests/`) — re-run 2026-09-20 in a clean venv with
  `maturin develop --release`: **136 pass unconditionally; 17 skip** (all in
  `tests/test_telemetry.py`, gated by `pytest.mark.skipif(not HAS_OTEL, ...)`).
  Installing `opentelemetry-api`/`opentelemetry-sdk` and re-running gets all 153
  passing. `.github/workflows/ci.yml`'s `python-tests` job does **not** install
  those packages, so a real CI run reports "136 passed, 17 skipped" — the
  previous version of this doc said "153 passing" without that caveat, which
  overstated what CI actually verifies. Wheels build successfully for
  Linux/macOS (Intel+ARM)/Windows (macOS arm64 build re-verified 2026-09-20).

## 🟡 Built but not independently verified

- **OTLP/Jaeger/Prometheus OTEL exporters** — real code paths exist
  (`--otel-exporter otlp|jaeger|prometheus`), and the fallback-to-console behavior *when
  the exporter package is missing* is tested. But no test actually verifies data
  reaching a real OTLP collector/Jaeger/Prometheus backend — that would need real
  infrastructure in CI, which doesn't exist here. Treat these three as "should work,
  unverified end-to-end" rather than "confirmed."

## 🔴 Not built / not yet functional

- **`setup.py`/`setup.cfg`-only projects are not parsed.** Both AST parsing of
  `setup.py` (`crates/pydep-parser/src/setup.rs:7`) and INI parsing of `setup.cfg`
  (`crates/pydep-parser/src/setup.rs:14`) are literal `// TODO` stubs — projects using
  only these (no `requirements.txt`/`pyproject.toml`) aren't scanned at all, and
  consequently aren't covered by `remediate` either.
- **Health score "Quality" factor is a single metric**, not yet an aggregate of
  multiple quality signals (`python/pydependencycheck/scanner.py`).

## ⚠️ CI/CD — current errors

- **The PyPI publish job has never succeeded on a real release tag.** Both real
  release-tag pushes to date — `v1.0.0` and `v1.4.0` — failed at the "Publish to PyPI"
  step (`.github/workflows/wheels.yml`, job `publish`, gated on
  `refs/tags/v*`). Root cause, from the actual failed-run logs: no `PYPI_API_TOKEN`
  secret is configured on this repo, so `pypa/gh-action-pypi-publish` falls back to
  OIDC trusted publishing — which then fails because the workflow has no `permissions:
  id-token: write` block at the job level (`OpenID Connect token retrieval failed:
  ... the ACTIONS_ID_TOKEN_REQUEST_TOKEN environment variable was unset`). **v1.4.0 is
  live on PyPI today only because it was uploaded manually via `twine`**, not through
  this CI job. Two ways to actually fix this (not yet done, needs a maintainer
  decision): (a) add a `PYPI_API_TOKEN` repo secret and keep password-based publish, or
  (b) register this project for PyPI Trusted Publishing and add `permissions:
  id-token: write` to the `publish` job. Until one of these happens, every future
  release needs a manual `twine upload`.

## 🧹 Fixed 2026-09-20 (small, mechanical, verified)

- `pyproject.toml` classifier said `License :: Other/Proprietary License`
  while `license = "Apache-2.0"` and `LICENSE` itself are Apache 2.0 — a
  leftover from before the 2026-09-06 relicense that was never updated.
  Corrected to `License :: OSI Approved :: Apache Software License`.
- `CONTRIBUTING.md`'s "Contributor Agreement" line still said code would be
  licensed under a "Proprietary License." Corrected to Apache-2.0.
- `Cargo.toml` had a stray `[build-system]` TOML table (copy-pasted from
  `pyproject.toml`) that Cargo doesn't understand — every `cargo`/`clippy`
  invocation printed `warning: unused manifest key: build-system`. Removed;
  re-verified `cargo test`/`clippy`/`fmt --check` all still pass.
- `Cargo.lock` was in `.gitignore` despite this crate building a `cdylib`
  Python extension (an application/binary artifact, not a library crate) —
  Rust's own guidance is to commit the lockfile for these so builds are
  reproducible. Un-ignored and committed it; `cargo update --workspace
  --dry-run` confirmed it was already current with `Cargo.toml` (0 packages
  would change), so this didn't silently pin anything stale.
- `.github/INSTALL.md` said "Python 3.10+" (contradicting `pyproject.toml`'s
  and `README.md`'s "3.8+") and linked to a nonexistent `examples/`
  directory. Corrected.
- `actionlint` flagged three outdated action versions in `ci.yml`/`wheels.yml`
  (`actions/cache@v3`, `actions/setup-python@v4`, `codecov/codecov-action@v3`
  — all past end-of-support on GitHub-hosted runners). Bumped to
  `v4`/`v5`/`v4` respectively; `actionlint` now passes clean on both files.
- `ci.yml` ran `pytest ... --cov=pydependencycheck` (no `--cov-report=xml`)
  and then tried to upload `./coverage.xml` to Codecov — that file was never
  generated, so the upload step had nothing real to send. Added
  `--cov-report=xml` to the test command.
- **`black --check python/` was actually failing** (verified 2026-09-20,
  black 25.11.0, no version pin anywhere so CI would hit the same result):
  `python/pydependencycheck/reporters.py` and `python/pydependencycheck/
  storage.py` had drifted out of black's formatting (multi-line f-string/
  SQL literals passed as unwrapped call arguments). This means the
  `lint` job in `ci.yml` was very likely red on `main` at the time of this
  audit — this repo has hit this exact failure mode before (see git log:
  `f40c077 fix(ci): apply black formatting to unblock the Linting job`,
  `9d0aef6` same). Ran `black python/` to reformat both files (whitespace
  only, no logic changes — full `pytest` suite re-run after, still
  148/153 passing in the same partial-otel-install configuration used
  before the fix). **Could not confirm via the GitHub API whether the
  `lint` job on `main` was actually showing red**, since this environment
  has no outbound network access to query `gh run list` — stated as
  "very likely" based on local reproduction, not confirmed from Actions
  history. This has now recurred at least three times (two prior fixes in
  git log plus this one) — the actual gap is that nothing pins a `black`
  version or runs `black` as a local pre-commit hook, so drift keeps
  re-happening between CI runs and contributor machines. **Worth a
  dedicated small fix**: pin `black` in `pyproject.toml`'s `dev` extra
  and/or add a `.pre-commit-config.yaml`.

## ⚠️ New CI risk introduced by the above fix (disclosed, not silently papered over)

- `codecov/codecov-action@v4` requires a `CODECOV_TOKEN` secret even for
  public repositories (v3 did not strictly enforce this). Whether this repo
  has that secret configured could not be checked from the environment this
  audit ran in (`gh secret list` timed out — no outbound network access to
  the GitHub API). If the token is absent, the "Upload coverage" step in
  `ci.yml` will fail on every run. `continue-on-error: true` and
  `fail_ci_if_error: false` were added so that failure degrades gracefully
  instead of turning the whole `python-tests` job red. **Someone with repo
  access should verify whether `CODECOV_TOKEN` exists and add it if not** —
  otherwise coverage reporting is silently broken going forward.

## 🆕 Added 2026-09-20 (maturity/discoverability, not yet exercised by a real CI run)

- `.github/dependabot.yml` — weekly update PRs for `cargo`, `pip`, and
  `github-actions` ecosystems. Mechanical config; not yet observed to
  actually open a PR (that only happens once GitHub processes it on the
  real schedule).
- `.github/workflows/security-audit.yml` — new `cargo-audit` + `pip-audit`
  jobs on push/PR to `main` and a weekly cron. **Not yet run on GitHub's
  infrastructure as of this writing** — `actionlint` validates the YAML is
  well-formed, but neither `cargo-audit` nor `pip-audit` could be executed
  in this sandbox (both need to fetch advisory databases over the network,
  which this environment doesn't have). Treat this job as "should work,
  unverified" until it's seen green on a real run — no badge for it has
  been added to the README for that reason.
- `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.github/ISSUE_TEMPLATE/*`,
  `.github/pull_request_template.md`, `CHANGELOG.md` — none of these existed
  before; added for baseline OSS discoverability/process. Pure
  documentation, nothing to "verify" beyond the fact that they're accurate
  as written (e.g. `SECURITY.md` states plainly there's no bug bounty, no
  dedicated security team, and one maintainer).

## 🔧 Technical debt (concrete, not yet dedicated a fix session)

Measured 2026-09-20 via `pytest tests/ --cov=pydependencycheck
--cov-report=term-missing` in a clean venv with `opentelemetry-api`/`sdk`
installed (153/153 passing in that configuration):

- **Line coverage is uneven across modules and low in several
  user-facing ones.** Overall: 58% (2055 statements, 860 missed).
  Worst offenders, with the specific missing line ranges:
  - `python/pydependencycheck/vulnerabilities.py` — **0%** (123/123 lines
    uncovered). This one is explained honestly in its own module docstring
    (lines 1-9): it's a pure-Python OSV client kept for reference/library
    use, not called by the CLI (the CLI uses the Rust `pydep-security`
    crate instead via `DependencyScanner.check_vulnerabilities()`). Not
    silently dead code — already disclosed in-repo — but still zero test
    coverage on ~120 lines that ship in the package.
  - `python/pydependencycheck/git_integration.py` — **20%**, missing
    lines 10-13, 22-30, 55, 73-117, 124-162, 166-185, 190-192, 196-197,
    201-211, 215-224. This backs `why`/`trace`, two of the commands the
    README leads with — most of the actual git-blame/history logic is
    untested.
  - `python/pydependencycheck/telemetry.py` — **21%** without the `otel`
    extra installed (58% with it), missing lines 11-16, 25-27, 34, 41,
    59-70, 77-84, 97-132, 136-164, 169-183, 188-200, 205-217, 221-248,
    252-277, 281-291, 301-318, 328, 334-336, 341 — expected given the
    `skipif` gating, not a bug, but means CI (which doesn't install
    `otel`) never exercises most of this file.
  - `python/pydependencycheck/dashboard.py` — **35%**, missing lines
    30-78, 82-136, 140-179, 228-235, 250, 252, 258-280 — no
    dashboard-specific test file exists in `tests/` at all (no
    `test_dashboard.py`).
  - `python/pydependencycheck/sbom.py` — **48%**, missing lines 15-17,
    162, 166-179, 183-216, 224-246, 250-284, despite the README/ROADMAP
    calling SBOM export "built & verified" — the *signing/verification*
    path is tested (`tests/test_sbom.py` exists and passes), but roughly
    half the module's lines (CycloneDX/SPDX serialization branches, error
    paths) aren't hit.
  - `python/pydependencycheck/scanner.py` — **56%**, missing lines 15-17,
    34, 41, 118-119, 176-177, 181-187, 229, 245-246, 252-298, 302-331,
    336-337, 370, 383-385, 390-404, 415, 419-421, 435-453 — the module
    implementing the actual `scan` command, including the `setup.py`/
    `.cfg` TODO stub call site at line 335 (inside the 302-331 gap).
  - `python/pydependencycheck/cli.py` — **60%**, missing lines 56-58,
    62-63, 67-72, 75-76, 90-113, 147-173, 181-202, 214-215, 223-224, 231,
    242-247, 276, 292, 300-302, 305, 313-334, 342-346, 354-385, 421-425,
    486-488, 516, 585-589, 617, 623-625, 635-657, 662-669 (158 of 397
    lines) — CLI error handling and several flag combinations aren't
    exercised by any test.
  - No `tests/test_dashboard.py`, `tests/test_git_integration.py`, or
    `tests/test_vulnerabilities.py` exist at all — three of the ten
    `python/pydependencycheck/*.py` modules have zero dedicated test file.
  - **This warrants a dedicated follow-up session** (not a quick fix): the
    gap is in exactly the two commands (`why`/`trace`) the README leads
    with as flagship use cases, so closing it means real integration tests
    against real git repos, not just unit tests with mocks.
- **`crates/pydep-parser/src/setup.rs:7` and `:14`** — `parse_setup_py`/
  `parse_setup_cfg` are literal `// TODO` stubs returning `Ok(Vec::new())`
  with the file content read and discarded (`let _content = ...`). Already
  disclosed in README/this file's "Not built" section above; flagging here
  again with exact line numbers for whoever picks this up. **Warrants a
  dedicated session** — needs a real `setup.py` AST-ish parser (regex over
  `install_requires=[...]` at minimum) and `setup.cfg` INI parsing, plus
  test fixtures covering both.
- **`python/pydependencycheck/scanner.py:335`** — matching Python-side TODO
  for the same setup.py gap; the two should be fixed together.
- **The automated PyPI publish CI job (`.github/workflows/wheels.yml`,
  job `publish`) is still broken** — confirmed still true on this pass
  (no `PYPI_API_TOKEN` secret referenced, no `permissions: id-token:
  write` block for OIDC). Every release including the current v1.4.0 was
  uploaded manually via `twine`. **Warrants a dedicated session** — needs
  a maintainer decision (token vs. Trusted Publisher) plus a real tagged
  release to prove the fix, not just a config change.
- **Minor, not worth a dedicated session:** `Cargo.lock` was un-ignored
  and committed this pass (see above) but has never been committed before,
  so there's no history yet of it catching a dependency drift — this is a
  "safety net that now exists" note, not a bug.

## Tracking this for future roadmap planning

The categories above (built & verified / built but unverified / not built / CI errors)
are the four buckets worth checking before adding anything new to the roadmap — a
feature that looks "done" in the README can still be sitting in one of the bottom two.
