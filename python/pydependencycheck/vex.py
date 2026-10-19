"""CycloneDX VEX export from OSV findings.

A VEX document records the exploitability/status of known vulnerabilities.
Without runtime reachability this exporter uses the honest state
``under_investigation`` (not ``not_affected``), so downstream consumers do not
mistake missing evidence for a clean bill of health.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SPEC_VERSION = "1.6"


def build_vex(
    vulnerabilities: Iterable[dict[str, Any]],
    *,
    project_name: str = "project",
    state: str = "under_investigation",
) -> dict[str, Any]:
    vulns = []
    for vuln in vulnerabilities:
        vuln_id = vuln.get("id") or vuln.get("cve_id")
        if not vuln_id:
            continue
        package = vuln.get("package_name") or "unknown"
        vulns.append(
            {
                "bom-ref": f"{package}:{vuln_id}",
                "id": str(vuln_id),
                "source": {"name": "OSV"},
                "analysis": {
                    "state": state,
                    "detail": "Exported from PyDependencyCheck OSV findings; "
                    "runtime reachability was not established.",
                },
                "affects": [
                    {
                        "ref": package,
                        "versions": (
                            [{"version": str(vuln.get("fix_version") or "")}] if vuln.get("fix_version") else []
                        ),
                    }
                ],
            }
        )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": SPEC_VERSION,
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": {"type": "application", "name": project_name},
        },
        "vulnerabilities": vulns,
    }


def write_vex(
    vulnerabilities: Iterable[dict[str, Any]],
    path: str | Path,
    *,
    project_name: str = "project",
    state: str = "under_investigation",
) -> str:
    document = build_vex(vulnerabilities, project_name=project_name, state=state)
    Path(path).write_text(json.dumps(document, indent=2), encoding="utf-8")
    return str(path)


__all__ = ["SPEC_VERSION", "build_vex", "write_vex"]
