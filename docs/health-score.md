# Health score

`pydependencycheck health` produces a single 0–100 score from four
independently computed factors. The implementation is
`HealthAnalyzer.compute_health_score` in
`python/pydependencycheck/health.py`.

## Weights

| Factor | Weight | Source |
|---|---|---|
| Vulnerabilities | 40% | OSV.dev |
| Maintenance (staleness) | 30% | PyPI release metadata |
| Quality (unused dependencies) | 20% | AST import analysis |
| Complexity (dependency count) | 10% | Declared dependency count |

Final score = weighted sum, truncated to an integer.

## How each factor is scored

### Vulnerabilities (0–100)

Starts at 100.

- `-20` for each package with at least one **CRITICAL** vulnerability.
- `-10` for each package with at least one **HIGH** vulnerability.
- Clamped to `0…100`.

A package with both severities is counted in both deductions (for example,
one package with a critical and a high finding scores `100 - 20 - 10 = 70`).

### Maintenance (0–100)

A package is **stale** when its latest PyPI release is more than **365 days**
old. A package whose metadata cannot be fetched is **not** counted as stale.

| Stale share of dependencies | Score |
|---|---|
| 0 | 100 |
| ≤ 10% | 90 |
| ≤ 25% | 75 |
| ≤ 50% | 50 |
| > 50% | 30 |

### Quality / unused dependencies (0–100)

| Unused share of dependencies | Score |
|---|---|
| 0 | 100 |
| ≤ 5% | 95 |
| ≤ 10% | 80 |
| ≤ 30% | 60 |
| > 30% | 40 |

See [Limitations](limitations.md): AST detection can miss dynamically imported
modules and can flag packages imported only in tooling.

### Complexity (0–100)

| Declared dependencies | Score |
|---|---|
| ≤ 20 | 95 |
| ≤ 50 | 80 |
| ≤ 100 | 60 |
| > 100 | 40 |

## Ratings

| Score | Rating |
|---|---|
| ≥ 80 | Excellent |
| ≥ 65 | Good |
| ≥ 50 | Fair |
| ≥ 35 | Poor |
| < 35 | Critical |

## Offline mode

`--offline` skips OSV and PyPI lookups. The maintenance factor then has no
staleness data and the vulnerability factor has no findings, so the resulting
score is a **local hygiene score only**. Do not read an offline score as "no
known vulnerabilities".

Example verified run against `test_project/`:

```text
Health Score: 87/100 (Excellent)
Critical vulnerabilities: 0
Unused dependencies: 3
```

## Gate interaction

`gate` uses the same score. Its built-in floor is 50, and `--min-health` can
make the requirement stricter. See [CI gating](ci-gating.md).
