# Contributing to PyDependencyCheck

Thanks for your interest in contributing! This guide covers development setup, testing, and the submission process.

## Development Setup

### Prerequisites
- Rust 1.75+ (`rustup update`)
- Python 3.8+ (3.10+ recommended)
- Git

### Clone & Build

```bash
git clone https://github.com/Mullassery/pydependencycheck
cd pydependencycheck

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install development dependencies
pip install -e .[dev]
pip install maturin

# Build Rust extension
maturin develop --release
```

### Running Tests

```bash
# Rust tests (fast)
cargo test --workspace

# Python tests (with coverage)
pytest tests/ -v --cov=pydependencycheck

# All checks
cargo fmt
cargo clippy
black python/
ruff python/
```

## Project Structure

```
PyDependencyCheck/
├── crates/                  # Rust workspace
│   ├── pydep-parser/        # Dependency file parsing
│   ├── pydep-graph/         # Graph algorithms (petgraph)
│   ├── pydep-ast/           # Code analysis (tree-sitter)
│   ├── pydep-security/      # OSV integration, scoring
│   └── pydep-py/            # PyO3 bindings
├── python/
│   └── pydependencycheck/   # Python package
│       ├── cli.py           # Click CLI
│       ├── scanner.py       # Main scanner
│       ├── reporters.py     # Output generators
│       ├── storage.py       # SQLite layer
│       └── git_integration.py
├── tests/                   # Test files
├── docs/                    # Documentation
└── pyproject.toml           # Maturin config
```

## Coding Standards

### Rust
- Format: `cargo fmt`
- Lint: `cargo clippy -- -D warnings`
- Tests: Unit tests in each crate, integration tests in `tests/`

### Python
- Format: `black python/` (line length 120)
- Lint: `ruff python/` (E, F, W, I)
- Type hints: Encouraged but not required (mypy friendly)

## Adding a Feature

### 1. Create an Issue
Describe what you want to build and why.

### 2. Design Phase
- Small features: Direct to PR
- Large features: Open a Design Discussion first

### 3. Development
- Create a feature branch: `git checkout -b feat/your-feature`
- Write tests first (TDD encouraged)
- Keep commits small and focused

### 4. Testing
- Rust: `cargo test --workspace`
- Python: `pytest tests/ -v`
- Integration: End-to-end test with real projects

### 5. Pull Request
- Link to the issue
- Describe changes clearly
- Ensure CI passes (GitHub Actions)
- Request review from maintainers

## Common Tasks

### Adding a Dependency Parser
1. Create parser module in `crates/pydep-parser/src/`
2. Implement `parse_xyz_file()` function
3. Update `lib.rs` to export it
4. Add integration test in `tests/`

### Adding a CLI Command
1. Add function to `python/pydependencycheck/cli.py`
2. Decorate with `@cli.command()`
3. Write docstring with examples
4. Test: `pydependencycheck --help`

### Improving Performance
1. Profile with `cargo flamegraph` or `py-spy`
2. Add benchmark test
3. Document improvements in PR

## Release Process

1. **Version bump:** Edit `Cargo.toml` + `pyproject.toml`
2. **Changelog:** Update `CHANGELOG.md`
3. **Tag:** `git tag v0.1.0`
4. **Push:** GitHub Actions builds wheels automatically
5. **PyPI:** Artifacts published to PyPI

## Getting Help

- **Slack:** [Join our community](https://community.example.com) (when available)
- **Discussions:** [GitHub Discussions](https://github.com/Mullassery/pydependencycheck/discussions)
- **Issues:** [Report a bug](https://github.com/Mullassery/pydependencycheck/issues)

---

**Contributor Agreement:** By submitting code, you agree it will be licensed under MIT.
