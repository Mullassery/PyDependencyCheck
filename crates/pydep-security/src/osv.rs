use crate::{Vulnerability, Severity, SecurityResult};
use std::collections::HashMap;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsvVulnerability {
    pub id: String,
    pub summary: String,
    pub details: Option<String>,
    pub affected: Vec<OsvAffected>,
    pub references: Vec<OsvReference>,
    pub published: Option<String>,
    pub modified: Option<String>,
    pub severity: Option<String>,
    pub cvss_v3_score: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsvAffected {
    pub package: OsvPackage,
    pub ranges: Option<Vec<OsvRange>>,
    pub versions: Option<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsvPackage {
    pub ecosystem: String,
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsvRange {
    pub r#type: String, // "SEMVER", "GIT", etc.
    pub events: Vec<OsvEvent>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsvEvent {
    pub introduced: Option<String>,
    pub fixed: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsvReference {
    pub r#type: String,
    pub url: String,
}

/// OSV Database client (in-memory mock for now)
pub struct OsvClient {
    vulnerabilities: HashMap<String, Vec<OsvVulnerability>>,
}

impl OsvClient {
    pub fn new() -> Self {
        Self {
            vulnerabilities: HashMap::new(),
        }
    }

    /// Query vulnerabilities for a package synchronously
    pub fn query_package(
        &self,
        package: &str,
        version: Option<&str>,
    ) -> SecurityResult<Vec<Vulnerability>> {
        let vulns = self.vulnerabilities.get(&package.to_lowercase())
            .cloned()
            .unwrap_or_default();

        let mut results = Vec::new();

        for vuln in vulns {
            // Check if vulnerability affects this version
            if let Some(version_str) = version {
                if self.version_affected(&vuln, version_str) {
                    results.push(self.osv_to_vuln(&vuln, package));
                }
            } else {
                // No version specified, include all
                results.push(self.osv_to_vuln(&vuln, package));
            }
        }

        Ok(results)
    }

    /// Check if a version is affected by vulnerability
    fn version_affected(&self, vuln: &OsvVulnerability, version: &str) -> bool {
        // Simplified: check if version matches affected versions
        for affected in &vuln.affected {
            if let Some(versions) = &affected.versions {
                if versions.contains(&version.to_string()) {
                    return true;
                }
            }
            // TODO: Implement semver range checking for ranges
        }
        false
    }

    /// Convert OSV format to internal Vulnerability
    fn osv_to_vuln(&self, osv: &OsvVulnerability, package: &str) -> Vulnerability {
        let severity = if let Some(cvss) = osv.cvss_v3_score {
            crate::scoring::RiskScorer::cvss_to_severity(cvss)
        } else {
            Severity::Medium
        };

        Vulnerability {
            id: osv.id.clone(),
            package_name: package.to_string(),
            package_version: None,
            severity,
            cvss_score: osv.cvss_v3_score,
            description: osv.summary.clone(),
            affected_versions: osv.affected
                .iter()
                .flat_map(|a| a.versions.clone().unwrap_or_default())
                .collect(),
            fix_available: osv.affected
                .iter()
                .any(|a| a.ranges.as_ref()
                    .and_then(|r| r.iter().find(|range| range.events.iter().any(|e| e.fixed.is_some())))
                    .is_some()),
            fix_version: osv.affected
                .iter()
                .find_map(|a| a.ranges.as_ref())
                .and_then(|ranges| ranges.iter()
                    .find_map(|r| r.events.iter()
                        .find_map(|e| e.fixed.clone()))),
        }
    }

    /// Load known vulnerabilities for common packages (mock data)
    pub fn load_known_vulns(&mut self) {
        // Mock vulnerability data for testing
        // In production, this would load from OSV database

        let mut django_vulns = Vec::new();

        // Example CVE for Django
        django_vulns.push(OsvVulnerability {
            id: "GHSA-xxxx-xxxx-xxxx".to_string(),
            summary: "SQL Injection in Django ORM".to_string(),
            details: Some("A SQL injection vulnerability in Django's ORM...".to_string()),
            affected: vec![OsvAffected {
                package: OsvPackage {
                    ecosystem: "PyPI".to_string(),
                    name: "django".to_string(),
                },
                ranges: Some(vec![OsvRange {
                    r#type: "SEMVER".to_string(),
                    events: vec![
                        OsvEvent { introduced: Some("2.0.0".to_string()), fixed: None },
                        OsvEvent { introduced: None, fixed: Some("3.2.5".to_string()) },
                    ],
                }]),
                versions: None,
            }],
            references: vec![OsvReference {
                r#type: "ADVISORY".to_string(),
                url: "https://github.com/advisories/...".to_string(),
            }],
            published: Some("2021-01-01T00:00:00Z".to_string()),
            modified: None,
            severity: Some("HIGH".to_string()),
            cvss_v3_score: Some(7.5),
        });

        self.vulnerabilities.insert("django".to_string(), django_vulns);
    }

    /// Check if OSV snapshot is available
    pub fn has_snapshot(&self) -> bool {
        !self.vulnerabilities.is_empty()
    }
}

impl Default for OsvClient {
    fn default() -> Self {
        Self::new()
    }
}
