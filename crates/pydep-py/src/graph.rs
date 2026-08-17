use pydep_graph::DependencyGraph as RustDependencyGraph;
use pyo3::prelude::*;

#[pyclass]
pub struct DependencyGraph {
    inner: RustDependencyGraph,
}

#[pymethods]
impl DependencyGraph {
    #[new]
    fn new() -> Self {
        Self {
            inner: RustDependencyGraph::new(),
        }
    }

    #[pyo3(signature = (name, version=None, is_direct=false))]
    fn add_node(&mut self, name: String, version: Option<String>, is_direct: bool) -> PyResult<()> {
        self.inner
            .add_node(name, version, is_direct)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }

    fn add_edge(&mut self, from: &str, to: &str) -> PyResult<()> {
        self.inner
            .add_edge(from, to)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }

    fn has_cycles(&self) -> bool {
        self.inner.has_cycles()
    }

    fn node_count(&self) -> usize {
        self.inner.node_count()
    }

    fn edge_count(&self) -> usize {
        self.inner.edge_count()
    }

    fn find_cycles(&self) -> PyResult<Vec<Vec<String>>> {
        self.inner
            .find_cycles()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }

    fn get_all_dependencies(&self, package: &str) -> PyResult<Vec<String>> {
        self.inner
            .get_all_dependencies(package)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }

    fn nodes(&self) -> Vec<(String, Option<String>, bool)> {
        self.inner
            .nodes()
            .into_iter()
            .map(|n| (n.name.clone(), n.version.clone(), n.is_direct))
            .collect()
    }

    fn edges(&self) -> Vec<(String, String)> {
        self.inner.edges()
    }
}

pub fn register_graph(module: &Bound<'_, pyo3::types::PyModule>) -> PyResult<()> {
    module.add_class::<DependencyGraph>()?;
    Ok(())
}
