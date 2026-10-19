# Command reference

Every command below was verified against the v1.5.0 CLI on 2026-10-19. Run
`pydependencycheck <command> --help` for the authoritative flags.

## Global

```text
pydependencycheck [--version] [--help] COMMAND [ARGS]...
```

## `scan`

Parse manifests and show a dependency overview.

```text
pydependencycheck scan [-p PATH] [-o FILE] [-f json|html|markdown|table] [--save-snapshot]
```

## `list`

List dependencies.

```text
pydependencycheck list [-p PATH] [-l LIMIT]
```

## `why`

Show Git provenance for a package.

```text
pydependencycheck why [-p PATH] PACKAGE
```

## `trace`

Show current status plus full Git history for a package.

```text
pydependencycheck trace [-p PATH] PACKAGE
```

## `health`

Compute the weighted health score.

```text
pydependencycheck health [-p PATH] [--offline] [--save-snapshot]
                         [--otel] [--otel-exporter console|otlp|jaeger|prometheus]
```

See [Health score](health-score.md).

## `licenses`

Classify dependency licenses and optional compatibility.

```text
pydependencycheck licenses [-p PATH] [--project-license LICENSE] [--fail-on-restricted]
```

## `remediate`

Print (and optionally apply) exact-pin upgrades for OSV-fixed versions.

```text
pydependencycheck remediate [-p PATH] [--apply] [--pr]
                            [--branch NAME] [--base-branch NAME] [--remote NAME]
```

Without `--apply`/`--pr`, this is a dry run that prints diffs.

## `export`

Export an SBOM.

```text
pydependencycheck export [-p PATH] [-f cyclonedx|spdx] [-o FILE]
                         [--sign] [--key PEM]
```

See [SBOM](sbom.md).

## `gate`

CI gate with a non-zero exit on failure.

```text
pydependencycheck gate [-p PATH] [--min-health N] [--max-dead-deps N] [--offline]
```

See [CI gating](ci-gating.md).

## `vex`

Export OSV findings as CycloneDX 1.6 VEX.

```text
pydependencycheck vex [-o FILE] [--state under_investigation|affected|not_affected|fixed] [PATH]
```

`--output/-o` is required. See [VEX](vex.md).

## `snapshot`

Manage dependency snapshots.

```text
pydependencycheck snapshot [-p PATH] [--save]
```

## `drift`

Detect dependency drift since a baseline.

```text
pydependencycheck drift [-p PATH] [-b BASELINE]
```

## `history`

Show dependency history and trends.

```text
pydependencycheck history [-p PATH] [-d DAYS]
```
