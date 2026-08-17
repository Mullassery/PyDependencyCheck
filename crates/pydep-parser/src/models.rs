use serde::{Deserialize, Serialize};
use std::fmt;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub struct Dependency {
    /// Package name (normalized: lowercase, hyphens/underscores normalized)
    pub name: String,

    /// Version constraints (e.g., ">=1.0,<2.0")
    pub version_constraint: Option<VersionConstraint>,

    /// Which file this dependency came from
    pub source: DependencySource,

    /// Is this a direct dependency or transitive?
    pub direct: bool,

    /// Optional extras (e.g., requests[security])
    pub extras: Vec<String>,

    /// Environment markers (e.g., python_version >= "3.8")
    pub markers: Option<String>,

    /// Is this a development dependency?
    pub dev: bool,

    /// VCS URL (e.g., git+https://...)
    pub url: Option<String>,

    /// Path dependency (e.g., ./local-package)
    pub path: Option<String>,
}

impl fmt::Display for Dependency {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.name)?;
        if let Some(version) = &self.version_constraint {
            write!(f, "{}", version)?;
        }
        if !self.extras.is_empty() {
            write!(f, "[{}]", self.extras.join(","))?;
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub struct VersionConstraint {
    /// Raw version specifier (e.g., ">=1.0,<2.0")
    pub raw: String,

    /// Parsed version specifiers
    pub specifiers: Vec<VersionSpecifier>,
}

impl fmt::Display for VersionConstraint {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.raw)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum VersionSpecifier {
    Exact(String),              // ==1.0.0
    GreaterThan(String),        // >1.0.0
    GreaterThanOrEqual(String), // >=1.0.0
    LessThan(String),           // <1.0.0
    LessThanOrEqual(String),    // <=1.0.0
    NotEqual(String),           // !=1.0.0
    Compatible(String),         // ~=1.0.0
    Wildcard(String),           // ==1.0.*
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum DependencySource {
    RequirementsFile(String), // path to requirements.txt
    PyProjectToml(String),    // path to pyproject.toml
    SetupPy(String),          // path to setup.py
    SetupCfg(String),         // path to setup.cfg
    PoetryLock(String),       // path to poetry.lock
    PipfileLock(String),      // path to Pipfile.lock
    UvLock(String),           // path to uv.lock
}

impl fmt::Display for DependencySource {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::RequirementsFile(p) => write!(f, "requirements:{}", p),
            Self::PyProjectToml(p) => write!(f, "pyproject.toml:{}", p),
            Self::SetupPy(p) => write!(f, "setup.py:{}", p),
            Self::SetupCfg(p) => write!(f, "setup.cfg:{}", p),
            Self::PoetryLock(p) => write!(f, "poetry.lock:{}", p),
            Self::PipfileLock(p) => write!(f, "Pipfile.lock:{}", p),
            Self::UvLock(p) => write!(f, "uv.lock:{}", p),
        }
    }
}
