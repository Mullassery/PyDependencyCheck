use pyo3::prelude::*;

mod parser;
mod graph;
mod security;

#[pymodule]
fn _pydependencycheck(py: Python, m: &PyModule) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;

    let parser_module = PyModule::new(py, "parser")?;
    parser::register_parser(parser_module)?;
    m.add_submodule(parser_module)?;

    let graph_module = PyModule::new(py, "graph")?;
    graph::register_graph(graph_module)?;
    m.add_submodule(graph_module)?;

    let security_module = PyModule::new(py, "security")?;
    security::register_security(security_module)?;
    m.add_submodule(security_module)?;

    Ok(())
}
