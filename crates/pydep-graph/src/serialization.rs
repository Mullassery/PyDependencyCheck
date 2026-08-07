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

        let edges = self
            .edges()
            .into_iter()
            .map(|(from, to)| EdgeJson { from, to })
            .collect();

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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn to_json_includes_edges() {
        let mut graph = DependencyGraph::new();
        graph.add_node("app".to_string(), Some("1.0.0".to_string()), true).unwrap();
        graph.add_node("requests".to_string(), Some("2.31.0".to_string()), false).unwrap();
        graph.add_edge("app", "requests").unwrap();

        let value = graph.to_json_value().unwrap();
        let edges = value["edges"].as_array().unwrap();
        assert_eq!(edges.len(), 1);
        assert_eq!(edges[0]["from"], "app");
        assert_eq!(edges[0]["to"], "requests");

        let nodes = value["nodes"].as_array().unwrap();
        assert_eq!(nodes.len(), 2);
    }

    #[test]
    fn to_json_with_no_edges_is_empty_array_not_missing() {
        let mut graph = DependencyGraph::new();
        graph.add_node("standalone".to_string(), None, true).unwrap();

        let value = graph.to_json_value().unwrap();
        assert_eq!(value["edges"].as_array().unwrap().len(), 0);
    }
}
