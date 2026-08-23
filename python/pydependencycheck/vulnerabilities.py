"""Vulnerability analysis and risk assessment

NOTE: This is a pure-Python OSV.dev client kept for reference/library use.
The CLI's `health` and `gate` commands do *not* use this module -- they use
`DependencyScanner.check_vulnerabilities()`, which calls the Rust
`pydep-security` crate's OSV client (faster, and covered by the Rust test
suite). This module currently has no test coverage of its own and is not
imported anywhere in the CLI; it's left in place as a documented,
honestly-labeled pure-Python fallback rather than silently dead code.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


@dataclass
class VulnerabilityReport:
    """Report on detected vulnerabilities"""

    package: str
    version: Optional[str]
    vulnerabilities: List["Vulnerability"] = None
    risk_score: int = 0
    rating: str = "unknown"

    def __post_init__(self):
        if self.vulnerabilities is None:
            self.vulnerabilities = []


@dataclass
class Vulnerability:
    """Single CVE/vulnerability"""

    id: str
    summary: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    cvss_score: Optional[float] = None
    affected_versions: List[str] = None
    fixed_version: Optional[str] = None
    published: Optional[str] = None
    references: List[str] = None

    def __post_init__(self):
        if self.affected_versions is None:
            self.affected_versions = []
        if self.references is None:
            self.references = []


class VulnerabilityAnalyzer:
    """Analyze vulnerabilities using OSV and PyPI"""

    OSV_API = "https://api.osv.dev/v1/query"
    CACHE_TTL = 7 * 24 * 3600  # 7 days

    def __init__(self):
        self.cache: Dict[str, Tuple[List[Vulnerability], datetime]] = {}
        self.session = requests.Session()

    def analyze_package(self, package: str, version: Optional[str] = None) -> VulnerabilityReport:
        """Analyze a package for known vulnerabilities"""
        report = VulnerabilityReport(package=package, version=version)

        # Try cache first
        cache_key = f"{package}@{version}" if version else package
        if cache_key in self.cache:
            vulns, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < self.CACHE_TTL:
                report.vulnerabilities = vulns
                report.risk_score = self._compute_risk_score(vulns)
                report.rating = self._score_to_rating(report.risk_score)
                return report

        # Query OSV
        try:
            vulns = self._query_osv(package, version)
            self.cache[cache_key] = (vulns, datetime.now())
            report.vulnerabilities = vulns
        except Exception as e:
            logger.warning(f"Failed to query OSV for {package}: {e}")

        report.risk_score = self._compute_risk_score(report.vulnerabilities)
        report.rating = self._score_to_rating(report.risk_score)

        return report

    def _query_osv(self, package: str, version: Optional[str] = None) -> List[Vulnerability]:
        """Query OSV API for vulnerabilities"""
        vulns = []

        # Build query
        query = {
            "package": {"ecosystem": "PyPI", "name": package},
        }

        if version:
            query["version"] = version

        try:
            response = self.session.post(self.OSV_API, json=query, timeout=10)
            response.raise_for_status()

            data = response.json()
            for vuln_data in data.get("vulns", []):
                vuln = Vulnerability(
                    id=vuln_data.get("id", ""),
                    summary=vuln_data.get("summary", ""),
                    severity=self._extract_severity(vuln_data),
                    cvss_score=vuln_data.get("cvss_v3_score"),
                    affected_versions=vuln_data.get("affected", []),
                    fixed_version=vuln_data.get("fixed_version"),
                    published=vuln_data.get("published"),
                    references=[ref.get("url") for ref in vuln_data.get("references", []) if ref.get("url")],
                )
                vulns.append(vuln)

        except requests.RequestException as e:
            logger.error(f"OSV API error: {e}")

        return vulns

    def _extract_severity(self, vuln_data: Dict) -> str:
        """Extract severity from OSV data"""
        # Try CVSS score first
        if cvss := vuln_data.get("cvss_v3_score"):
            if cvss >= 9.0:
                return "CRITICAL"
            elif cvss >= 7.0:
                return "HIGH"
            elif cvss >= 4.0:
                return "MEDIUM"
            else:
                return "LOW"

        # Try explicit severity field
        if severity := vuln_data.get("severity"):
            return severity.upper()

        return "MEDIUM"

    def _compute_risk_score(self, vulns: List[Vulnerability]) -> int:
        """Compute overall risk score (0-100)"""
        if not vulns:
            return 0

        total_score = 0
        for vuln in vulns:
            if vuln.cvss_score:
                total_score += int(vuln.cvss_score * 10)
            else:
                # Estimate from severity
                severity_scores = {
                    "CRITICAL": 95,
                    "HIGH": 75,
                    "MEDIUM": 50,
                    "LOW": 25,
                }
                total_score += severity_scores.get(vuln.severity, 50)

        # Average across vulnerabilities, capped at 100
        average = min(total_score // len(vulns), 100)
        return average

    def _score_to_rating(self, score: int) -> str:
        """Convert score to rating"""
        if score >= 80:
            return "Critical"
        elif score >= 60:
            return "High"
        elif score >= 40:
            return "Medium"
        elif score >= 20:
            return "Low"
        else:
            return "Minimal"

    def analyze_project(self, dependencies: List[Dict]) -> Dict:
        """Analyze vulnerabilities across all dependencies"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_packages": len(dependencies),
            "packages_with_vulns": 0,
            "total_vulns": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "packages": [],
        }

        for dep in dependencies:
            package = dep.get("name", "")
            version = dep.get("version")

            report = self.analyze_package(package, version)

            if report.vulnerabilities:
                results["packages_with_vulns"] += 1
                results["packages"].append(
                    {
                        "name": package,
                        "version": version,
                        "vulnerabilities": [
                            {
                                "id": v.id,
                                "summary": v.summary,
                                "severity": v.severity,
                                "cvss_score": v.cvss_score,
                            }
                            for v in report.vulnerabilities
                        ],
                        "risk_score": report.risk_score,
                        "rating": report.rating,
                    }
                )

                # Count by severity
                for vuln in report.vulnerabilities:
                    results["total_vulns"] += 1
                    if vuln.severity == "CRITICAL":
                        results["critical"] += 1
                    elif vuln.severity == "HIGH":
                        results["high"] += 1
                    elif vuln.severity == "MEDIUM":
                        results["medium"] += 1
                    else:
                        results["low"] += 1

        return results
