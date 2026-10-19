# VEX export

`pydependencycheck vex` turns OSV findings into a **CycloneDX 1.6 VEX**
document, so downstream consumers can record the exploitability status of each
known vulnerability.

## Command

```bash
pydependencycheck vex . --output vex.json --state under_investigation
```

| Option | Required | Values |
|---|---|---|
| `-o/--output` | yes | Output file path |
| `--state` | no | `under_investigation` (default), `affected`, `not_affected`, `fixed` |
| `PATH` | no | Project path (default: current directory) |

The command scans the project, queries OSV, and writes the VEX document. It
requires network access to OSV; there is currently no `--offline` option.

## Output

Verified structure:

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.6",
  "version": 1,
  "metadata": { "timestamp": "...", "component": { "type": "application", "name": "..." } },
  "vulnerabilities": [
    {
      "bom-ref": "<package>:<id>",
      "id": "<OSV id>",
      "source": { "name": "OSV" },
      "analysis": {
        "state": "under_investigation",
        "detail": "Exported from PyDependencyCheck OSV findings; runtime reachability was not established."
      },
      "affects": [{ "ref": "<package>", "versions": [] }]
    }
  ]
}
```

Notes:

- The default state is intentionally `under_investigation`, **not**
  `not_affected`. Missing reachability evidence is never presented as a clean
  result.
- `analysis.detail` states explicitly that reachability was not established.
- The exporter does not perform analyst triage; set `--state` only when you have
  evidence that justifies it for the whole exported set.
- `source.name` is `OSV`, because findings come from OSV.dev.

## Practical workflow

1. Run `vex` with the default state.
2. Assign each vulnerability a state in your VEX review process.
3. Publish the reviewed document alongside the SBOM
   ([SBOM](sbom.md)) for auditors.

## Limitations

- No reachability analysis; states are assertions, not proof.
- The command exports all OSV findings for the declared dependency set.
- CycloneDX 1.6 only.
- See [Limitations](limitations.md).
