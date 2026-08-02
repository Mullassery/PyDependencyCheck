use petgraph::graph::{DiGraph, NodeIndex};
use petgraph::algo;
use std::collections::HashMap;
use crate::{DependencyNode, GraphError, GraphResult};

/// Dependency graph using petgraph DiGraph
pub struct DependencyGraph {
    graph: DiGraph<DependencyNode, ()>,
    nodes: HashMap<String, NodeIndex>,
}

impl DependencyGraph {
    /// Create a new empty dependency graph
    pub fn new() -> Self {
        Self {
            graph: DiGraph::new(),
            nodes: HashMap::new(),
        }
    }

    /// Add a dependency node to the graph
    pub fn add_node(&mut self, name: String, version: Option<String>, is_direct: bool) -> GraphResult<()> {
        if !self.nodes.contains_key(&name) {
            let node = DependencyNode { name: name.clone(), version, is_direct };
            let idx = self.graph.add_node(node);
            self.nodes.insert(name, idx);
        }
        Ok(())
    }

    /// Add an edge from one dependency to another
    pub fn add_edge(&mut self, from: &str, to: &str) -> GraphResult<()> {
        let from_idx = self.nodes.get(from)
            .copied()
            .ok_or_else(|| GraphError::NodeNotFound(from.to_string()))?;
        let to_idx = self.nodes.get(to)
            .copied()
            .ok_or_else(|| GraphError::NodeNotFound(to.to_string()))?;

        self.graph.add_edge(from_idx, to_idx, ());
        Ok(())
    }

    /// Check for cycles in the graph
    pub fn has_cycles(&self) -> bool {
        algo::is_cyclic_directed(&self.graph)
    }

    /// Get all dependencies (direct + transitive) for a package
    pub fn get_all_dependencies(&self, package: &str) -> GraphResult<Vec<String>> {
        let start_idx = self.nodes.get(package)
            .copied()
            .ok_or_else(|| GraphError::NodeNotFound(package.to_string()))?;

        let mut result = Vec::new();
        let mut stack = vec![start_idx];
        let mut visited = std::collections::HashSet::new();

        while let Some(idx) = stack.pop() {
            if visited.insert(idx) {
                for neighbor in self.graph.neighbors(idx) {
                    if let Some(node) = self.graph.node_weight(neighbor) {
                        result.push(node.name.clone());
                    }
                    stack.push(neighbor);
                }
            }
        }

        Ok(result)
    }

    /// Get the dependency path from one package to another
    pub fn get_path(&self, from: &str, to: &str) -> GraphResult<Option<Vec<String>>> {
        let from_idx = self.nodes.get(from)
            .copied()
            .ok_or_else(|| GraphError::NodeNotFound(from.to_string()))?;
        let to_idx = self.nodes.get(to)
            .copied()
            .ok_or_else(|| GraphError::NodeNotFound(to.to_string()))?;

        match algo::astar(&self.graph, from_idx, |n| n == to_idx, |_| 1, |_| 0) {
            Some((_cost, path)) => {
                let path_names = path
                    .iter()
                    .filter_map(|&idx| self.graph.node_weight(idx).map(|n| n.name.clone()))
                    .collect();
                Ok(Some(path_names))
            }
            None => Ok(None),
        }
    }

    /// Get reverse dependencies (packages that depend on this one)
    pub fn get_reverse_dependencies(&self, package: &str) -> GraphResult<Vec<String>> {
        let target_idx = self.nodes.get(package)
            .copied()
            .ok_or_else(|| GraphError::NodeNotFound(package.to_string()))?;

        let mut result = Vec::new();
        for idx in self.graph.node_indices() {
            if algo::has_path_connecting(&self.graph, idx, target_idx, None) && idx != target_idx {
                if let Some(node) = self.graph.node_weight(idx) {
                    result.push(node.name.clone());
                }
            }
        }

        Ok(result)
    }

    /// Get number of nodes
    pub fn node_count(&self) -> usize {
        self.graph.node_count()
    }

    /// Get number of edges
    pub fn edge_count(&self) -> usize {
        self.graph.edge_count()
    }

    /// Get all nodes
    pub fn nodes(&self) -> Vec<&DependencyNode> {
        self.graph.node_weights().collect()
    }
}

impl Default for DependencyGraph {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_graph_creation() {
        let mut graph = DependencyGraph::new();
        graph.add_node("requests".to_string(), Some("2.32.0".to_string()), true).unwrap();
        assert_eq!(graph.node_count(), 1);
    }

    #[test]
    fn test_add_edge() {
        let mut graph = DependencyGraph::new();
        graph.add_node("app".to_string(), None, true).unwrap();
        graph.add_node("requests".to_string(), Some("2.32.0".to_string()), false).unwrap();
        graph.add_edge("app", "requests").unwrap();
        assert_eq!(graph.edge_count(), 1);
    }
}
