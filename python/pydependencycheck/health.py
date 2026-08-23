"""Health score calculation and dependency analysis"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# A package with no release in this many days is considered stale for the
# purposes of the "maintenance" health factor.
STALE_THRESHOLD_DAYS = 365


class PackageStalenessChecker:
    """Determine dependency staleness from real PyPI release metadata.

    A package is "stale" if its most recent release predates
    `STALE_THRESHOLD_DAYS`. This mirrors the network-lookup pattern already
    used by `LicenseAnalyzer`/`VulnerabilityAnalyzer`: a short-timeout GET
    against PyPI's public JSON API, with failures logged and treated as
    "unknown" (never counted as stale) rather than raising.
    """

    PYPI_URL = "https://pypi.org/pypi/{name}/json"

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    def last_release_date(self, package_name: str) -> Optional[datetime]:
        """Return the upload time of the most recent release, if known."""
        try:
            response = requests.get(self.PYPI_URL.format(name=package_name), timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.debug(f"Failed to fetch PyPI metadata for {package_name}: {e}")
            return None

        latest_upload: Optional[datetime] = None
        releases = data.get("releases", {})
        for files in releases.values():
            for file_info in files:
                upload_time = file_info.get("upload_time_iso_8601") or file_info.get("upload_time")
                if not upload_time:
                    continue
                try:
                    parsed = datetime.fromisoformat(upload_time.replace("Z", "+00:00"))
                except ValueError:
                    continue
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                if latest_upload is None or parsed > latest_upload:
                    latest_upload = parsed

        return latest_upload

    def is_stale(self, package_name: str, days_threshold: int = STALE_THRESHOLD_DAYS) -> bool:
        """Return True only when we positively know the package is stale.

        Unknown (network failure, no releases found) intentionally returns
        False rather than penalizing a package we couldn't actually check.
        """
        last_release = self.last_release_date(package_name)
        if last_release is None:
            return False
        age_days = (datetime.now(timezone.utc) - last_release).days
        return age_days > days_threshold

    def find_stale_packages(self, dependencies: List[Dict], days_threshold: int = STALE_THRESHOLD_DAYS) -> List[str]:
        """Find declared dependencies with no release in `days_threshold` days."""
        stale = []
        for dep in dependencies:
            name = dep.get("name")
            if not name:
                continue
            if self.is_stale(name, days_threshold=days_threshold):
                stale.append(name)
        return stale


@dataclass
class HealthScore:
    """Overall dependency health score"""

    score: int  # 0-100
    rating: str  # Excellent, Good, Fair, Poor, Critical
    vulnerabilities_score: int
    maintenance_score: int
    complexity_score: int
    quality_score: int
    issues: List[str] = None
    recommendations: List[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.recommendations is None:
            self.recommendations = []


class HealthAnalyzer:
    """Analyze overall dependency health"""

    def __init__(self):
        pass

    def compute_health_score(
        self,
        dependencies: List[Dict],
        vulnerabilities_by_pkg: Dict[str, List],
        dead_deps: List[str],
        stale_packages: List[str],
        import_analysis: Optional[Dict] = None,
    ) -> HealthScore:
        """Compute overall health score"""

        # Component scores
        vuln_score = self._score_vulnerabilities(vulnerabilities_by_pkg, len(dependencies))
        maintenance_score = self._score_maintenance(stale_packages, len(dependencies))
        quality_score = self._score_quality(dead_deps, len(dependencies))
        complexity_score = self._score_complexity(len(dependencies), import_analysis)

        # Weighted average
        total_score = (
            vuln_score * 0.40  # 40% weight - security is critical
            + maintenance_score * 0.30  # 30% weight
            + quality_score * 0.20  # 20% weight
            + complexity_score * 0.10  # 10% weight
        )

        health_score = int(total_score)

        # Determine rating
        rating = self._score_to_rating(health_score)

        # Identify issues and recommendations
        issues = self._identify_issues(vulnerabilities_by_pkg, stale_packages, dead_deps, health_score)
        recommendations = self._make_recommendations(vulnerabilities_by_pkg, stale_packages, dead_deps, import_analysis)

        return HealthScore(
            score=health_score,
            rating=rating,
            vulnerabilities_score=vuln_score,
            maintenance_score=maintenance_score,
            complexity_score=complexity_score,
            quality_score=quality_score,
            issues=issues,
            recommendations=recommendations,
        )

    def _score_vulnerabilities(self, vulns_by_pkg: Dict[str, List], total_deps: int) -> int:
        """Score based on vulnerabilities (0-100)"""
        if not vulns_by_pkg:
            return 100

        critical_count = sum(
            1 for vulns in vulns_by_pkg.values() if any(v.get("severity") == "CRITICAL" for v in vulns)
        )

        high_count = sum(1 for vulns in vulns_by_pkg.values() if any(v.get("severity") == "HIGH" for v in vulns))

        # Deduct points
        score = 100
        score -= critical_count * 20  # Each critical package: -20
        score -= high_count * 10  # Each high severity: -10

        return max(0, min(100, score))

    def _score_maintenance(self, stale_packages: List[str], total_deps: int) -> int:
        """Score based on package age/maintenance"""
        if not stale_packages:
            return 100

        stale_ratio = len(stale_packages) / max(1, total_deps)

        if stale_ratio > 0.5:
            return 30  # More than half are stale
        elif stale_ratio > 0.25:
            return 50
        elif stale_ratio > 0.1:
            return 75
        else:
            return 90

    def _score_quality(self, dead_deps: List[str], total_deps: int) -> int:
        """Score based on dead/unused dependencies"""
        if not dead_deps:
            return 100

        dead_ratio = len(dead_deps) / max(1, total_deps)

        if dead_ratio > 0.3:
            return 40  # 30%+ are dead
        elif dead_ratio > 0.1:
            return 60
        elif dead_ratio > 0.05:
            return 80
        else:
            return 95

    def _score_complexity(self, total_deps: int, import_analysis: Optional[Dict]) -> int:
        """Score based on dependency complexity"""
        # Penalize high transitive dependency counts
        if total_deps > 100:
            return 40  # Very complex
        elif total_deps > 50:
            return 60
        elif total_deps > 20:
            return 80
        else:
            return 95

    def _score_to_rating(self, score: int) -> str:
        """Convert score to rating"""
        if score >= 80:
            return "Excellent"
        elif score >= 65:
            return "Good"
        elif score >= 50:
            return "Fair"
        elif score >= 35:
            return "Poor"
        else:
            return "Critical"

    def _identify_issues(
        self,
        vulns: Dict[str, List],
        stale: List[str],
        dead: List[str],
        score: int,
    ) -> List[str]:
        """Identify main issues affecting health"""
        issues = []

        # Critical vulnerabilities
        critical_packages = [
            pkg for pkg, v_list in vulns.items() if any(v.get("severity") == "CRITICAL" for v in v_list)
        ]
        if critical_packages:
            issues.append(f"🚨 {len(critical_packages)} packages with critical vulnerabilities")

        # Stale packages
        if stale:
            issues.append(f"⚠️ {len(stale)} packages not updated in 12+ months")

        # Dead dependencies
        if dead:
            issues.append(f"📦 {len(dead)} unused dependencies")

        # Overall score
        if score < 50:
            issues.append("⛔ Overall health score below 50 - immediate action recommended")

        return issues

    def _make_recommendations(
        self,
        vulns: Dict[str, List],
        stale: List[str],
        dead: List[str],
        import_analysis: Optional[Dict],
    ) -> List[str]:
        """Make actionable recommendations"""
        recommendations = []

        # Fix critical vulnerabilities
        critical = [pkg for pkg, v_list in vulns.items() if any(v.get("severity") == "CRITICAL" for v in v_list)]
        if critical:
            recommendations.append(f"Upgrade {critical[0]} to fix critical vulnerability")

        # Update stale packages
        if stale:
            recommendations.append(f"Update {len(stale)} stale packages (>12 months old)")

        # Remove dead dependencies
        if dead:
            shown = ", ".join(dead[:3])
            suffix = f" (and {len(dead) - 3} more)" if len(dead) > 3 else ""
            recommendations.append(f"Remove or audit {len(dead)} unused dependencies: {shown}{suffix}")

        # Reduce complexity
        if len(critical) + len(stale) + len(dead) > 10:
            recommendations.append("Consider refactoring to reduce overall complexity")

        return recommendations
