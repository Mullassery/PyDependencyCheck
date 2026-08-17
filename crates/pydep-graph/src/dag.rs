use crate::{DependencyNode, GraphError, GraphResult};
use petgraph::algo;
use petgraph::graph::{DiGraph, NodeIndex};
use std::collections::{HashMap, HashSet, VecDeque};

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
    pub fn add_node(
        &mut self,
        name: String,
        version: Option<String>,
        is_direct: bool,
    ) -> GraphResult<()> {
        if !self.nodes.contains_key(&name) {
            let node = DependencyNode {
                name: name.clone(),
                version,
                is_direct,
            };
            let idx = self.graph.add_node(node);
            self.nodes.insert(name, idx);
        }
        Ok(())
    }

    /// Add an edge from one dependency to another
    pub fn add_edge(&mut self, from: &str, to: &str) -> GraphResult<()> {
        let from_idx = self
            .nodes
            .get(from)
            .copied()
            .ok_or_else(|| GraphError::NodeNotFound(from.to_string()))?;
        let to_idx = self
            .nodes
            .get(to)
            .copied()
            .ok_or_else(|| GraphError::NodeNotFound(to.to_string()))?;

        self.graph.add_edge(from_idx, to_idx, ());
        Ok(())
    }

    /// Check for cycles in the graph
    pub fn has_cycles(&self) -> bool {
        algo::is_cyclic_directed(&self.graph)
    }

    /// Detect all cycles in the graph
    pub fn find_cycles(&self) -> GraphResult<Vec<Vec<String>>> {
        let mut cycles = Vec::new();
        let mut visited = HashSet::new();
        let mut rec_stack = HashSet::new();

        for start_idx in self.graph.node_indices() {
            if !visited.contains(&start_idx) {
                self.dfs_cycle_detection(start_idx, &mut visited, &mut rec_stack, &mut cycles)?;
            }
        }

        Ok(cycles)
    }

    fn dfs_cycle_detection(
        &self,
        node_idx: NodeIndex,
        visited: &mut HashSet<NodeIndex>,
        rec_stack: &mut HashSet<NodeIndex>,
        cycles: &mut Vec<Vec<String>>,
    ) -> GraphResult<()> {
        visited.insert(node_idx);
        rec_stack.insert(node_idx);

        for neighbor in self.graph.neighbors(node_idx) {
            if !visited.contains(&neighbor) {
                self.dfs_cycle_detection(neighbor, visited, rec_stack, cycles)?;
            } else if rec_stack.contains(&neighbor) {
                // Found a cycle
                if let (Some(start_node), Some(end_node)) = (
                    self.graph.node_weight(node_idx),
                    self.graph.node_weight(neighbor),
                ) {
                    cycles.push(vec![start_node.name.clone(), end_node.name.clone()]);
                }
            }
        }

        rec_stack.remove(&node_idx);
        Ok(())
    }

    /// Get all dependencies (direct + transitive) for a package
    pub fn get_all_dependencies(&self, package: &str) -> GraphResult<Vec<String>> {
        let start_idx = self
            .nodes
            .get(package)
            .copied()
            .ok_or_else(|| GraphError::NodeNotFound(package.to_string()))?;

        let mut result = Vec::new();
        let mut queue = VecDeque::new();
        let mut visited = HashSet::new();

        queue.push_back(start_idx);
        visited.insert(start_idx);

        while let Some(idx) = queue.pop_front() {
            for neighbor in self.graph.neighbors(idx) {
                if !visited.contains(&neighbor) {
                    visited.insert(neighbor);
                    if let Some(node) = self.graph.node_weight(neighbor) {
                        result.push(node.name.clone());
                    }
                    queue.push_back(neighbor);
                }
            }
        }

        Ok(result)
    }

    /// Get immediate dependencies (one level only)
    pub fn get_direct_dependencies(&self, package: &str) -> GraphResult<Vec<String>> {
        let start_idx = self
            .nodes
            .get(package)
            .copied()
            .ok_or_else(|| GraphError::NodeNotFound(package.to_string()))?;

        let mut result = Vec::new();
        for neighbor in self.graph.neighbors(start_idx) {
            if let Some(node) = self.graph.node_weight(neighbor) {
                result.push(node.name.clone());
            }
        }

        Ok(result)
    }

    /// Get the dependency path from one package to another
    pub fn get_path(&self, from: &str, to: &str) -> GraphResult<Option<Vec<String>>> {
        let from_idx = self
            .nodes
            .get(from)
            .copied()
            .ok_or_else(|| GraphError::NodeNotFound(from.to_string()))?;
        let to_idx = self
            .nodes
            .get(to)
            .copied()
            .ok_or_else(|| GraphError::NodeNotFound(to.to_string()))?;

        // BFS to find shortest path
        let mut queue = VecDeque::new();
        let mut parent_map: HashMap<NodeIndex, NodeIndex> = HashMap::new();
        let mut visited = HashSet::new();

        queue.push_back(from_idx);
        visited.insert(from_idx);

        while let Some(current) = queue.pop_front() {
            if current == to_idx {
                // Reconstruct path
                let mut path = vec![to_idx];
                let mut current = to_idx;
                while let Some(&parent) = parent_map.get(&current) {
                    path.push(parent);
                    current = parent;
                }
                path.reverse();

                let path_names = path
                    .iter()
                    .filter_map(|&idx| self.graph.node_weight(idx).map(|n| n.name.clone()))
                    .collect();
                return Ok(Some(path_names));
            }

            for neighbor in self.graph.neighbors(current) {
                if !visited.contains(&neighbor) {
                    visited.insert(neighbor);
                    parent_map.insert(neighbor, current);
                    queue.push_back(neighbor);
                }
            }
        }

        Ok(None)
    }

    /// Get reverse dependencies (packages that depend on this one)
    pub fn get_reverse_dependencies(&self, package: &str) -> GraphResult<Vec<String>> {
        let target_idx = self
            .nodes
            .get(package)
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

    /// Compute dependency depth (longest path from root to leaf)
    pub fn compute_depth(&self, package: &str) -> GraphResult<usize> {
        let start_idx = self
            .nodes
            .get(package)
            .copied()
            .ok_or_else(|| GraphError::NodeNotFound(package.to_string()))?;

        self.compute_depth_recursive(start_idx, &mut HashSet::new())
    }

    fn compute_depth_recursive(
        &self,
        node_idx: NodeIndex,
        visited: &mut HashSet<NodeIndex>,
    ) -> GraphResult<usize> {
        if visited.contains(&node_idx) {
            return Ok(0); // Cycle detected, return 0
        }

        visited.insert(node_idx);

        let mut max_depth = 0;
        for neighbor in self.graph.neighbors(node_idx) {
            let depth = self.compute_depth_recursive(neighbor, visited)?;
            max_depth = max_depth.max(depth + 1);
        }

        visited.remove(&node_idx);
        Ok(max_depth)
    }

    /// Get number of nodes
    pub fn node_count(&self) -> usize {
        self.graph.node_count()
    }

    /// Get number of direct dependencies
    pub fn direct_dep_count(&self) -> usize {
        self.graph.node_weights().filter(|n| n.is_direct).count()
    }

    /// Get number of transitive dependencies
    pub fn transitive_dep_count(&self) -> usize {
        self.node_count() - self.direct_dep_count()
    }

    /// Get number of edges
    pub fn edge_count(&self) -> usize {
        self.graph.edge_count()
    }

    /// Get all nodes
    pub fn nodes(&self) -> Vec<&DependencyNode> {
        self.graph.node_weights().collect()
    }

    /// Get nodes as owned data (for serialization)
    pub fn nodes_owned(&self) -> Vec<DependencyNode> {
        self.graph.node_weights().cloned().collect()
    }

    /// Get all edges as (from, to) pairs
    pub fn edges(&self) -> Vec<(String, String)> {
        self.graph
            .edge_indices()
            .filter_map(|edge_idx| {
                let (from_idx, to_idx) = self.graph.edge_endpoints(edge_idx)?;
                let from = self.graph.node_weight(from_idx)?.name.clone();
                let to = self.graph.node_weight(to_idx)?.name.clone();
                Some((from, to))
            })
            .collect()
    }

    /// Check if a path exists from one package to another
    pub fn has_path(&self, from: &str, to: &str) -> GraphResult<bool> {
        let from_idx = self
            .nodes
            .get(from)
            .copied()
            .ok_or_else(|| GraphError::NodeNotFound(from.to_string()))?;
        let to_idx = self
            .nodes
            .get(to)
            .copied()
            .ok_or_else(|| GraphError::NodeNotFound(to.to_string()))?;

        Ok(algo::has_path_connecting(
            &self.graph,
            from_idx,
            to_idx,
            None,
        ))
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
        graph
            .add_node("requests".to_string(), Some("2.32.0".to_string()), true)
            .unwrap();
        assert_eq!(graph.node_count(), 1);
    }

    #[test]
    fn test_add_edge() {
        let mut graph = DependencyGraph::new();
        graph.add_node("app".to_string(), None, true).unwrap();
        graph
            .add_node("requests".to_string(), Some("2.32.0".to_string()), false)
            .unwrap();
        graph.add_edge("app", "requests").unwrap();
        assert_eq!(graph.edge_count(), 1);
    }
}
