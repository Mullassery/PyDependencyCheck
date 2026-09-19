# Installation Guide

## Quick Install

```bash
pip install pydependencycheck
```

## Requirements

- Python 3.8+
- macOS, Linux (x86_64), or Windows (x86_64) with a prebuilt wheel available;
  see [What's not working / open issues](../README.md#whats-not-working--open-issues)
  in the README for current CI/release gaps.

## Installation

### Standard Install (Recommended)
Works for most users with prebuilt wheels (Linux x86_64, macOS Intel/Apple Silicon, Windows x86_64):
```bash
pip install pydependencycheck
```

### From Source (If No Prebuilt Wheel Matches Your Platform)
Requires a Rust toolchain and [maturin](https://github.com/PyO3/maturin):
```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Clone and build
git clone https://github.com/Mullassery/PyDependencyCheck
cd PyDependencyCheck
pip install maturin
maturin build --release
pip install target/wheels/pydependencycheck-*.whl
```

## Troubleshooting

### "No wheels available for your platform"
Build from source using the steps above, then:
```bash
pip install --force-reinstall pydependencycheck
```

### Python version issues
This project requires Python 3.8+:
```bash
python --version
```

### Missing dependencies (Linux)
```bash
sudo apt-get install python3-dev build-essential
```

## Next Steps

After installation:
1. See the [README](../README.md) for the quick start and full command reference.
2. See [ROADMAP_HONEST.md](../ROADMAP_HONEST.md) for what's verified vs. not built.
3. See [CONTRIBUTING.md](../CONTRIBUTING.md) if you want to build from source or contribute.
