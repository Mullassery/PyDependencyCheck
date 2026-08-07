"""Dependency Scanner: Orchestrates parsing, analysis, and reporting"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import logging
import json

logger = logging.getLogger(__name__)

# Try to import Rust backend
try:
    from . import _pydependencycheck

    HAS_RUST_BACKEND = True
except ImportError:
    HAS_RUST_BACKEND = False
    logger.warning("Rust backend not available, using pure Python (slower)")


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

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.found_files: List[Path] = []
        self.parsed_deps: List[Dict[str, Any]] = []

    def find_dependency_files(self) -> List[Path]:
        """Auto-detect dependency declaration files"""
        found = []
        for pattern in self.DEPENDENCY_FILES:
            matches = list(self.project_path.glob(f"**/{pattern}"))
            found.extend(matches)

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
                if dep["name"] not in dependencies:
                    dependencies[dep["name"]] = dep
                else:
                    # Merge version constraints if seen in multiple files
                    existing = dependencies[dep["name"]]
                    existing["sources"].append(dep.get("source", str(file_path)))

        self.parsed_deps = list(dependencies.values())
        return self.parsed_deps

    def _parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a single dependency file"""
        file_name = file_path.name.lower()

        if "requirements" in file_name or file_name == "constraints.txt":
            return self._parse_requirements_txt(file_path)
        elif file_name == "pyproject.toml":
            return self._parse_pyproject_toml(file_path)
        elif file_name in ("setup.py", "setup.cfg"):
            return self._parse_setup_file(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_name}")
            return []

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
        """Analyze which dependencies are actually used"""
        # TODO: Scan source code for imports (Phase 2)
        return {}

    def check_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Check parsed dependencies against the OSV.dev vulnerability database.

        Only pinned dependencies (those with a resolved version) can be
        checked meaningfully, since OSV's SEMVER range matching needs a
        concrete version to test against.
        """
        if not HAS_RUST_BACKEND:
            logger.warning("Rust backend not available, skipping vulnerability scan")
            return []

        pinned = [
            (dep["name"], dep["version"])
            for dep in self.parsed_deps
            if dep.get("version")
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

    def compute_health_score(self) -> int:
        """Compute overall health score (0-100)"""
        # TODO: Aggregate multiple metrics (Phase 3)
        return 50
