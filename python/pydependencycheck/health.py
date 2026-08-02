"""Health score calculation and dependency analysis"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


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
            recommendations.append(
                f"Remove or audit {len(dead[:3])} unused dependencies "
                f"({'and ' + str(len(dead) - 3) + ' more' if len(dead) > 3 else ''})"
            )

        # Reduce complexity
        if len(critical) + len(stale) + len(dead) > 10:
            recommendations.append("Consider refactoring to reduce overall complexity")

        return recommendations
