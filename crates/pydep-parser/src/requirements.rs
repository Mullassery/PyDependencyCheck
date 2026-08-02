use std::path::Path;
use crate::{Dependency, DependencySource, ParserResult, VersionConstraint, VersionSpecifier};

/// Parse a requirements.txt file
pub fn parse_requirements_file(path: &Path) -> ParserResult<Vec<Dependency>> {
    let content = std::fs::read_to_string(path)?;
    parse_requirements(&content, path.to_string_lossy().to_string())
}

/// Parse requirements.txt format (PEP 508)
pub fn parse_requirements(content: &str, source_path: String) -> ParserResult<Vec<Dependency>> {
    let mut dependencies = Vec::new();

    for line in content.lines() {
        let line = line.trim();

        // Skip empty lines and comments
        if line.is_empty() || line.starts_with('#') {
            continue;
        }

        // Skip directives
        if line.starts_with('-') {
            continue;
        }

        // Handle line continuations (backslash)
        let line = if line.ends_with('\\') {
            &line[..line.len()-1]
        } else {
            line
        };

        // Parse dependency
        if let Ok(dep) = parse_pep508_requirement(line, &source_path) {
            dependencies.push(dep);
        }
    }

    Ok(dependencies)
}

/// Parse a single PEP 508 requirement string
/// Format: name [extras] [version-specifier] [environment-marker]
/// Examples:
/// - requests
/// - requests==2.32.0
/// - requests[security]>=2.0,<3.0
/// - django>=3.0; python_version >= "3.8"
pub fn parse_pep508_requirement(req: &str, source_path: &str) -> ParserResult<Dependency> {
    let req = req.trim();
    if req.is_empty() {
        return Err(crate::errors::ParserError::InvalidRequirement(req.to_string()));
    }

    // Split on semicolon to separate environment markers
    let (req_part, markers) = if let Some(pos) = req.find(';') {
        let marker = req[pos+1..].trim().to_string();
        (&req[..pos], Some(marker))
    } else {
        (req, None)
    };

    // Extract extras: name[extra1,extra2] or name
    let (name_part, extras) = if let Some(bracket_pos) = req_part.find('[') {
        if let Some(end_bracket) = req_part.find(']') {
            let name = req_part[..bracket_pos].trim();
            let extras_str = &req_part[bracket_pos+1..end_bracket];
            let extras = extras_str.split(',')
                .map(|s| s.trim().to_string())
                .collect();
            (name, extras)
        } else {
            (req_part, Vec::new())
        }
    } else {
        (req_part, Vec::new())
    };

    // Split name and version constraint
    let (name, version_constraint) = parse_name_and_version(name_part)?;

    Ok(Dependency {
        name: normalize_package_name(&name),
        version_constraint,
        source: DependencySource::RequirementsFile(source_path.to_string()),
        direct: true,
        extras,
        markers,
        dev: false,
        url: None,
        path: None,
    })
}

/// Parse package name and version constraint
/// Returns (name, version_constraint)
fn parse_name_and_version(s: &str) -> ParserResult<(String, Option<VersionConstraint>)> {
    // Version specifiers: ==, !=, <, >, <=, >=, ~=, ===
    let version_operators = ["===", "==", "!=", "<=", ">=", "~=", "<", ">"];

    for op in &version_operators {
        if let Some(pos) = s.find(op) {
            let name = s[..pos].trim();
            let version_part = s[pos..].trim();

            if !name.is_empty() && !version_part.is_empty() {
                let version_constraint = parse_version_constraint(version_part)?;
                return Ok((name.to_string(), Some(version_constraint)));
            }
        }
    }

    // No version constraint found
    Ok((s.to_string(), None))
}

/// Parse version constraint string
/// Examples: ==2.32.0, >=2.0,<3.0, ~=1.4.2
fn parse_version_constraint(s: &str) -> ParserResult<VersionConstraint> {
    let mut specifiers = Vec::new();
    let mut remaining = s;

    while !remaining.is_empty() {
        remaining = remaining.trim();

        // Match operator
        let (op, version_start) = if remaining.starts_with("===") {
            ("===", 3)
        } else if remaining.starts_with("==") {
            ("==", 2)
        } else if remaining.starts_with("!=") {
            ("!=", 2)
        } else if remaining.starts_with("<=") {
            ("<=", 2)
        } else if remaining.starts_with(">=") {
            (">=", 2)
        } else if remaining.starts_with("~=") {
            ("~=", 2)
        } else if remaining.starts_with("<") {
            ("<", 1)
        } else if remaining.starts_with(">") {
            (">", 1)
        } else {
            break;
        };

        remaining = &remaining[version_start..];
        remaining = remaining.trim_start();

        // Extract version number (until comma or end)
        let (version, next_remaining) = if let Some(comma_pos) = remaining.find(',') {
            (remaining[..comma_pos].trim(), &remaining[comma_pos+1..])
        } else {
            (remaining.trim(), "")
        };

        if !version.is_empty() {
            specifiers.push(match op {
                "===" => VersionSpecifier::Exact(version.to_string()),
                "==" => VersionSpecifier::Exact(version.to_string()),
                "!=" => VersionSpecifier::NotEqual(version.to_string()),
                "<" => VersionSpecifier::LessThan(version.to_string()),
                ">" => VersionSpecifier::GreaterThan(version.to_string()),
                "<=" => VersionSpecifier::LessThanOrEqual(version.to_string()),
                ">=" => VersionSpecifier::GreaterThanOrEqual(version.to_string()),
                "~=" => VersionSpecifier::Compatible(version.to_string()),
                _ => continue,
            });
        }

        remaining = next_remaining;
    }

    if specifiers.is_empty() {
        return Err(crate::errors::ParserError::InvalidVersion(s.to_string()));
    }

    Ok(VersionConstraint {
        raw: s.to_string(),
        specifiers,
    })
}

/// Normalize package name according to PEP 503
/// - lowercase
/// - replace underscores and hyphens with single hyphen
fn normalize_package_name(name: &str) -> String {
    name.to_lowercase()
        .chars()
        .map(|c| if c == '_' || c == '.' { '-' } else { c })
        .collect::<String>()
        .split('-')
        .filter(|s| !s.is_empty())
        .collect::<Vec<_>>()
        .join("-")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_simple_requirement() {
        let content = "requests==2.32.0\n";
        let deps = parse_requirements(content, "requirements.txt".to_string()).unwrap();
        assert_eq!(deps.len(), 1);
        assert_eq!(deps[0].name, "requests");
    }

    #[test]
    fn test_parse_requirement_with_extras() {
        let content = "requests[security]>=2.0,<3.0\n";
        let deps = parse_requirements(content, "requirements.txt".to_string()).unwrap();
        assert_eq!(deps.len(), 1);
        assert_eq!(deps[0].name, "requests");
        assert_eq!(deps[0].extras, vec!["security"]);
    }

    #[test]
    fn test_parse_requirement_with_markers() {
        let content = "pywin32; sys_platform == 'win32'\n";
        let deps = parse_requirements(content, "requirements.txt".to_string()).unwrap();
        assert_eq!(deps.len(), 1);
        assert!(deps[0].markers.is_some());
    }

    #[test]
    fn test_normalize_package_name() {
        assert_eq!(normalize_package_name("Django"), "django");
        assert_eq!(normalize_package_name("Django_REST_Framework"), "django-rest-framework");
        assert_eq!(normalize_package_name("my.package"), "my-package");
    }

    #[test]
    fn test_parse_complex_version_constraint() {
        let content = "numpy>=1.20.0,<2.0,!=1.21.0\n";
        let deps = parse_requirements(content, "requirements.txt".to_string()).unwrap();
        assert_eq!(deps.len(), 1);
        assert!(deps[0].version_constraint.is_some());
    }
}
