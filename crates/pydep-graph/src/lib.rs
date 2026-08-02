//! PyDependencyCheck Graph: Dependency graph construction and analysis
//!
//! Provides:
//! - DAG construction from dependency lists
//! - Cycle detection
//! - Transitive closure computation
//! - Dependency lineage queries
//! - Impact analysis

pub mod dag;
pub mod analysis;
pub mod serialization;
pub mod errors;

pub use dag::DependencyGraph;
pub use analysis::GraphAnalysis;
pub use errors::{GraphError, GraphResult};

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct DependencyNode {
    pub name: String,
    pub version: Option<String>,
    pub is_direct: bool,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_graph_creation() {
        // TODO: Implement test
    }
}
