use pyo3::prelude::*;
use pydep_graph::DependencyGraph as RustDependencyGraph;

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

    fn add_node(&mut self, name: String, version: Option<String>, is_direct: bool) -> PyResult<()> {
        self.inner.add_node(name, version, is_direct)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }

    fn add_edge(&mut self, from: &str, to: &str) -> PyResult<()> {
        self.inner.add_edge(from, to)
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
}

pub fn register_graph(module: &PyModule) -> PyResult<()> {
    module.add_class::<DependencyGraph>()?;
    Ok(())
}
