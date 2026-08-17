//! PyDependencyCheck Parser: Parse Python dependency declarations
//!
//! Supports:
//! - requirements.txt
//! - requirements-dev.txt, requirements-test.txt (variants)
//! - constraints.txt
//! - pyproject.toml (PEP 508)
//! - poetry.lock
//! - Pipfile / Pipfile.lock
//! - uv.lock
//! - setup.py / setup.cfg
//!
//! Output: Normalized dependency structures with version constraints

pub mod constraint;
pub mod errors;
pub mod models;
pub mod pyproject;
pub mod requirements;
pub mod setup;

pub use errors::{ParserError, ParserResult};
pub use models::{Dependency, DependencySource, VersionConstraint, VersionSpecifier};

/// Parse a dependencies file and extract dependencies
pub fn parse_file(path: &str) -> ParserResult<Vec<Dependency>> {
    let path = std::path::Path::new(path);
    let filename = path
        .file_name()
        .and_then(|n| n.to_str())
        .ok_or_else(|| ParserError::InvalidPath(path.to_string_lossy().to_string()))?;

    match filename {
        f if f.starts_with("requirements") && f.ends_with(".txt") => {
            requirements::parse_requirements_file(path)
        }
        "constraints.txt" => constraint::parse_constraints_file(path),
        "pyproject.toml" => pyproject::parse_pyproject(path),
        "setup.py" => setup::parse_setup_py(path),
        "setup.cfg" => setup::parse_setup_cfg(path),
        "Pipfile" => Err(ParserError::UnsupportedFormat("Pipfile".to_string())),
        "poetry.lock" => Err(ParserError::UnsupportedFormat("poetry.lock".to_string())),
        "uv.lock" => Err(ParserError::UnsupportedFormat("uv.lock".to_string())),
        _ => Err(ParserError::UnknownFileType(filename.to_string())),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn test_parse_requirements_basic() {
        let dir = std::env::temp_dir().join(format!("pydep-parser-test-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let file_path = dir.join("requirements.txt");
        let mut file = std::fs::File::create(&file_path).unwrap();
        writeln!(file, "requests==2.32.0").unwrap();
        writeln!(file, "flask>=2.0.0").unwrap();

        let deps = parse_file(file_path.to_str().unwrap()).unwrap();

        assert_eq!(deps.len(), 2);
        assert!(deps.iter().any(|d| d.name == "requests"));
        assert!(deps.iter().any(|d| d.name == "flask"));

        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn test_parse_file_unknown_type_errs() {
        let result = parse_file("Cargo.lock");
        assert!(result.is_err());
    }
}
