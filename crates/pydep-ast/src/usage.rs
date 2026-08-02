use crate::{ImportInfo, AstResult};
use std::collections::{HashMap, HashSet};
use super::imports::extract_package_name;

/// Track which packages are actually used in the codebase
#[derive(Debug)]
pub struct UsageAnalysis {
    /// Map of package name to usage count
    pub usage_count: HashMap<String, usize>,
    /// Map of package name to files where it's imported
    pub import_locations: HashMap<String, Vec<(String, usize)>>, // (file, line)
    /// All imported packages
    pub imported_packages: HashSet<String>,
}

impl UsageAnalysis {
    pub fn new() -> Self {
        Self {
            usage_count: HashMap::new(),
            import_locations: HashMap::new(),
            imported_packages: HashSet::new(),
        }
    }

    /// Analyze imports to track usage
    pub fn from_imports(imports: Vec<ImportInfo>) -> Self {
        let mut analysis = Self::new();

        for import in imports {
            let package = extract_package_name(&import.module);

            // Count usage
            *analysis.usage_count.entry(package.clone()).or_insert(0) += 1;

            // Track location
            analysis
                .import_locations
                .entry(package.clone())
                .or_insert_with(Vec::new)
                .push((import.file.clone(), import.line));

            analysis.imported_packages.insert(package);
        }

        analysis
    }

    /// Check if a package is used
    pub fn is_used(&self, package: &str) -> bool {
        self.imported_packages.contains(&package.to_lowercase().replace("_", "-"))
    }

    /// Get usage count for a package
    pub fn get_usage_count(&self, package: &str) -> usize {
        let normalized = package.to_lowercase().replace("_", "-");
        *self.usage_count.get(&normalized).unwrap_or(&0)
    }

    /// Get all locations where a package is imported
    pub fn get_import_locations(&self, package: &str) -> Vec<(String, usize)> {
        let normalized = package.to_lowercase().replace("_", "-");
        self.import_locations
            .get(&normalized)
            .cloned()
            .unwrap_or_default()
    }

    /// Find packages that are imported but not in the dependency list
    pub fn find_missing_imports(&self, declared_packages: &[&str]) -> Vec<String> {
        let declared_set: HashSet<String> = declared_packages
            .iter()
            .map(|p| p.to_lowercase().replace("_", "-"))
            .collect();

        self.imported_packages
            .iter()
            .filter(|pkg| !declared_set.contains(pkg.as_str()))
            .filter(|pkg| !Self::is_stdlib(pkg))
            .cloned()
            .collect()
    }

    /// Find candidates for unused/dead dependencies
    /// Returns packages that:
    /// 1. Are declared but not imported (high confidence)
    /// 2. Are barely used (low confidence)
    pub fn find_potential_dead_deps(&self, declared_packages: &[&str]) -> Vec<(String, Confidence)> {
        let mut dead_deps = Vec::new();

        for package in declared_packages {
            let normalized = package.to_lowercase().replace("_", "-");

            if !self.is_used(&normalized) {
                // Never imported: HIGH confidence it's dead
                dead_deps.push((normalized, Confidence::High));
            } else {
                // Used, but check usage frequency
                let count = self.get_usage_count(&normalized);
                if count == 1 {
                    // Used only once: MEDIUM confidence
                    dead_deps.push((normalized, Confidence::Medium));
                }
                // More than 1 usage: probably not dead
            }
        }

        // Filter out common dev tools that might have low usage
        dead_deps.retain(|(pkg, _)| !Self::is_dev_tool(pkg));

        dead_deps
    }

    /// Check if a package is part of Python stdlib
    fn is_stdlib(package: &str) -> bool {
        matches!(
            package.to_lowercase().as_str(),
            "os" | "sys" | "json" | "re" | "math" | "datetime" | "time" | "collections" |
            "itertools" | "functools" | "pathlib" | "tempfile" | "shutil" | "subprocess" |
            "threading" | "multiprocessing" | "asyncio" | "urllib" | "http" | "email" |
            "socket" | "ssl" | "base64" | "hashlib" | "hmac" | "secrets" | "io" | "csv" |
            "xml" | "html" | "urllib3" | "typing" | "dataclasses" | "abc" | "enum" |
            "warnings" | "logging" | "unittest" | "doctest" | "pdb" | "traceback"
        )
    }

    /// Check if a package is a common dev/test tool
    fn is_dev_tool(package: &str) -> bool {
        matches!(
            package.to_lowercase().as_str(),
            "pytest" | "pytest-cov" | "black" | "ruff" | "mypy" | "flake8" | "isort" |
            "sphinx" | "tox" | "coverage" | "mock" | "faker" | "factory-boy" | "hypothesis"
        )
    }
}

#[derive(Debug, Clone, Copy, serde::Serialize, serde::Deserialize, PartialEq, Eq)]
pub enum Confidence {
    High,
    Medium,
    Low,
}

impl Default for UsageAnalysis {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ImportInfo;

    #[test]
    fn test_usage_analysis() {
        let imports = vec![
            ImportInfo {
                module: "requests".to_string(),
                file: "app.py".to_string(),
                line: 1,
                import_type: crate::ImportType::Direct,
            },
            ImportInfo {
                module: "requests.auth".to_string(),
                file: "auth.py".to_string(),
                line: 5,
                import_type: crate::ImportType::From,
            },
        ];

        let analysis = UsageAnalysis::from_imports(imports);
        assert_eq!(analysis.get_usage_count("requests"), 2);
        assert!(analysis.is_used("requests"));
    }

    #[test]
    fn test_find_missing_imports() {
        let imports = vec![
            ImportInfo {
                module: "requests".to_string(),
                file: "app.py".to_string(),
                line: 1,
                import_type: crate::ImportType::Direct,
            },
            ImportInfo {
                module: "unknown_package".to_string(),
                file: "app.py".to_string(),
                line: 2,
                import_type: crate::ImportType::Direct,
            },
        ];

        let analysis = UsageAnalysis::from_imports(imports);
        assert_eq!(analysis.imported_packages.len(), 2);

        let missing = analysis.find_missing_imports(&["requests", "flask"]);
        // Should find unknown_package as missing (not declared)
        assert!(missing.len() > 0, "Should find at least one missing package");
    }

    #[test]
    fn test_find_dead_deps() {
        let analysis = UsageAnalysis::new();
        let dead = analysis.find_potential_dead_deps(&["requests", "flask", "django"]);
        assert_eq!(dead.len(), 3);
        for (_, conf) in &dead {
            assert_eq!(*conf, Confidence::High);
        }
    }
}
