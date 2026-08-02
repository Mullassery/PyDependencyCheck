use std::path::Path;
use crate::{Dependency, DependencySource, ParserResult};

/// Parse a constraints.txt file
pub fn parse_constraints_file(path: &Path) -> ParserResult<Vec<Dependency>> {
    let content = std::fs::read_to_string(path)?;
    parse_constraints(&content, path.to_string_lossy().to_string())
}

/// Parse constraints.txt format (similar to requirements.txt)
pub fn parse_constraints(content: &str, source_path: String) -> ParserResult<Vec<Dependency>> {
    let mut dependencies = Vec::new();

    for line in content.lines() {
        let line = line.trim();

        if line.is_empty() || line.starts_with('#') {
            continue;
        }

        if line.starts_with('-') {
            continue;
        }

        let name = line.split('=').next().unwrap_or(line).trim();
        dependencies.push(Dependency {
            name: name.to_lowercase(),
            version_constraint: None,
            source: DependencySource::RequirementsFile(source_path.clone()),
            direct: true,
            extras: Vec::new(),
            markers: None,
            dev: false,
            url: None,
            path: None,
        });
    }

    Ok(dependencies)
}
