"""Tests for the dependency scanner"""

import pytest

from pydependencycheck.scanner import DependencyScanner, ScanResult


class TestDependencyScanner:
    """Test dependency scanning"""

    def test_scan_empty_directory(self, tmp_path):
        """An empty directory has no dependency files and no dependencies."""
        scanner = DependencyScanner(str(tmp_path))
        result = scanner.scan()

        assert result.dependencies == []
        assert result.direct_count == 0
        assert result.transitive_count == 0

    def test_scan_requirements_txt(self, tmp_path):
        """Test scanning a project with requirements.txt"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.32.0\nflask>=1.0.0\n")

        scanner = DependencyScanner(str(tmp_path))
        result = scanner.scan()

        names = {d["name"] for d in result.dependencies}
        assert names == {"requests", "flask"}
        assert result.direct_count == 2
        assert result.transitive_count == 0

        requests_dep = next(d for d in result.dependencies if d["name"] == "requests")
        assert requests_dep["direct"] is True
        assert requests_dep["version"] is not None
        assert "2.32.0" in requests_dep["version"]

    def test_scan_requirements_with_extras_and_range(self, tmp_path):
        """Regression test for a real bug: `pkg[extra]>=x,<y` used to lose
        its version constraint entirely because the Rust parser dropped
        everything after the closing `]` (see requirements.rs fix)."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("django[async]>=3.2,<4.0\n")

        scanner = DependencyScanner(str(tmp_path))
        result = scanner.scan()

        assert len(result.dependencies) == 1
        dep = result.dependencies[0]
        assert dep["name"] == "django"
        assert dep["version"] is not None
        assert "3.2" in dep["version"]

    def test_scan_requirements_with_non_equals_operators(self, tmp_path):
        """Regression test: the old pure-Python fallback only recognized
        `==`, so `flask>=2.0.0,<3.0.0` used to be parsed as a single
        package literally named "flask>=2.0.0,<3.0.0" with no version."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("flask>=2.0.0,<3.0.0\n")

        scanner = DependencyScanner(str(tmp_path))
        result = scanner.scan()

        assert len(result.dependencies) == 1
        assert result.dependencies[0]["name"] == "flask"

    def test_scan_pyproject_toml(self, tmp_path):
        """Test scanning a project with pyproject.toml"""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
dependencies = ["requests>=2.0", "click>=8.0"]
"""
        )

        scanner = DependencyScanner(str(tmp_path))
        result = scanner.scan()

        names = {d["name"] for d in result.dependencies}
        assert names == {"requests", "click"}

    def test_scan_dedupes_package_declared_in_multiple_files(self, tmp_path):
        """Regression test: merging a package seen in two dependency files
        used to crash with KeyError('sources') because the code appended
        to a "sources" key that was never initialized on first sight."""
        (tmp_path / "requirements.txt").write_text("requests==2.32.0\n")
        (tmp_path / "pyproject.toml").write_text(
            """
[project]
dependencies = ["requests>=2.0"]
"""
        )

        scanner = DependencyScanner(str(tmp_path))
        result = scanner.scan()  # must not raise

        requests_deps = [d for d in result.dependencies if d["name"] == "requests"]
        assert len(requests_deps) == 1
        assert len(requests_deps[0]["sources"]) == 2

    def test_scan_ignores_venv_directory(self, tmp_path):
        """Regression test: a recursive glob for dependency files used to
        also match manifests bundled inside an in-project venv's installed
        packages (pip/setuptools ship their own test-fixture
        requirements.txt/pyproject.toml files), polluting scan results."""
        (tmp_path / "requirements.txt").write_text("requests==2.32.0\n")

        venv_pkg_dir = tmp_path / "venv" / "lib" / "some_pkg"
        venv_pkg_dir.mkdir(parents=True)
        (venv_pkg_dir / "requirements.txt").write_text("some-unrelated-nested-dep==9.9.9\n")

        scanner = DependencyScanner(str(tmp_path))
        result = scanner.scan()

        names = {d["name"] for d in result.dependencies}
        assert names == {"requests"}
        assert "some-unrelated-nested-dep" not in names

    def test_find_dead_dependencies_no_rust_backend(self, tmp_path, monkeypatch):
        """Without the Rust backend, dead-dependency detection should
        degrade gracefully (empty result) rather than raising."""
        import pydependencycheck.scanner as scanner_module

        monkeypatch.setattr(scanner_module, "HAS_RUST_BACKEND", False)
        (tmp_path / "requirements.txt").write_text("requests==2.32.0\n")

        scanner = scanner_module.DependencyScanner(str(tmp_path))
        scanner.scan()
        assert scanner.find_dead_dependencies() == []


class TestScanResult:
    def test_to_dict_reflects_counts(self):
        result = ScanResult()
        result.dependencies = [{"name": "a", "direct": True}, {"name": "b", "direct": False}]
        result.direct_count = 1
        result.transitive_count = 1

        as_dict = result.to_dict()
        assert as_dict["total_count"] == 2
        assert as_dict["direct_count"] == 1
        assert as_dict["transitive_count"] == 1


class TestDependencyGraph:
    """Test dependency graph construction (Rust-backed)"""

    def test_add_nodes(self):
        pydependencycheck = pytest.importorskip("pydependencycheck")
        if pydependencycheck.graph is None:
            pytest.skip("Rust extension not built")

        graph = pydependencycheck.graph.DependencyGraph()
        graph.add_node("requests", "2.32.0", True)
        graph.add_node("urllib3", "2.0.0", False)

        assert graph.node_count() == 2

    def test_detect_cycles(self):
        pydependencycheck = pytest.importorskip("pydependencycheck")
        if pydependencycheck.graph is None:
            pytest.skip("Rust extension not built")

        graph = pydependencycheck.graph.DependencyGraph()
        graph.add_node("a", None, True)
        graph.add_node("b", None, False)
        graph.add_edge("a", "b")
        graph.add_edge("b", "a")

        assert graph.has_cycles() is True

    def test_no_cycles_in_dag(self):
        pydependencycheck = pytest.importorskip("pydependencycheck")
        if pydependencycheck.graph is None:
            pytest.skip("Rust extension not built")

        graph = pydependencycheck.graph.DependencyGraph()
        graph.add_node("a", None, True)
        graph.add_node("b", None, False)
        graph.add_edge("a", "b")

        assert graph.has_cycles() is False

    def test_transitive_closure(self):
        pydependencycheck = pytest.importorskip("pydependencycheck")
        if pydependencycheck.graph is None:
            pytest.skip("Rust extension not built")

        graph = pydependencycheck.graph.DependencyGraph()
        graph.add_node("app", None, True)
        graph.add_node("mid", None, False)
        graph.add_node("leaf", None, False)
        graph.add_edge("app", "mid")
        graph.add_edge("mid", "leaf")

        all_deps = graph.get_all_dependencies("app")
        assert set(all_deps) == {"mid", "leaf"}
