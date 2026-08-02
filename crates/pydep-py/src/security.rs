use pyo3::prelude::*;
use pydep_security::Severity;

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

#[pyclass]
pub struct Vulnerability {
    #[pyo3(get, set)]
    pub id: String,
    #[pyo3(get, set)]
    pub package_name: String,
    #[pyo3(get, set)]
    pub severity: String,
    #[pyo3(get, set)]
    pub cvss_score: Option<f64>,
}

#[pymethods]
impl Vulnerability {
    #[new]
    fn new(id: String, package_name: String, severity: String, cvss_score: Option<f64>) -> Self {
        Self {
            id,
            package_name,
            severity,
            cvss_score,
        }
    }
}

pub fn register_security(module: &PyModule) -> PyResult<()> {
    module.add_class::<PySeverity>()?;
    module.add_class::<Vulnerability>()?;
    Ok(())
}
