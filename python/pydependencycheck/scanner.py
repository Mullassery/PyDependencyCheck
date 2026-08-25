"""Dependency Scanner: Orchestrates parsing, analysis, and reporting"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import Rust backend
try:
    from . import _pydependencycheck

    HAS_RUST_BACKEND = True
except ImportError:
    HAS_RUST_BACKEND = False
    logger.warning("Rust backend not available, using pure Python (slower)")


def exact_pin_version(version_spec: Optional[str]) -> Optional[str]:
    """Extract a concrete version from a dependency's stored `version`
    field, but only when it unambiguously names one version.

    `dep["version"]` stores the *full* PEP 508 specifier as parsed
    (`"==2.25.0"`, `">=2.0.0,<3.0.0"`, `"~=8.1"`) rather than a bare
    version -- fine for display/SBOM purposes, but wrong to feed directly
    into a version-sensitive API like OSV's, which needs a real semver
    string (`"==2.25.0"` fails to parse as semver and silently matches
    nothing). Only a bare `==` pin resolves to one concrete version; any
    other operator or a comma-separated range is left out rather than
    guessed at.
    """
    if not version_spec:
        return None
    spec = version_spec.strip()
    if spec.startswith("==") and "," not in spec:
        return spec[2:].strip() or None
    # Already a bare version (no leading operator) -- some callers pass this form.
    if re.match(r"^\d", spec):
        return spec
    return None


class ScanResult:
    """Result of a dependency scan"""

    def __init__(self):
        self.dependencies: List[Dict[str, Any]] = []
        self.direct_count: int = 0
        self.transitive_count: int = 0
        self.cycles: List[List[str]] = []
        self.graph_data: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dependencies": self.dependencies,
            "direct_count": self.direct_count,
            "transitive_count": self.transitive_count,
            "total_count": self.direct_count + self.transitive_count,
            "cycles": self.cycles,
        }


class DependencyScanner:
    """Main scanner class that orchestrates dependency analysis"""

    # Files to search for dependencies, in priority order
    DEPENDENCY_FILES = [
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-test.txt",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "Pipfile",
        "Pipfile.lock",
        "poetry.lock",
        "uv.lock",
    ]

    # Directories that should never be walked into when auto-detecting
    # dependency files: virtual environments and VCS/build/cache dirs
    # commonly nested inside a real project. Without this, a recursive
    # `**/requirements.txt`-style glob on "." also matches every dependency
    # manifest bundled inside an in-project venv's installed packages
    # (pip/setuptools ship their own requirements.txt/pyproject.toml test
    # fixtures), producing bogus, unrelated results.
    IGNORED_DIRS = {
        ".git",
        ".hg",
        ".svn",
        "venv",
        ".venv",
        "env",
        ".env",
        "node_modules",
        "__pycache__",
        ".tox",
        ".nox",
        "build",
        "dist",
        ".eggs",
        "site-packages",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.found_files: List[Path] = []
        self.parsed_deps: List[Dict[str, Any]] = []

    def _is_ignored(self, path: Path) -> bool:
        """Check whether a path falls inside an ignored directory."""
        try:
            relative_parts = path.relative_to(self.project_path).parts
        except ValueError:
            relative_parts = path.parts
        return any(part in self.IGNORED_DIRS or part.endswith(".egg-info") for part in relative_parts)

    def find_dependency_files(self) -> List[Path]:
        """Auto-detect dependency declaration files"""
        found = []
        for pattern in self.DEPENDENCY_FILES:
            matches = list(self.project_path.glob(f"**/{pattern}"))
            found.extend(m for m in matches if not self._is_ignored(m))

        self.found_files = found
        logger.info(f"Found {len(found)} dependency files: {[f.name for f in found]}")
        return found

    def parse_dependencies(self) -> List[Dict[str, Any]]:
        """Parse all found dependency files using Rust backend"""
        dependencies: Dict[str, Dict[str, Any]] = {}

        for file_path in self.found_files:
            logger.info(f"Parsing {file_path.relative_to(self.project_path)}")
            deps = self._parse_file(file_path)
            for dep in deps:
                name = dep["name"]
                if name not in dependencies:
                    # "sources" tracks every file that declares this
                    # package (a dep can legitimately appear in both
                    # requirements.txt and pyproject.toml); "source"
                    # (singular) is kept as the first-seen file for
                    # backwards compatibility with callers that only
                    # display one location.
                    dep["sources"] = [dep.get("source", str(file_path))]
                    dependencies[name] = dep
                else:
                    # Merge version constraints if seen in multiple files
                    existing = dependencies[name]
                    existing.setdefault("sources", [existing.get("source", str(file_path))])
                    existing["sources"].append(dep.get("source", str(file_path)))

        self.parsed_deps = list(dependencies.values())
        return self.parsed_deps

    # File types the Rust PEP 508 parser (crates/pydep-parser) fully
    # supports: requirements*.txt, constraints.txt, pyproject.toml. It
    # correctly handles every version operator (>=, <=, ~=, !=, ...), extras,
    # and environment markers -- the pure-Python fallback below only ever
    # recognized "==". setup.py/setup.cfg parsing isn't implemented on
    # either side yet (see `_parse_setup_file`).
    _RUST_PARSEABLE = ("constraints.txt", "pyproject.toml")

    def _parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a single dependency file"""
        file_name = file_path.name.lower()
        rust_supported = "requirements" in file_name or file_name in self._RUST_PARSEABLE

        if HAS_RUST_BACKEND and rust_supported:
            try:
                return self._parse_file_rust(file_path)
            except Exception as e:
                logger.warning(f"Rust parser failed for {file_path}, falling back to Python parser: {e}")

        if "requirements" in file_name or file_name == "constraints.txt":
            return self._parse_requirements_txt(file_path)
        elif file_name == "pyproject.toml":
            return self._parse_pyproject_toml(file_path)
        elif file_name in ("setup.py", "setup.cfg"):
            return self._parse_setup_file(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_name}")
            return []

    def _parse_file_rust(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse using the Rust PEP 508 parser.

        This is the real, fully-tested parser (7 unit tests across
        requirements.rs/pyproject.rs/constraint.rs) and correctly handles
        version operators the pure-Python fallback above does not (e.g.
        `flask>=2.0.0,<3.0.0` was previously mis-parsed as a single package
        named "flask>=2.0.0,<3.0.0" with no version, since the fallback only
        ever split on "==").
        """
        source = str(file_path.relative_to(self.project_path))
        file_name = file_path.name.lower()
        rust_deps = _pydependencycheck.parser.parse_file(str(file_path))

        result = []
        for dep in rust_deps:
            # requirements-dev.txt / requirements-test.txt should still be
            # flagged as dev dependencies by filename, same as the
            # pure-Python fallback -- the Rust requirements.txt parser
            # doesn't infer this from the filename itself.
            dev = dep.dev or ("dev" in file_name or "test" in file_name)
            result.append(
                {
                    "name": dep.name,
                    "version": dep.version,
                    "source": source,
                    "direct": dep.direct,
                    "dev": dev,
                }
            )
        return result

    def _parse_requirements_txt(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse requirements.txt format"""
        dependencies = []
        try:
            content = file_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue

                # Simple parsing (full PEP 508 handled by Rust backend)
                parts = line.split("==")
                name = parts[0].strip().lower()
                version = parts[1].strip() if len(parts) > 1 else None

                dependencies.append(
                    {
                        "name": name,
                        "version": version,
                        "source": str(file_path.relative_to(self.project_path)),
                        "direct": True,
                        "dev": "dev" in file_path.name.lower(),
                    }
                )
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")

        return dependencies

    def _parse_pyproject_toml(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse pyproject.toml"""
        dependencies = []
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore
            except ImportError:
                logger.warning("tomli not installed, skipping pyproject.toml")
                return []

        try:
            content = file_path.read_text(encoding="utf-8")
            data = tomllib.loads(content)

            # PEP 621 project dependencies
            if "project" in data:
                project = data["project"]
                if "dependencies" in project:
                    for dep in project.get("dependencies", []):
                        deps = self._parse_pep508(dep, file_path, dev=False)
                        dependencies.extend(deps)

                if "optional-dependencies" in project:
                    for group, deps_list in project["optional-dependencies"].items():
                        for dep in deps_list:
                            deps = self._parse_pep508(dep, file_path, dev=True)
                            dependencies.extend(deps)

            # Poetry dependencies
            if "tool" in data and "poetry" in data["tool"]:
                poetry = data["tool"]["poetry"]
                for name, version in poetry.get("dependencies", {}).items():
                    if name != "python":
                        dependencies.append(
                            {
                                "name": name.lower(),
                                "version": str(version) if version else None,
                                "source": str(file_path.relative_to(self.project_path)),
                                "direct": True,
                                "dev": False,
                            }
                        )

        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")

        return dependencies

    def _parse_pep508(self, req: str, file_path: Path, dev: bool = False) -> List[Dict[str, Any]]:
        """Parse PEP 508 requirement string"""
        try:
            # Split on semicolon to remove markers
            req = req.split(";")[0].strip()
            # Simple extraction of name
            for op in ["==", ">=", "<=", "!=", "~=", ">"]:
                if op in req:
                    name = req.split(op)[0].strip()
                    version = req.split(op)[1].strip().split(",")[0].strip()
                    return [
                        {
                            "name": name.lower().replace("_", "-"),
                            "version": version,
                            "source": str(file_path.relative_to(self.project_path)),
                            "direct": True,
                            "dev": dev,
                        }
                    ]

            return [
                {
                    "name": req.lower().replace("_", "-"),
                    "version": None,
                    "source": str(file_path.relative_to(self.project_path)),
                    "direct": True,
                    "dev": dev,
                }
            ]
        except Exception as e:
            logger.error(f"Failed to parse requirement '{req}': {e}")
            return []

    def _parse_setup_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse setup.py or setup.cfg"""
        # TODO: Implement proper setup.py AST parsing
        logger.warning(f"setup.py/setup.cfg parsing not yet implemented: {file_path}")
        return []

    def scan(self) -> ScanResult:
        """Execute full dependency scan"""
        result = ScanResult()

        # Find all dependency files
        self.find_dependency_files()
        if not self.found_files:
            logger.warning(f"No dependency files found in {self.project_path}")

        # Parse dependencies
        self.parse_dependencies()
        result.dependencies = self.parsed_deps

        # Count direct vs transitive
        result.direct_count = sum(1 for dep in self.parsed_deps if dep.get("direct", False))
        result.transitive_count = len(self.parsed_deps) - result.direct_count

        # Build graph for analysis
        if HAS_RUST_BACKEND:
            result.graph_data = self._build_graph()

        logger.info(
            f"Scan complete: {len(self.parsed_deps)} dependencies "
            f"({result.direct_count} direct, {result.transitive_count} transitive)"
        )

        return result

    def _build_graph(self) -> Dict[str, Any]:
        """Build dependency graph using Rust backend"""
        if not HAS_RUST_BACKEND:
            return {}

        try:
            graph = _pydependencycheck.graph.DependencyGraph()

            # Add nodes
            for dep in self.parsed_deps:
                graph.add_node(dep["name"], dep.get("version"), dep.get("direct", False))

            return {
                "nodes": len(self.parsed_deps),
                "cycles": graph.has_cycles(),
            }
        except Exception as e:
            logger.error(f"Failed to build graph: {e}")
            return {}

    def analyze_usage(self) -> Dict[str, int]:
        """Scan the project's source tree and count how many times each
        declared dependency is actually imported."""
        if not HAS_RUST_BACKEND:
            logger.warning("Rust backend not available, skipping usage analysis")
            return {}

        try:
            imported = _pydependencycheck.ast.scan_imports(str(self.project_path))
        except Exception as e:
            logger.error(f"Usage analysis failed: {e}")
            return {}

        counts: Dict[str, int] = {}
        for dep in self.parsed_deps:
            normalized = dep["name"].lower().replace("_", "-")
            counts[dep["name"]] = sum(1 for pkg in imported if pkg.lower().replace("_", "-") == normalized)
        return counts

    def find_dead_dependencies(self) -> List[Dict[str, str]]:
        """Find declared dependencies that are never imported anywhere in
        the project, with a confidence level (High/Medium/Low)."""
        if not HAS_RUST_BACKEND:
            logger.warning("Rust backend not available, skipping dead-dependency scan")
            return []

        installed = [dep["name"] for dep in self.parsed_deps]
        if not installed:
            return []

        try:
            dead = _pydependencycheck.ast.find_dead_packages(str(self.project_path), installed)
        except Exception as e:
            logger.error(f"Dead-dependency scan failed: {e}")
            return []

        return [{"name": name, "confidence": confidence} for name, confidence in dead]

    def check_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Check parsed dependencies against the OSV.dev vulnerability database.

        Only exactly-pinned dependencies (`==X.Y.Z`) can be checked
        meaningfully, since OSV's SEMVER range matching needs one concrete
        version to test against -- a range/compatible-release specifier
        (`>=2.0,<3.0`, `~=8.1`) doesn't resolve to a single version without
        actually resolving the dependency, so those are skipped rather than
        guessed at.
        """
        if not HAS_RUST_BACKEND:
            logger.warning("Rust backend not available, skipping vulnerability scan")
            return []

        pinned = [
            (dep["name"], version)
            for dep in self.parsed_deps
            if (version := exact_pin_version(dep.get("version"))) is not None
        ]
        if not pinned:
            return []

        try:
            vulns = _pydependencycheck.security.scan_vulnerabilities(pinned)
        except Exception as e:
            logger.error(f"Vulnerability scan failed: {e}")
            return []

        return [
            {
                "id": v.id,
                "package_name": v.package_name,
                "severity": v.severity,
                "cvss_score": v.cvss_score,
                "description": v.description,
                "affected_versions": v.affected_versions,
                "fix_available": v.fix_available,
                "fix_version": v.fix_version,
            }
            for v in vulns
        ]
