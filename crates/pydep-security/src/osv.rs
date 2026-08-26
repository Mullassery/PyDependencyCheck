use crate::cache::VulnerabilityCache;
use crate::{SecurityError, SecurityResult, Severity, Vulnerability};
use semver::Version;
use serde::{Deserialize, Serialize};

const OSV_API_URL: &str = "https://api.osv.dev/v1/query";
const ECOSYSTEM: &str = "PyPI";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsvVulnerability {
    pub id: String,
    #[serde(default)]
    pub summary: Option<String>,
    #[serde(default)]
    pub details: Option<String>,
    #[serde(default)]
    pub affected: Vec<OsvAffected>,
    #[serde(default)]
    pub references: Vec<OsvReference>,
    #[serde(default)]
    pub published: Option<String>,
    #[serde(default)]
    pub modified: Option<String>,
    #[serde(default)]
    pub severity: Vec<OsvSeverity>,
    #[serde(default)]
    pub database_specific: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsvSeverity {
    #[serde(rename = "type")]
    pub kind: String,
    pub score: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsvAffected {
    #[serde(default)]
    pub package: Option<OsvPackage>,
    #[serde(default)]
    pub ranges: Option<Vec<OsvRange>>,
    #[serde(default)]
    pub versions: Option<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsvPackage {
    pub ecosystem: String,
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsvRange {
    pub r#type: String, // "SEMVER", "ECOSYSTEM", "GIT", etc.
    pub events: Vec<OsvEvent>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsvEvent {
    #[serde(default)]
    pub introduced: Option<String>,
    #[serde(default)]
    pub fixed: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsvReference {
    #[serde(default)]
    pub r#type: Option<String>,
    pub url: String,
}

#[derive(Debug, Serialize)]
struct OsvQueryPackage<'a> {
    name: &'a str,
    ecosystem: &'a str,
}

#[derive(Debug, Serialize)]
struct OsvQueryRequest<'a> {
    package: OsvQueryPackage<'a>,
    #[serde(skip_serializing_if = "Option::is_none")]
    version: Option<&'a str>,
}

#[derive(Debug, Deserialize)]
struct OsvQueryResponse {
    #[serde(default)]
    vulns: Vec<OsvVulnerability>,
}

/// Client for the OSV.dev vulnerability database, with a 7-day on-disk cache.
pub struct OsvClient {
    http: reqwest::blocking::Client,
    cache: Option<VulnerabilityCache>,
}

impl OsvClient {
    pub fn new() -> Self {
        Self {
            http: reqwest::blocking::Client::builder()
                .user_agent("pydependencycheck/1.0")
                .timeout(std::time::Duration::from_secs(10))
                .build()
                .unwrap_or_else(|_| reqwest::blocking::Client::new()),
            cache: VulnerabilityCache::new().ok(),
        }
    }

    /// Query the live OSV database for a package, optionally scoped to a
    /// specific version. Results are cached on disk for 7 days.
    pub fn query_package(
        &self,
        package: &str,
        version: Option<&str>,
    ) -> SecurityResult<Vec<Vulnerability>> {
        let body = self.fetch_raw(package, version)?;
        let parsed: OsvQueryResponse = serde_json::from_str(&body)
            .map_err(|e| SecurityError::OsvError(format!("failed to parse OSV response: {e}")))?;

        let mut results = Vec::new();
        for vuln in &parsed.vulns {
            match version {
                Some(v) if !self.version_affected(vuln, v) => continue,
                _ => {}
            }
            results.push(self.osv_to_vuln(vuln, package));
        }
        Ok(results)
    }

    /// Fetch the raw OSV response body, using the on-disk cache when fresh.
    fn fetch_raw(&self, package: &str, version: Option<&str>) -> SecurityResult<String> {
        if let Some(cache) = &self.cache {
            if let Some(cached) = cache.get(ECOSYSTEM, package, version) {
                return Ok(cached);
            }
        }

        let request = OsvQueryRequest {
            package: OsvQueryPackage {
                name: package,
                ecosystem: ECOSYSTEM,
            },
            version,
        };

        let response = self
            .http
            .post(OSV_API_URL)
            .json(&request)
            .send()
            .map_err(|e| SecurityError::NetworkError(format!("OSV request failed: {e}")))?;

        if !response.status().is_success() {
            return Err(SecurityError::OsvError(format!(
                "OSV API returned status {}",
                response.status()
            )));
        }

        let body = response.text().map_err(|e| {
            SecurityError::NetworkError(format!("failed to read OSV response: {e}"))
        })?;

        if let Some(cache) = &self.cache {
            let _ = cache.put(ECOSYSTEM, package, version, &body);
        }

        Ok(body)
    }

    /// Check if a version is affected by a vulnerability, using real semver
    /// range comparison against `introduced`/`fixed` events, plus exact
    /// version-list matching for non-range advisories.
    fn version_affected(&self, vuln: &OsvVulnerability, version: &str) -> bool {
        let target = match Version::parse(version) {
            Ok(v) => v,
            // If the version string isn't strict semver (e.g. "1.0" or "1.0.0rc1"),
            // fall back to exact string matching only.
            Err(_) => {
                return vuln.affected.iter().any(|a| {
                    a.versions
                        .as_ref()
                        .is_some_and(|vs| vs.iter().any(|v| v == version))
                });
            }
        };

        for affected in &vuln.affected {
            if let Some(versions) = &affected.versions {
                if versions.iter().any(|v| v == version) {
                    return true;
                }
            }
            if let Some(ranges) = &affected.ranges {
                for range in ranges {
                    if !Self::is_ecosystem_range(range) {
                        continue;
                    }
                    if Self::version_in_range(&target, &range.events) {
                        return true;
                    }
                }
            }
        }
        false
    }

    /// An OSV range's `type` is "SEMVER"/"ECOSYSTEM" (events carry real
    /// package versions) or "GIT" (events carry commit hashes). Only the
    /// former is meaningful for a PyPI version comparison or as a
    /// `fix_version` -- a GIT range's `fixed` commit hash isn't installable
    /// via `pip install package==<version>`.
    fn is_ecosystem_range(range: &OsvRange) -> bool {
        range.r#type == "SEMVER" || range.r#type == "ECOSYSTEM"
    }

    /// SEMVER ranges in OSV are a sorted sequence of introduced/fixed/last_affected
    /// events. A version is affected if it falls at-or-after the most recent
    /// `introduced` bound that precedes it, and before the next `fixed` bound.
    fn version_in_range(target: &Version, events: &[OsvEvent]) -> bool {
        let mut introduced: Option<Version> = None;
        let mut fixed_after_introduction: Option<Version> = None;

        // Events are ordered; find the introduced bound this version falls under,
        // then check whether a fix landed before this version.
        let mut in_window = false;
        for event in events {
            if let Some(intro) = &event.introduced {
                let intro_v = Self::parse_lenient(intro);
                let clears_bound = intro_v.as_ref().map(|v| target >= v).unwrap_or(true); // "0" means "all versions"
                if clears_bound {
                    introduced = intro_v;
                    in_window = true;
                    fixed_after_introduction = None;
                }
            }
            if let Some(fixed) = &event.fixed {
                if in_window {
                    if let Some(fixed_v) = Self::parse_lenient(fixed) {
                        if target < &fixed_v {
                            fixed_after_introduction = None;
                        } else {
                            in_window = false;
                            fixed_after_introduction = Some(fixed_v);
                        }
                    }
                }
            }
        }

        let _ = introduced;
        let _ = fixed_after_introduction;
        in_window
    }

    fn parse_lenient(v: &str) -> Option<Version> {
        Version::parse(v).ok().or_else(|| {
            // Pad "1.2" -> "1.2.0" since OSV ranges often omit the patch component.
            let parts: Vec<&str> = v.split('.').collect();
            if parts.len() == 2 {
                Version::parse(&format!("{v}.0")).ok()
            } else {
                None
            }
        })
    }

    fn osv_to_vuln(&self, osv: &OsvVulnerability, package: &str) -> Vulnerability {
        let severity = Self::derive_severity(osv);
        let cvss_score = osv
            .severity
            .iter()
            .find(|s| s.kind == "CVSS_V3" || s.kind == "CVSS_V4")
            .and_then(|s| Self::cvss_base_score_from_vector(&s.score));

        Vulnerability {
            id: osv.id.clone(),
            package_name: package.to_string(),
            package_version: None,
            severity,
            cvss_score,
            description: osv
                .summary
                .clone()
                .or_else(|| osv.details.clone())
                .unwrap_or_else(|| "No description available".to_string()),
            affected_versions: osv
                .affected
                .iter()
                .flat_map(|a| a.versions.clone().unwrap_or_default())
                .collect(),
            // Only ECOSYSTEM/SEMVER ranges carry a real PyPI version in
            // their `fixed` event -- a GIT range's `fixed` is a commit
            // hash, not something that belongs in a version field (or gets
            // fed into a `pip install package==<this>`). Same filter
            // `version_affected` below already applies when matching
            // against a queried version; this just applies it here too.
            fix_available: osv.affected.iter().any(|a| {
                a.ranges
                    .as_ref()
                    .map(|ranges| {
                        ranges.iter().any(|r| {
                            Self::is_ecosystem_range(r)
                                && r.events.iter().any(|e| e.fixed.is_some())
                        })
                    })
                    .unwrap_or(false)
            }),
            fix_version: osv
                .affected
                .iter()
                .find_map(|a| a.ranges.as_ref())
                .and_then(|ranges| {
                    ranges
                        .iter()
                        .filter(|r| Self::is_ecosystem_range(r))
                        .find_map(|r| r.events.iter().rev().find_map(|e| e.fixed.clone()))
                }),
        }
    }

    /// Prefer the GitHub-Security-Advisory-style `database_specific.severity`
    /// string (present on the large majority of PyPI advisories in OSV);
    /// fall back to bucketing a numeric CVSS base score if that's all we have.
    fn derive_severity(osv: &OsvVulnerability) -> Severity {
        if let Some(db_specific) = &osv.database_specific {
            if let Some(sev_str) = db_specific.get("severity").and_then(|v| v.as_str()) {
                match sev_str.to_uppercase().as_str() {
                    "CRITICAL" => return Severity::Critical,
                    "HIGH" => return Severity::High,
                    "MODERATE" | "MEDIUM" => return Severity::Medium,
                    "LOW" => return Severity::Low,
                    _ => {}
                }
            }
        }

        if let Some(entry) = osv
            .severity
            .iter()
            .find(|s| s.kind == "CVSS_V3" || s.kind == "CVSS_V4")
        {
            if let Some(score) = Self::cvss_base_score_from_vector(&entry.score) {
                return crate::scoring::RiskScorer::cvss_to_severity(score);
            }
        }

        Severity::Medium
    }

    /// Extract the base score component embedded in a CVSS vector string when
    /// present (some OSV sources embed ".../S:U.../score:7.5" style suffixes);
    /// most CVSS_V3 entries from OSV are the vector only with no numeric score,
    /// in which case this returns None and callers fall back to database_specific.
    fn cvss_base_score_from_vector(vector: &str) -> Option<f64> {
        vector
            .split('/')
            .find_map(|part| part.strip_prefix("score:"))
            .and_then(|s| s.parse::<f64>().ok())
    }

    /// Run cache maintenance (removes entries older than the TTL).
    pub fn cleanup_cache(&self) -> SecurityResult<()> {
        match &self.cache {
            Some(cache) => cache.cleanup_stale_cache(),
            None => Ok(()),
        }
    }

    pub fn has_cache(&self) -> bool {
        self.cache.is_some()
    }
}

impl Default for OsvClient {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn range(events: Vec<(Option<&str>, Option<&str>)>) -> Vec<OsvEvent> {
        events
            .into_iter()
            .map(|(i, f)| OsvEvent {
                introduced: i.map(String::from),
                fixed: f.map(String::from),
            })
            .collect()
    }

    #[test]
    fn version_in_range_detects_affected_version() {
        let events = range(vec![(Some("2.0.0"), None), (None, Some("3.2.5"))]);
        let target = Version::parse("2.5.0").unwrap();
        assert!(OsvClient::version_in_range(&target, &events));
    }

    #[test]
    fn version_in_range_excludes_fixed_version() {
        let events = range(vec![(Some("2.0.0"), None), (None, Some("3.2.5"))]);
        let target = Version::parse("3.2.5").unwrap();
        assert!(!OsvClient::version_in_range(&target, &events));
    }

    #[test]
    fn version_in_range_excludes_version_before_introduction() {
        let events = range(vec![(Some("2.0.0"), None), (None, Some("3.2.5"))]);
        let target = Version::parse("1.9.0").unwrap();
        assert!(!OsvClient::version_in_range(&target, &events));
    }

    #[test]
    fn version_in_range_handles_zero_lower_bound() {
        // introduced: "0" means "affected since the beginning of history"
        let events = range(vec![(Some("0"), None), (None, Some("1.5.0"))]);
        let target = Version::parse("0.1.0").unwrap();
        assert!(OsvClient::version_in_range(&target, &events));
    }

    #[test]
    fn derive_severity_prefers_database_specific() {
        let vuln = OsvVulnerability {
            id: "GHSA-test".into(),
            summary: None,
            details: None,
            affected: vec![],
            references: vec![],
            published: None,
            modified: None,
            severity: vec![],
            database_specific: Some(serde_json::json!({"severity": "HIGH"})),
        };
        assert_eq!(OsvClient::derive_severity(&vuln), Severity::High);
    }

    /// Regression test for a real observed bug: PYSEC-2023-74 (a `requests`
    /// advisory) has a GIT-type range (fixed = commit hash) listed before
    /// its ECOSYSTEM range (fixed = real PyPI version) in `affected[0]`.
    /// `osv_to_vuln` used to take the first range with any `fixed` event
    /// regardless of type, so `fix_version` came back as a 40-char commit
    /// hash instead of "2.31.0" -- which is not a valid PyPI version and
    /// broke any caller (e.g. remediation) that tried to use it as one.
    #[test]
    fn fix_version_ignores_git_range_and_uses_ecosystem_range() {
        let vuln = OsvVulnerability {
            id: "PYSEC-2023-74".into(),
            summary: None,
            details: None,
            affected: vec![OsvAffected {
                package: Some(OsvPackage {
                    ecosystem: "PyPI".into(),
                    name: "requests".into(),
                }),
                ranges: Some(vec![
                    OsvRange {
                        r#type: "GIT".into(),
                        events: range(vec![
                            (Some("0"), None),
                            (None, Some("74ea7cf7a6a27a4eeb2ae24e162bcc942a6706d5")),
                        ]),
                    },
                    OsvRange {
                        r#type: "ECOSYSTEM".into(),
                        events: range(vec![(Some("0"), None), (None, Some("2.31.0"))]),
                    },
                ]),
                versions: None,
            }],
            references: vec![],
            published: None,
            modified: None,
            severity: vec![],
            database_specific: None,
        };

        let client = OsvClient::new();
        let result = client.osv_to_vuln(&vuln, "requests");

        assert_eq!(result.fix_version.as_deref(), Some("2.31.0"));
        assert!(result.fix_available);
    }

    #[test]
    fn parses_real_osv_response_shape() {
        let sample = r#"{
            "vulns": [{
                "id": "GHSA-xxxx-xxxx-xxxx",
                "summary": "SQL Injection in Django ORM",
                "affected": [{
                    "package": {"ecosystem": "PyPI", "name": "django"},
                    "ranges": [{
                        "type": "SEMVER",
                        "events": [{"introduced": "2.0.0"}, {"fixed": "3.2.5"}]
                    }]
                }],
                "references": [{"type": "ADVISORY", "url": "https://github.com/advisories/x"}],
                "database_specific": {"severity": "HIGH"}
            }]
        }"#;
        let parsed: OsvQueryResponse = serde_json::from_str(sample).unwrap();
        assert_eq!(parsed.vulns.len(), 1);
        assert_eq!(parsed.vulns[0].id, "GHSA-xxxx-xxxx-xxxx");
    }
}
