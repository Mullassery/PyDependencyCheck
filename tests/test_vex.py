"""CycloneDX VEX export tests."""

from __future__ import annotations

import json

from pydependencycheck.vex import build_vex, write_vex


def test_build_vex_uses_under_investigation_by_default():
    doc = build_vex(
        [
            {
                "id": "GHSA-x",
                "package_name": "requests",
                "fix_version": "2.32.0",
            }
        ],
        project_name="demo",
    )
    assert doc["bomFormat"] == "CycloneDX"
    assert doc["vulnerabilities"][0]["analysis"]["state"] == "under_investigation"
    assert doc["vulnerabilities"][0]["affects"][0]["ref"] == "requests"


def test_write_vex(tmp_path):
    out = tmp_path / "vex.json"
    write_vex([{"id": "CVE-1", "package_name": "flask"}], out)
    data = json.loads(out.read_text())
    assert data["vulnerabilities"][0]["id"] == "CVE-1"
