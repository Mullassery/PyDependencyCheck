## What does this change?

<!-- One or two sentences: what problem does this solve, or what does it add? -->

## Why?

<!-- Link an issue if one exists. If not, briefly explain the motivation. -->

## How was this tested?

<!-- Be specific and honest — per this project's own documentation norms,
     say exactly what you ran and what passed, don't just check the boxes. -->

- [ ] `cargo test --workspace` (if Rust code changed)
- [ ] `cargo clippy --workspace -- -D warnings` and `cargo fmt --check` (if Rust code changed)
- [ ] `pytest tests/ -v` (if Python code changed)
- [ ] `black --check python/` and `ruff check python/` (if Python code changed)
- [ ] Manually ran the affected CLI command(s) against a real project

## Checklist

- [ ] I updated `README.md` and/or `ROADMAP_HONEST.md` if this changes what's
      built, working, or broken (this project treats those as load-bearing
      status docs, not just feature lists — see `ROADMAP_HONEST.md`'s intro)
- [ ] I did not mark anything as "working" that I didn't actually run
- [ ] New code has test coverage, or I explained why it doesn't
