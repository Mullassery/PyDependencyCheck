use crate::{DependencyGraph, GraphResult};
use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct GraphJson {
    pub nodes: Vec<NodeJson>,
    pub edges: Vec<EdgeJson>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct NodeJson {
    pub name: String,
    pub version: Option<String>,
    pub is_direct: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EdgeJson {
    pub from: String,
    pub to: String,
}

impl DependencyGraph {
    /// Serialize graph to JSON
    pub fn to_json(&self) -> GraphResult<String> {
        let nodes = self.nodes()
            .iter()
            .map(|n| NodeJson {
                name: n.name.clone(),
                version: n.version.clone(),
                is_direct: n.is_direct,
            })
            .collect();

        let edges = Vec::new(); // TODO: Extract edges from graph

        let json = GraphJson { nodes, edges };
        serde_json::to_string_pretty(&json)
            .map_err(|e| crate::GraphError::SerializationError(e.to_string()))
    }

    /// Serialize graph to JSON value
    pub fn to_json_value(&self) -> GraphResult<serde_json::Value> {
        let json_str = self.to_json()?;
        serde_json::from_str(&json_str)
            .map_err(|e| crate::GraphError::SerializationError(e.to_string()))
    }
}
