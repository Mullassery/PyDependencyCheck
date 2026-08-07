use crate::usage::{Confidence, UsageAnalysis};
use crate::{AstResult, ImportInfo, ImportType};

/// Detect dead/unused dependencies by cross-referencing declared packages
/// against what's actually imported in the codebase. Delegates to
/// `UsageAnalysis`, which already implements the real heuristics (never
/// imported = high confidence, imported exactly once = medium confidence,
/// with stdlib and common dev-tool false positives filtered out).
pub struct DeadCodeDetector;

/// One package flagged as a possible dead dependency, with the confidence
/// heuristic that produced it.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct DeadPackage {
    pub name: String,
    pub confidence: DeadCodeConfidence,
}

impl DeadCodeDetector {
    /// Find packages that are declared/installed but never imported anywhere
    /// (high-confidence only — see `find_dead_packages_with_confidence` for
    /// the full picture, which also surfaces single-use packages as lower-
    /// confidence candidates worth a manual look, not definite removals).
    /// `imports` are module names as they appear in import statements
    /// (e.g. "yaml", not the PyPI package name "PyYAML" — callers should
    /// pass whatever `extract_package_name` would normalize to, or raw
    /// module names, since matching here is case/hyphen/underscore-insensitive).
    pub fn find_dead_packages(imports: Vec<String>, installed: Vec<String>) -> AstResult<Vec<String>> {
        Ok(Self::find_dead_packages_with_confidence(imports, installed)?
            .into_iter()
            .filter(|d| d.confidence == DeadCodeConfidence::High)
            .map(|d| d.name)
            .collect())
    }

    /// Same as `find_dead_packages`, but returns every candidate (including
    /// lower-confidence ones like single-use packages) tagged with the
    /// confidence level that produced it, instead of silently dropping them.
    pub fn find_dead_packages_with_confidence(
        imports: Vec<String>,
        installed: Vec<String>,
    ) -> AstResult<Vec<DeadPackage>> {
        let import_infos: Vec<ImportInfo> = imports
            .into_iter()
            .map(|module| ImportInfo { module, file: String::new(), line: 0, import_type: ImportType::Direct })
            .collect();

        let analysis = UsageAnalysis::from_imports(import_infos);
        let installed_refs: Vec<&str> = installed.iter().map(String::as_str).collect();

        Ok(analysis
            .find_potential_dead_deps(&installed_refs)
            .into_iter()
            .map(|(name, confidence)| DeadPackage {
                name,
                confidence: match confidence {
                    Confidence::High => DeadCodeConfidence::High,
                    Confidence::Medium => DeadCodeConfidence::Medium,
                    Confidence::Low => DeadCodeConfidence::Low,
                },
            })
            .collect())
    }
}

#[derive(Debug, Clone, Copy, serde::Serialize, serde::Deserialize, PartialEq, Eq)]
pub enum DeadCodeConfidence {
    High,
    Medium,
    Low,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn never_imported_package_is_high_confidence() {
        // "requests" imported twice so it doesn't also trip the single-use
        // medium-confidence heuristic in UsageAnalysis::find_potential_dead_deps.
        let imports = vec!["requests".to_string(), "requests".to_string()];
        let installed = vec!["requests".to_string(), "unused-package".to_string()];

        let dead = DeadCodeDetector::find_dead_packages(imports, installed).unwrap();

        assert_eq!(dead, vec!["unused-package".to_string()]);
    }

    #[test]
    fn single_use_package_surfaces_as_medium_confidence_not_high() {
        let imports = vec!["requests".to_string()]; // imported exactly once
        let installed = vec!["requests".to_string()];

        let with_confidence =
            DeadCodeDetector::find_dead_packages_with_confidence(imports.clone(), installed.clone()).unwrap();
        assert_eq!(with_confidence.len(), 1);
        assert_eq!(with_confidence[0].confidence, DeadCodeConfidence::Medium);

        // But the plain high-confidence-only list should NOT include it —
        // "used once" isn't the same claim as "never used".
        let high_only = DeadCodeDetector::find_dead_packages(imports, installed).unwrap();
        assert!(high_only.is_empty());
    }

    #[test]
    fn imported_package_is_not_flagged() {
        let imports = vec!["flask".to_string(), "flask".to_string(), "flask".to_string()];
        let installed = vec!["flask".to_string()];

        let dead = DeadCodeDetector::find_dead_packages(imports, installed).unwrap();
        assert!(dead.is_empty());
    }

    #[test]
    fn dev_tools_are_never_flagged_even_when_unimported() {
        let dead = DeadCodeDetector::find_dead_packages(vec![], vec!["pytest".to_string(), "black".to_string()])
            .unwrap();
        assert!(dead.is_empty());
    }
}
