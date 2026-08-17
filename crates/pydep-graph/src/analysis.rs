use crate::{DependencyGraph, GraphResult};
use std::collections::{HashMap, HashSet, VecDeque};

/// Graph analysis operations
pub struct GraphAnalysis;

impl GraphAnalysis {
    /// Perform topological sort (Kahn's algorithm)
    /// Returns packages in order safe for upgrades
    pub fn topological_sort(graph: &DependencyGraph) -> GraphResult<Vec<String>> {
        let mut in_degree: HashMap<String, usize> = HashMap::new();
        let mut adj_list: HashMap<String, Vec<String>> = HashMap::new();

        // Build adjacency list and in-degree map
        for node in graph.nodes() {
            in_degree.entry(node.name.clone()).or_insert(0);
            adj_list.entry(node.name.clone()).or_default();
        }

        for (from, to) in graph.edges() {
            *in_degree.entry(to.clone()).or_insert(0) += 1;
            adj_list.entry(from).or_default().push(to);
        }

        // Find all nodes with in-degree 0
        let mut queue: VecDeque<String> = in_degree
            .iter()
            .filter(|(_, degree)| **degree == 0)
            .map(|(name, _)| name.clone())
            .collect();

        let mut sorted = Vec::new();

        while let Some(node) = queue.pop_front() {
            sorted.push(node.clone());

            if let Some(neighbors) = adj_list.get(&node) {
                for neighbor in neighbors {
                    if let Some(degree) = in_degree.get_mut(neighbor) {
                        *degree -= 1;
                        if *degree == 0 {
                            queue.push_back(neighbor.clone());
                        }
                    }
                }
            }
        }

        Ok(sorted)
    }

    /// Compute transitive closure
    /// Returns all (a, b) pairs where there's a path from a to b
    pub fn transitive_closure(graph: &DependencyGraph) -> GraphResult<Vec<(String, String)>> {
        let mut closure = Vec::new();

        for from_node in graph.nodes() {
            let deps = graph.get_all_dependencies(&from_node.name)?;
            for dep in deps {
                closure.push((from_node.name.clone(), dep));
            }
        }

        Ok(closure)
    }

    /// Find cycles in the graph
    pub fn find_cycles(graph: &DependencyGraph) -> GraphResult<Vec<Vec<String>>> {
        graph.find_cycles()
    }

    /// Compute average dependency depth
    pub fn average_depth(graph: &DependencyGraph) -> GraphResult<f64> {
        if graph.node_count() == 0 {
            return Ok(0.0);
        }

        let mut total_depth = 0usize;
        let direct_deps: HashSet<String> = graph
            .nodes()
            .iter()
            .filter(|n| n.is_direct)
            .map(|n| n.name.clone())
            .collect();

        for package in direct_deps {
            let depth = graph.compute_depth(&package)?;
            total_depth += depth;
        }

        Ok(total_depth as f64 / graph.direct_dep_count().max(1) as f64)
    }

    /// Find packages with no dependents (leaf nodes)
    pub fn find_leaf_packages(graph: &DependencyGraph) -> Vec<String> {
        graph
            .nodes()
            .iter()
            .filter(|n| {
                // Check if this node has any incoming edges
                !graph.edges().iter().any(|(_, to)| to == &n.name)
            })
            .map(|n| n.name.clone())
            .collect()
    }

    /// Find packages that are depended on by many others
    pub fn find_critical_packages(graph: &DependencyGraph) -> Vec<(String, usize)> {
        let mut dependents_count: HashMap<String, usize> = HashMap::new();

        for (_, to) in graph.edges() {
            *dependents_count.entry(to).or_insert(0) += 1;
        }

        let mut critical: Vec<_> = dependents_count.into_iter().collect();
        critical.sort_by_key(|b| std::cmp::Reverse(b.1));
        critical
    }

    /// Compute impact of removing a package
    /// Returns count of directly affected packages
    pub fn impact_of_removal(graph: &DependencyGraph, package: &str) -> GraphResult<usize> {
        let direct_deps = graph.get_direct_dependencies(package)?;
        Ok(direct_deps.len())
    }

    /// Find packages that are transitively required by a package
    pub fn transitive_dependencies(
        graph: &DependencyGraph,
        package: &str,
    ) -> GraphResult<Vec<String>> {
        graph.get_all_dependencies(package)
    }

    /// Check for "diamond dependency" patterns (A->B, A->C, B->D, C->D)
    pub fn find_diamond_patterns(
        graph: &DependencyGraph,
    ) -> GraphResult<Vec<(String, String, String)>> {
        let mut diamonds = Vec::new();

        for start_node in graph.nodes() {
            let direct_deps = graph.get_direct_dependencies(&start_node.name)?;

            if direct_deps.len() >= 2 {
                // Check if any two direct deps share common dependencies
                for i in 0..direct_deps.len() {
                    for j in (i + 1)..direct_deps.len() {
                        let deps_i = graph.get_all_dependencies(&direct_deps[i])?;
                        let deps_j = graph.get_all_dependencies(&direct_deps[j])?;

                        // Find common deps
                        let deps_i_set: HashSet<_> = deps_i.into_iter().collect();
                        for common_dep in deps_j {
                            if deps_i_set.contains(&common_dep) {
                                diamonds.push((
                                    start_node.name.clone(),
                                    direct_deps[i].clone(),
                                    direct_deps[j].clone(),
                                ));
                            }
                        }
                    }
                }
            }
        }

        Ok(diamonds)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::DependencyGraph;

    #[test]
    fn test_topological_sort() {
        let mut graph = DependencyGraph::new();
        graph.add_node("a".to_string(), None, true).unwrap();
        graph.add_node("b".to_string(), None, false).unwrap();
        graph.add_node("c".to_string(), None, false).unwrap();

        graph.add_edge("a", "b").unwrap();
        graph.add_edge("b", "c").unwrap();

        let sorted = GraphAnalysis::topological_sort(&graph).unwrap();
        assert!(!sorted.is_empty());
        // 'a' should come before 'b' before 'c'
        let a_pos = sorted.iter().position(|x| x == "a").unwrap();
        let b_pos = sorted.iter().position(|x| x == "b").unwrap();
        let c_pos = sorted.iter().position(|x| x == "c").unwrap();
        assert!(a_pos < b_pos && b_pos < c_pos);
    }

    #[test]
    fn test_transitive_closure() {
        let mut graph = DependencyGraph::new();
        graph.add_node("app".to_string(), None, true).unwrap();
        graph.add_node("lib1".to_string(), None, false).unwrap();
        graph.add_node("lib2".to_string(), None, false).unwrap();

        graph.add_edge("app", "lib1").unwrap();
        graph.add_edge("lib1", "lib2").unwrap();

        let closure = GraphAnalysis::transitive_closure(&graph).unwrap();
        assert!(closure.contains(&("app".to_string(), "lib1".to_string())));
        assert!(closure.contains(&("app".to_string(), "lib2".to_string())));
    }
}
