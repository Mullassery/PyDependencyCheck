"""License detection and compliance checking"""

from typing import Dict, List, Optional, Tuple
import requests
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# SPDX license categories
PERMISSIVE_LICENSES = {
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "MPL-2.0",
    "Python-2.0",
    "WTFPL",
    "Zlib",
    "CC0-1.0",
}

COPYLEFT_LICENSES = {"GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0", "AGPL-3.0"}

RESTRICTED_LICENSES = {"AGPL-3.0", "GPL-3.0", "GPL-2.0"}  # Restrictive for proprietary software


@dataclass
class LicenseInfo:
    """License information for a package"""

    package: str
    version: Optional[str] = None
    licenses: List[str] = None
    primary_license: Optional[str] = None
    is_spdx_valid: bool = False
    risk_level: str = "unknown"  # permissive, restricted, unknown, incompatible

    def __post_init__(self):
        if self.licenses is None:
            self.licenses = []

    def __str__(self) -> str:
        license_str = ", ".join(self.licenses) if self.licenses else "Unknown"
        return f"{self.package}: {license_str} ({self.risk_level})"


class LicenseAnalyzer:
    """Analyze and detect licenses in dependencies"""

    def __init__(self, cache_licenses: bool = True):
        self.cache: Dict[str, LicenseInfo] = {}
        self.cache_licenses = cache_licenses

    def analyze_package(self, package_name: str, version: Optional[str] = None) -> LicenseInfo:
        """Analyze a package for licenses"""
        cache_key = f"{package_name}@{version}" if version else package_name

        if cache_key in self.cache:
            return self.cache[cache_key]

        info = LicenseInfo(package=package_name, version=version)

        # Try to fetch from PyPI
        try:
            info = self._fetch_from_pypi(package_name, version)
        except Exception as e:
            logger.debug(f"Failed to fetch license from PyPI: {e}")

        # Classify risk level
        info = self._classify_risk(info)

        if self.cache_licenses:
            self.cache[cache_key] = info

        return info

    def _fetch_from_pypi(self, package_name: str, version: Optional[str] = None) -> LicenseInfo:
        """Fetch license information from PyPI"""
        url = f"https://pypi.org/pypi/{package_name}/json"

        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        info = data.get("info", {})

        licenses = []
        classifiers = info.get("classifiers", [])

        # Extract license from classifiers
        for classifier in classifiers:
            if classifier.startswith("License :: OSI Approved ::"):
                license_name = classifier.replace("License :: OSI Approved :: ", "")
                licenses.append(license_name)

        # Also check license field
        license_field = info.get("license")
        if license_field and license_field.strip():
            licenses.append(license_field)

        version_used = version or info.get("version", "unknown")
        result = LicenseInfo(
            package=package_name,
            version=version_used,
            licenses=licenses,
            primary_license=licenses[0] if licenses else None,
            is_spdx_valid=any(self._is_spdx_license(l) for l in licenses),
        )

        return result

    def _classify_risk(self, info: LicenseInfo) -> LicenseInfo:
        """Classify the risk level of a license"""
        if not info.licenses:
            info.risk_level = "unknown"
            return info

        # Check for any restrictive licenses
        for license_name in info.licenses:
            normalized = self._normalize_license(license_name)

            if normalized in RESTRICTED_LICENSES:
                info.risk_level = "restricted"
                return info

            if normalized in COPYLEFT_LICENSES:
                info.risk_level = "copyleft"
                return info

        # Check for permissive licenses
        for license_name in info.licenses:
            normalized = self._normalize_license(license_name)
            if normalized in PERMISSIVE_LICENSES:
                info.risk_level = "permissive"
                return info

        info.risk_level = "unknown"
        return info

    def check_compatibility(self, project_license: str, dependency_licenses: List[str]) -> Tuple[bool, List[str]]:
        """Check if dependency licenses are compatible with project license"""
        conflicts = []

        project_normalized = self._normalize_license(project_license)

        for dep_license in dependency_licenses:
            dep_normalized = self._normalize_license(dep_license)

            # MIT is compatible with almost everything
            if dep_normalized == "MIT" or project_normalized == "MIT":
                continue

            # GPL conflicts with most permissive licenses for proprietary projects
            if dep_normalized in RESTRICTED_LICENSES and project_normalized in PERMISSIVE_LICENSES:
                conflicts.append(f"Restrictive {dep_normalized} incompatible with {project_normalized}")

            # Mismatched GPL versions
            if dep_normalized in COPYLEFT_LICENSES and project_normalized in COPYLEFT_LICENSES:
                if dep_normalized != project_normalized:
                    conflicts.append(f"Different copyleft versions: {project_normalized} vs {dep_normalized}")

        return len(conflicts) == 0, conflicts

    def _is_spdx_license(self, license_name: str) -> bool:
        """Check if license is valid SPDX identifier"""
        # Simplified check - in production would use full SPDX list
        known_spdx = PERMISSIVE_LICENSES | COPYLEFT_LICENSES | RESTRICTED_LICENSES
        return self._normalize_license(license_name) in known_spdx

    def _normalize_license(self, license_name: str) -> str:
        """Normalize license name to SPDX format"""
        normalized = license_name.upper().strip()

        # Common mappings
        mappings = {
            "MIT LICENSE": "MIT",
            "APACHE 2.0": "Apache-2.0",
            "APACHE SOFTWARE LICENSE": "Apache-2.0",
            "BSD LICENSE": "BSD-3-Clause",
            "GNU GPL": "GPL-2.0",
            "GNU GENERAL PUBLIC LICENSE": "GPL-2.0",
            "GPL V3": "GPL-3.0",
            "GPL V2": "GPL-2.0",
            "MOZILLA PUBLIC LICENSE": "MPL-2.0",
        }

        for key, value in mappings.items():
            if key in normalized:
                return value

        return license_name

    def analyze_project_licenses(self, dependencies: List[Dict]) -> Dict[str, any]:
        """Analyze licenses for all dependencies"""
        results = {
            "total": len(dependencies),
            "permissive": 0,
            "copyleft": 0,
            "restricted": 0,
            "unknown": 0,
            "conflicts": [],
            "packages": [],
        }

        for dep in dependencies:
            package_name = dep.get("name", "")
            version = dep.get("version")

            info = self.analyze_package(package_name, version)
            results["packages"].append(
                {
                    "name": package_name,
                    "licenses": info.licenses,
                    "risk": info.risk_level,
                }
            )

            if info.risk_level == "permissive":
                results["permissive"] += 1
            elif info.risk_level == "copyleft":
                results["copyleft"] += 1
            elif info.risk_level == "restricted":
                results["restricted"] += 1
            else:
                results["unknown"] += 1

        return results


class DeadDependencyDetector:
    """Detect unused/dead dependencies"""

    def __init__(self):
        self.threshold_low = 1  # Used only once
        self.threshold_medium = 0  # Never used

    def find_dead_dependencies(self, declared: List[str], used: List[str]) -> Dict[str, any]:
        """Find potentially dead dependencies"""
        declared_set = {p.lower().replace("_", "-") for p in declared}
        used_set = {p.lower().replace("_", "-") for p in used}

        definitely_dead = declared_set - used_set
        probably_dead = []  # Low usage threshold

        result = {
            "definitely_dead": sorted(list(definitely_dead)),
            "probably_dead": probably_dead,
            "recommendations": [],
        }

        if definitely_dead:
            result["recommendations"].append(f"Consider removing {len(definitely_dead)} packages that are not imported")

        return result
