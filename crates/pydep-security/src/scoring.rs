use crate::{Vulnerability, Severity, SecurityResult};
use std::collections::HashMap;

/// Risk scoring for dependencies
pub struct RiskScorer;

impl RiskScorer {
    /// Compute risk score for a single package (0-100)
    /// Factors:
    /// - Vulnerabilities (40 points)
    /// - Maintenance (30 points)
    /// - Popularity (20 points)
    /// - Age (10 points)
    pub fn score_package(
        vulnerabilities: &[Vulnerability],
        maintenance_days_since_release: u32,
        downloads_per_month: u64,
    ) -> SecurityResult<u32> {
        let mut score = 100u32;

        // Vulnerability impact (max -40 points)
        let vuln_penalty = vulnerabilities.iter()
            .map(|v| match v.severity {
                Severity::Critical => 20,
                Severity::High => 10,
                Severity::Medium => 5,
                Severity::Low => 2,
                Severity::Informational => 1,
            })
            .sum::<u32>()
            .min(40);
        score -= vuln_penalty;

        // Maintenance impact (max -30 points)
        // Penalize old packages (>2 years since release)
        let maintenance_penalty = if maintenance_days_since_release > 730 {
            30 // Very stale
        } else if maintenance_days_since_release > 365 {
            20 // Stale
        } else if maintenance_days_since_release > 180 {
            10 // Outdated
        } else {
            0 // Recent
        };
        score = score.saturating_sub(maintenance_penalty);

        // Popularity impact (max -20 points)
        // Reward popular packages, penalize obscure ones
        let popularity_penalty = if downloads_per_month < 100 {
            20 // Rarely used
        } else if downloads_per_month < 1000 {
            10 // Niche
        } else if downloads_per_month > 1_000_000 {
            0 // Widely used
        } else {
            5 // Moderate popularity
        };
        score = score.saturating_sub(popularity_penalty);

        Ok(score.max(0))
    }

    /// Propagate risk through dependency chain
    /// Each dependency layer increases risk slightly
    pub fn propagate_risk(base_score: u32, chain_length: usize) -> SecurityResult<u32> {
        if chain_length <= 1 {
            return Ok(base_score);
        }

        // Each additional layer degrades score by 2%
        let degradation = (chain_length as u32 - 1) * 2;
        let degraded = (base_score * (100 - degradation.min(80))) / 100;

        Ok(degraded)
    }

    /// Compute health score (0-100) for all dependencies
    /// Formula:
    /// base = 100
    /// - (critical_vulns × 20)
    /// - (high_vulns × 10)
    /// - (stale_packages × 5)
    /// - min(dead_dependencies × 3, 15)
    /// - min(transitive_depth / 2, 10)
    pub fn compute_health_score(
        vulnerabilities: &[Vulnerability],
        stale_packages: usize,
        dead_dependencies: usize,
        transitive_depth: usize,
    ) -> SecurityResult<u32> {
        let mut score = 100i32;

        // Count vulnerabilities by severity
        let critical_count = vulnerabilities.iter().filter(|v| v.severity == Severity::Critical).count() as i32;
        let high_count = vulnerabilities.iter().filter(|v| v.severity == Severity::High).count() as i32;
        let medium_count = vulnerabilities.iter().filter(|v| v.severity == Severity::Medium).count() as i32;

        score -= critical_count * 20;
        score -= high_count * 10;
        score -= medium_count * 3;

        // Stale packages
        score -= (stale_packages as i32 * 5).min(25);

        // Dead dependencies
        score -= (dead_dependencies as i32 * 3).min(15);

        // Transitive depth (complexity penalty)
        score -= (transitive_depth as i32 / 2).min(10);

        Ok((score.max(0) as u32).min(100))
    }

    /// Get a risk rating label
    pub fn score_to_rating(score: u32) -> &'static str {
        match score {
            90..=100 => "Excellent",
            75..=89 => "Good",
            50..=74 => "Fair",
            25..=49 => "Poor",
            _ => "Critical",
        }
    }

    /// Convert CVSS score to severity
    pub fn cvss_to_severity(cvss_score: f64) -> Severity {
        match cvss_score {
            9.0..=10.0 => Severity::Critical,
            7.0..=8.9 => Severity::High,
            4.0..=6.9 => Severity::Medium,
            0.1..=3.9 => Severity::Low,
            _ => Severity::Informational,
        }
    }

    /// Aggregate risk across multiple packages
    pub fn aggregate_risk(package_scores: &HashMap<String, u32>) -> u32 {
        if package_scores.is_empty() {
            return 100;
        }

        let sum: u32 = package_scores.values().sum();
        sum / package_scores.len() as u32
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_score_package_clean() {
        let score = RiskScorer::score_package(&[], 30, 100_000).unwrap();
        assert!(score > 80);
    }

    #[test]
    fn test_score_package_vulnerable() {
        let vuln = Vulnerability {
            id: "CVE-2024-1234".to_string(),
            package_name: "test".to_string(),
            package_version: Some("1.0".to_string()),
            severity: Severity::Critical,
            cvss_score: Some(9.5),
            description: "Critical vulnerability".to_string(),
            affected_versions: vec!["1.0".to_string()],
            fix_available: true,
            fix_version: Some("1.0.1".to_string()),
        };

        let score = RiskScorer::score_package(&[vuln], 30, 100_000).unwrap();
        assert!(score < 100);
    }

    #[test]
    fn test_cvss_to_severity() {
        assert_eq!(RiskScorer::cvss_to_severity(9.5), Severity::Critical);
        assert_eq!(RiskScorer::cvss_to_severity(7.5), Severity::High);
        assert_eq!(RiskScorer::cvss_to_severity(5.0), Severity::Medium);
    }

    #[test]
    fn test_score_to_rating() {
        assert_eq!(RiskScorer::score_to_rating(95), "Excellent");
        assert_eq!(RiskScorer::score_to_rating(72), "Fair");
        assert_eq!(RiskScorer::score_to_rating(15), "Critical");
    }
}
