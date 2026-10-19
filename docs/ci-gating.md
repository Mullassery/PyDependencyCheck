# CI gating with GitHub Actions

`pydependencycheck gate` computes the same health score as `health` and exits
non-zero when your criteria fail. It is designed to run as a CI step; no hosted
service is required.

## Command

```bash
pydependencycheck gate --min-health 50 --max-dead-deps 10
```

| Option | Default | Meaning |
|---|---|---|
| `-p/--path` | `.` | Project path |
| `--min-health` | `50` | Minimum acceptable health score (0–100) |
| `--max-dead-deps` | `10` | Maximum acceptable unused-dependency count |
| `--offline` | off | Skip OSV/PyPI network calls for a local-only check |

## When the gate fails

The gate exits `1` if **any** of these is true:

- at least one **critical** vulnerability is found;
- the health score is **below 50** (built-in floor);
- the health score is below your `--min-health` value;
- unused dependencies exceed `--max-dead-deps`.

Otherwise it exits `0`.

> The built-in floor of 50 applies even if you pass a lower `--min-health`.
> Raising `--min-health` makes the gate stricter; lowering it below 50 does not
> make the gate more permissive.

## GitHub Actions annotations

When `GITHUB_ACTIONS` is set, `gate` emits workflow annotations:

- `::error` for critical/high vulnerabilities and gate failures;
- `::warning` for lower-severity findings, unused dependencies, and issues;
- `::notice` for the health summary.

Outside GitHub Actions, annotations are suppressed but the exit code still
applies, so the command works in any CI.

## Example workflow

```yaml
name: Dependency health

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  dependency-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install
        run: python -m pip install pydependencycheck
      - name: Gate
        run: pydependencycheck gate --min-health 65 --max-dead-deps 5
```

Notes:

- There is **no official `uses:` action yet**; this is a normal step.
- `permissions: contents: read` is sufficient for the gate.
- If your CI has no network access, add `--offline`. An offline run does not
  check OSV vulnerabilities, so treat it as a local hygiene check only.
- Tune thresholds against a baseline run before enforcing them on all PRs.

## Recommended rollout

1. Run `pydependencycheck health` locally and record the current score.
2. Start with a threshold slightly below the baseline (for example, baseline
   minus 5) and no dead-dependency cap.
3. Once the score is stable, add `--max-dead-deps`.
4. Keep `--min-health` at or above 50.

See [Health score](health-score.md) for how the number is computed and
[Limitations](limitations.md) for what the gate cannot detect.
