use pyo3::prelude::*;

#[pyclass]
pub struct Dependency {
    #[pyo3(get, set)]
    pub name: String,
    #[pyo3(get, set)]
    pub version: Option<String>,
}

#[pymethods]
impl Dependency {
    #[new]
    fn new(name: String, version: Option<String>) -> Self {
        Self { name, version }
    }

    fn __repr__(&self) -> String {
        match &self.version {
            Some(v) => format!("{}=={}", self.name, v),
            None => self.name.clone(),
        }
    }
}

pub fn register_parser(module: &PyModule) -> PyResult<()> {
    module.add_class::<Dependency>()?;
    Ok(())
}
