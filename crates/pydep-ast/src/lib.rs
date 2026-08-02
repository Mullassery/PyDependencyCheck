//! PyDependencyCheck AST: Python code analysis
//!
//! Uses tree-sitter to extract:
//! - Import statements
//! - Function calls
//! - Module usage
//! - Dead code detection

pub mod imports;
pub mod usage;
pub mod dead_code;
pub mod errors;

pub use errors::{AstError, AstResult};

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ImportInfo {
    pub module: String,
    pub file: String,
    pub line: usize,
    pub import_type: ImportType,
}

#[derive(Debug, Clone, Copy, serde::Serialize, serde::Deserialize, PartialEq, Eq, Hash)]
pub enum ImportType {
    Direct,      // import module
    From,        // from module import name
    Dynamic,     // importlib.import_module()
    Conditional, // try/except imports
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_import() {
        // TODO: Implement test
    }
}
