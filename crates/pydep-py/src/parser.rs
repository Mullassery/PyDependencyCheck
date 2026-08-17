use pydep_parser::{parse_file as rs_parse_file, Dependency as RsDependency};
use pyo3::prelude::*;

#[pyclass]
pub struct Dependency {
    #[pyo3(get, set)]
    pub name: String,
    #[pyo3(get, set)]
    pub version: Option<String>,
    #[pyo3(get, set)]
    pub dev: bool,
    #[pyo3(get, set)]
    pub direct: bool,
    #[pyo3(get, set)]
    pub url: Option<String>,
}

#[pymethods]
impl Dependency {
    #[new]
    fn new(name: String, version: Option<String>) -> Self {
        Self {
            name,
            version,
            dev: false,
            direct: true,
            url: None,
        }
    }

    fn __repr__(&self) -> String {
        match &self.version {
            Some(v) => format!("{}=={}", self.name, v),
            None => self.name.clone(),
        }
    }
}

fn convert_dependency(dep: RsDependency) -> Dependency {
    Dependency {
        name: dep.name,
        version: dep.version_constraint.map(|v| v.raw),
        dev: dep.dev,
        direct: dep.direct,
        url: dep.url,
    }
}

#[pyfunction]
pub fn parse_file(path: &str) -> PyResult<Vec<Dependency>> {
    rs_parse_file(path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
        .map(|deps| deps.into_iter().map(convert_dependency).collect())
}

#[pyfunction]
pub fn parse_requirements_file(path: &str) -> PyResult<Vec<Dependency>> {
    parse_file(path)
}

#[pyfunction]
pub fn parse_pyproject_toml(path: &str) -> PyResult<Vec<Dependency>> {
    parse_file(path)
}

pub fn register_parser(module: &Bound<'_, pyo3::types::PyModule>) -> PyResult<()> {
    module.add_class::<Dependency>()?;
    module.add_function(wrap_pyfunction!(parse_file, module)?)?;
    module.add_function(wrap_pyfunction!(parse_requirements_file, module)?)?;
    module.add_function(wrap_pyfunction!(parse_pyproject_toml, module)?)?;
    Ok(())
}
