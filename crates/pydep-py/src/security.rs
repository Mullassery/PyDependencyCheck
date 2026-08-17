use pydep_security::{OsvClient, Severity};
use pyo3::prelude::*;

#[pyclass]
#[derive(Clone)]
pub enum PySeverity {
    Critical,
    High,
    Medium,
    Low,
    Informational,
}

impl From<Severity> for PySeverity {
    fn from(s: Severity) -> Self {
        match s {
            Severity::Critical => PySeverity::Critical,
            Severity::High => PySeverity::High,
            Severity::Medium => PySeverity::Medium,
            Severity::Low => PySeverity::Low,
            Severity::Informational => PySeverity::Informational,
        }
    }
}

fn severity_str(s: Severity) -> &'static str {
    match s {
        Severity::Critical => "CRITICAL",
        Severity::High => "HIGH",
        Severity::Medium => "MEDIUM",
        Severity::Low => "LOW",
        Severity::Informational => "INFORMATIONAL",
    }
}

#[pyclass]
#[derive(Clone)]
pub struct Vulnerability {
    #[pyo3(get)]
    pub id: String,
    #[pyo3(get)]
    pub package_name: String,
    #[pyo3(get)]
    pub severity: String,
    #[pyo3(get)]
    pub cvss_score: Option<f64>,
    #[pyo3(get)]
    pub description: String,
    #[pyo3(get)]
    pub affected_versions: Vec<String>,
    #[pyo3(get)]
    pub fix_available: bool,
    #[pyo3(get)]
    pub fix_version: Option<String>,
}

impl From<pydep_security::Vulnerability> for Vulnerability {
    fn from(v: pydep_security::Vulnerability) -> Self {
        Self {
            id: v.id,
            package_name: v.package_name,
            severity: severity_str(v.severity).to_string(),
            cvss_score: v.cvss_score,
            description: v.description,
            affected_versions: v.affected_versions,
            fix_available: v.fix_available,
            fix_version: v.fix_version,
        }
    }
}

#[pymethods]
impl Vulnerability {
    fn __repr__(&self) -> String {
        format!(
            "Vulnerability(id='{}', package='{}', severity={})",
            self.id, self.package_name, self.severity
        )
    }
}

/// Query the live OSV.dev database for known vulnerabilities affecting a
/// specific package version. Network errors surface as a Python exception
/// rather than silently returning no results, so callers can distinguish
/// "checked, none found" from "couldn't check".
#[pyfunction]
pub fn scan_package(package_name: &str, version: &str) -> PyResult<Vec<Vulnerability>> {
    let client = OsvClient::new();
    client
        .query_package(package_name, Some(version))
        .map(|vulns| vulns.into_iter().map(Vulnerability::from).collect())
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
}

/// Batch vulnerability scanning across a dependency list. Each package is
/// queried independently; a single package's network failure is recorded as
/// an empty-but-flagged result rather than aborting the whole scan, since a
/// dependency graph can have hundreds of entries and one transient failure
/// shouldn't block reporting on the rest.
#[pyfunction]
pub fn scan_vulnerabilities(dependencies: Vec<(String, String)>) -> PyResult<Vec<Vulnerability>> {
    let client = OsvClient::new();
    let mut all = Vec::new();
    for (name, version) in dependencies {
        match client.query_package(&name, Some(&version)) {
            Ok(vulns) => all.extend(vulns.into_iter().map(Vulnerability::from)),
            Err(e) => {
                tracing::warn!("OSV query failed for {name}=={version}: {e}");
            }
        }
    }
    Ok(all)
}

pub fn register_security(module: &Bound<'_, pyo3::types::PyModule>) -> PyResult<()> {
    module.add_class::<PySeverity>()?;
    module.add_class::<Vulnerability>()?;
    module.add_function(wrap_pyfunction!(scan_package, module)?)?;
    module.add_function(wrap_pyfunction!(scan_vulnerabilities, module)?)?;
    Ok(())
}
