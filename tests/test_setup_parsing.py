"""Regression tests for setup.py/setup.cfg dependency discovery and patching.

These files were previously skipped silently (scanner returned []).  A
security scanner that misses declared dependencies gives false assurance, so
these tests cover both the AST/configparser parsing and the remediation
patch path.
"""

from __future__ import annotations

import textwrap

from pydependencycheck.remediate import (
    PackageFix,
    build_remediation_plan,
    patch_setup_content,
)
from pydependencycheck.scanner import DependencyScanner


def test_scan_setup_cfg_install_requires(tmp_path):
    (tmp_path / "setup.cfg").write_text(
        textwrap.dedent(
            """
            [metadata]
            name = demo

            [options]
            install_requires =
                requests>=2.0,<3
                flask

            [options.extras_require]
            test =
                pytest>=7
            """
        )
    )
    deps = DependencyScanner(str(tmp_path)).scan().dependencies
    names = {d["name"] for d in deps}
    assert {"requests", "flask", "pytest"} <= names
    assert next(d for d in deps if d["name"] == "pytest")["dev"] is True


def test_scan_setup_py_literal_install_requires(tmp_path):
    (tmp_path / "setup.py").write_text(
        textwrap.dedent(
            """
            from setuptools import setup

            setup(
                name="demo",
                install_requires=["requests>=2.0,<3", "flask"],
                extras_require={"test": ["pytest>=7"]},
            )
            """
        )
    )
    deps = DependencyScanner(str(tmp_path)).scan().dependencies
    names = {d["name"] for d in deps}
    assert {"requests", "flask", "pytest"} <= names


def test_scan_setup_py_dynamic_metadata_is_not_silent(tmp_path, caplog):
    (tmp_path / "setup.py").write_text(
        "from setuptools import setup\n" "setup(name='demo', install_requires=read_requirements())\n"
    )
    deps = DependencyScanner(str(tmp_path)).scan().dependencies
    assert deps == []
    # The server still cannot resolve dynamic metadata, but it must warn
    # instead of pretending the project has no dependencies.
    assert any("computed dynamically" in r.message for r in caplog.records)


def test_patch_setup_content_rewrites_pin():
    content = 'setup(install_requires=["requests==2.25.0"])'
    fixes = [PackageFix("requests", "2.25.0", "2.32.0", ["GHSA-x"], ["setup.py"])]
    assert "requests==2.32.0" in patch_setup_content(content, fixes)


def test_build_remediation_plan_patches_setup_py(tmp_path):
    (tmp_path / "setup.py").write_text('from setuptools import setup\nsetup(install_requires=["requests==2.25.0"])\n')
    dependencies = [{"name": "requests", "version": "2.25.0", "sources": ["setup.py"], "source": "setup.py"}]
    vulnerabilities = [
        {
            "package_name": "requests",
            "fix_available": True,
            "fix_version": "2.32.0",
            "id": "GHSA-x",
        }
    ]
    plan = build_remediation_plan(str(tmp_path), dependencies, vulnerabilities)
    assert "setup.py" in plan.patches
    assert "requests==2.32.0" in plan.patches["setup.py"][1]
