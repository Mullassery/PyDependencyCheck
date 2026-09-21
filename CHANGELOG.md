# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This file was started 2026-09-20. No changelog was kept before that date, so
entries for `v0.1.0`, `v1.0.0`, and `v1.4.0` are not reconstructed here to
avoid fabricating history — see `git log` and the
[GitHub tags](https://github.com/Mullassery/PyDependencyCheck/tags) for the
real commit-level history of those releases, and
[ROADMAP_HONEST.md](ROADMAP_HONEST.md) for what's actually verified working
in the current release.

## [Unreleased]

### Fixed
- `pyproject.toml` classifier mismatch: metadata declared `License :: Other/
  Proprietary License` while `license = "Apache-2.0"` and `LICENSE` are Apache
  2.0 (the classifier predates the 2026-09 relicense and was never updated).
  Corrected to `License :: OSI Approved :: Apache Software License`.
- `CONTRIBUTING.md` still told contributors their code would be licensed
  under a "Proprietary License" after the project relicensed to Apache-2.0.
  Corrected to reference Apache-2.0.
- CI (`ci.yml`) ran `pytest tests/ -v --cov=pydependencycheck` and then tried
  to upload `./coverage.xml` to Codecov, but no step ever generated that
  file (no `--cov-report=xml`), so the upload silently had nothing to send.
  Added `--cov-report=xml` to the test step.
- Removed a stray `[build-system]` TOML table from `Cargo.toml` (a
  copy-paste artifact from `pyproject.toml`; Cargo doesn't recognize this
  key and warned `unused manifest key: build-system` on every build).
- `Cargo.lock` was gitignored despite this crate building a `cdylib`
  (Python extension module), not a pure library — per Rust's own guidance,
  binary/application crates should commit their lockfile for reproducible
  builds. Un-ignored and committed it (verified via `cargo update --dry-run`
  that it was already up to date with `Cargo.toml`).
- `.github/INSTALL.md` said "Python 3.10+" while `pyproject.toml` and
  `README.md` both say Python 3.8+, and linked to a nonexistent `examples/`
  directory. Corrected the version and removed the dead link.
- Reformatted `python/pydependencycheck/reporters.py` and
  `python/pydependencycheck/storage.py` with `black` (whitespace only, no
  logic changes) — both had drifted out of formatting and were failing
  `black --check python/`, which the `lint` CI job runs. See
  `ROADMAP_HONEST.md` for why this keeps recurring and the suggested fix
  (pin `black`'s version / add a pre-commit hook).
- Bumped deprecated GitHub Actions in `.github/workflows/ci.yml` and
  `wheels.yml`: `actions/cache@v3` → `v4`, `actions/setup-python@v4` → `v5`,
  `codecov/codecov-action@v3` → `v4` (flagged by `actionlint`, which now
  passes clean on both workflow files).
- Pinned `black==25.11.0` (exact) in `pyproject.toml`'s `dev` extra and in
  `.github/workflows/ci.yml`'s `lint` job, replacing the unbounded
  `black>=23.0` / unpinned `pip install black ruff mypy`. This is the
  concrete fix for the `black --check` drift that had already recurred
  three times (see `ROADMAP_HONEST.md`); reproduced it again with an
  unpinned `black 26.5.1` and confirmed `25.11.0` is the version this
  repo's committed formatting actually matches, and the newest one still
  installable under the project's stated `requires-python = ">=3.8"`.
- Moved `pyproject.toml`'s `[tool.ruff]` `select`/`ignore` keys into a new
  `[tool.ruff.lint]` table — `ruff check` was printing a deprecation
  warning on every run for the old top-level location.

### Added
- `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.github/dependabot.yml`,
  `.github/ISSUE_TEMPLATE/` (bug report + feature request), and
  `.github/pull_request_template.md` — none of these existed before.

### Known issue introduced by this pass (disclosed, not silently hidden)
- `codecov/codecov-action@v4` requires a `CODECOV_TOKEN` secret even for
  public repos (v3 did not strictly require one). **Confirmed 2026-09-21**
  via `gh api repos/Mullassery/PyDependencyCheck/actions/secrets`
  (`{"total_count":0,"secrets":[]}`): this repo has no secrets configured
  at all, so the "Upload coverage" step will fail on every CI run.
  `continue-on-error: true` and `fail_ci_if_error: false` are already in
  place so this degrades to a soft failure instead of turning the whole
  `python-tests` job red, but actually fixing coverage upload requires a
  maintainer to add the secret. See `ROADMAP_HONEST.md`.
