//! PyDependencyCheck Graph: Dependency graph construction and analysis
//!
//! Provides:
//! - DAG construction from dependency lists
//! - Cycle detection
//! - Transitive closure computation
//! - Dependency lineage queries
//! - Impact analysis

pub mod analysis;
pub mod dag;
pub mod errors;
pub mod serialization;

pub use analysis::GraphAnalysis;
pub use dag::DependencyGraph;
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
        let mut graph = DependencyGraph::new();
        graph.add_node("app".to_string(), None, true).unwrap();
        graph
            .add_node("requests".to_string(), Some("2.32.0".to_string()), false)
            .unwrap();
        graph.add_edge("app", "requests").unwrap();

        assert_eq!(graph.node_count(), 2);
        assert_eq!(graph.edge_count(), 1);
        assert!(!graph.has_cycles());
    }
}
