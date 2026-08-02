use std::path::Path;
use crate::{Dependency, DependencySource, ParserResult};

/// Parse a requirements.txt file
pub fn parse_requirements_file(path: &Path) -> ParserResult<Vec<Dependency>> {
    let content = std::fs::read_to_string(path)?;
    parse_requirements(&content, path.to_string_lossy().to_string())
}

/// Parse requirements.txt format (PEP 508)
pub fn parse_requirements(content: &str, source_path: String) -> ParserResult<Vec<Dependency>> {
    let mut dependencies = Vec::new();

    for (line_num, line) in content.lines().enumerate() {
        let line = line.trim();

        // Skip empty lines and comments
        if line.is_empty() || line.starts_with('#') {
            continue;
        }

        // Skip environment markers and other directives
        if line.starts_with('-') {
            continue;
        }

        // Parse dependency (simplified)
        // TODO: Full PEP 508 parser
        if let Ok(dep) = parse_pep508_requirement(line, &source_path) {
            dependencies.push(dep);
        }
    }

    Ok(dependencies)
}

/// Parse a single PEP 508 requirement string
/// Format: name [extras] [version-specifier] [environment-marker]
fn parse_pep508_requirement(req: &str, source_path: &str) -> ParserResult<Dependency> {
    // TODO: Implement full PEP 508 parser with proper parsing
    let name = req.split('=').next().unwrap_or(req).trim();

    Ok(Dependency {
        name: name.to_lowercase(),
        version_constraint: None,
        source: DependencySource::RequirementsFile(source_path.to_string()),
        direct: true,
        extras: Vec::new(),
        markers: None,
        dev: false,
        url: None,
        path: None,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_simple_requirement() {
        let content = "requests==2.32.0\n";
        let deps = parse_requirements(content, "requirements.txt".to_string()).unwrap();
        assert!(!deps.is_empty());
    }
}
