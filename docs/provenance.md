# Provenance: why a dependency exists

PyDependencyCheck can answer questions that vulnerability scanners usually
cannot:

- **Who added this dependency, and when?**
- **What commit/message introduced or changed it?**
- **Is it direct or transitive, and where is it declared?**

This is the project's main differentiator. Treat the output as evidence from
your Git history, not as a package-manager lockfile database.

## Commands

```bash
# Why is this package here?
pydependencycheck why requests

# Current status + every manifest change across history
pydependencycheck trace requests
```

Options:

| Command | Option | Meaning |
|---|---|---|
| `why` | `-p/--path` | Project path (default: current directory) |
| `trace` | `-p/--path` | Project path (default: current directory) |

## What `why` shows

A verified example (run against this repository):

```text
requests
  Version: ==2.32.0
  Source: test_project/requirements.txt

Introduced by:
  Commit: 09fa4f3
  Author: Georgi Mammen Mullassery
  Date: 2026-08-03 01:55:27
  Message: Initial PyDependencyCheck scaffold: Rust core + Python CLI, 5-phase roadmap
```

- `Version` is the constraint as declared in the manifest.
- `Source` is the manifest file where the dependency is declared.
- `Introduced by` is derived from `git blame` on that declaration line. The
  commit is the one that last touched the line, which is normally the commit
  that introduced or last edited the dependency.

## What `trace` shows

`trace` prints the current status (direct/transitive, declared file) and a
table of historical entries with date, commit, version, author, file, and
message. It reconstructs the history from real Git commits, not from a
simulated log.

## Requirements and accuracy

- **A Git repository is required.** In a directory without `.git`, provenance
  cannot be reconstructed.
- **Manifest lines are the unit of evidence.** `why` blames the line where the
  dependency is declared. If a declaration spans lines or was reformatted, the
  blamed commit is the reformat, not necessarily the original introduction.
- **History depth is limited by the clone.** Shallow clones (`--depth`) only
  contain recent commits.
- **Dynamic metadata is not executed.** For `setup.py`, only static
  `install_requires`/`extras_require` are read (via AST); calls such as
  `read_requirements()` are reported as warnings, not resolved. See
  [Limitations](limitations.md).
- **Lockfiles are not the source.** Provenance describes manifest declarations,
  not resolved lockfile graphs.

## Practical workflow

1. Run `trace <package>` before removing a dependency; the history often shows
   the feature that introduced it.
2. Use `why <package>` in incident review to find the commit and author to ask.
3. For audit evidence, pair provenance output with a signed SBOM
   ([SBOM](sbom.md)) and a VEX statement ([VEX](vex.md)).
