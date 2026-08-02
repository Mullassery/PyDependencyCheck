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

pub mod errors;
pub mod requirements;
pub mod pyproject;
pub mod setup;
pub mod constraint;
pub mod models;

pub use errors::{ParserError, ParserResult};
pub use models::{Dependency, VersionConstraint, VersionSpecifier, DependencySource};

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
        f if f == "constraints.txt" => {
            constraint::parse_constraints_file(path)
        }
        f if f == "pyproject.toml" => {
            pyproject::parse_pyproject(path)
        }
        f if f == "setup.py" => {
            setup::parse_setup_py(path)
        }
        f if f == "setup.cfg" => {
            setup::parse_setup_cfg(path)
        }
        f if f == "Pipfile" => {
            Err(ParserError::UnsupportedFormat("Pipfile".to_string()))
        }
        f if f == "poetry.lock" => {
            Err(ParserError::UnsupportedFormat("poetry.lock".to_string()))
        }
        f if f == "uv.lock" => {
            Err(ParserError::UnsupportedFormat("uv.lock".to_string()))
        }
        _ => Err(ParserError::UnknownFileType(filename.to_string())),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_requirements_basic() {
        // TODO: Implement test fixtures
    }
}
