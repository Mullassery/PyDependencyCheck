//! PyDependencyCheck Security: Vulnerability and risk analysis
//!
//! Integrates with:
//! - OSV (Open Source Vulnerabilities) database
//! - PyPI advisories
//! - CVSS scoring

pub mod osv;
pub mod scoring;
pub mod cache;
pub mod errors;

pub use errors::{SecurityError, SecurityResult};

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Vulnerability {
    pub id: String,
    pub package_name: String,
    pub package_version: Option<String>,
    pub severity: Severity,
    pub cvss_score: Option<f64>,
    pub description: String,
    pub affected_versions: Vec<String>,
    pub fix_available: bool,
    pub fix_version: Option<String>,
}

#[derive(Debug, Clone, Copy, serde::Serialize, serde::Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum Severity {
    Critical = 4,
    High = 3,
    Medium = 2,
    Low = 1,
    Informational = 0,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_severity_ordering() {
        assert!(Severity::Critical > Severity::High);
        assert!(Severity::High > Severity::Medium);
    }
}
