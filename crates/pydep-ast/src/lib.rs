//! PyDependencyCheck AST: Python code analysis
//!
//! Uses tree-sitter to extract:
//! - Import statements
//! - Function calls
//! - Module usage
//! - Dead code detection

pub mod dead_code;
pub mod errors;
pub mod imports;
pub mod usage;

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
    use crate::imports::extract_imports_from_source;

    #[test]
    fn test_parse_import() {
        let source = "import requests\nfrom flask import Flask\n";
        let imports = extract_imports_from_source(source, "test.py").unwrap();

        assert_eq!(imports.len(), 2);
        assert_eq!(imports[0].module, "requests");
        assert_eq!(imports[0].import_type, ImportType::Direct);
        assert_eq!(imports[1].module, "flask");
        assert_eq!(imports[1].import_type, ImportType::From);
    }
}
