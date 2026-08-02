use crate::{ImportInfo, ImportType, AstResult};
use std::path::Path;

/// Extract all imports from a Python file
pub fn extract_imports(file_path: &Path) -> AstResult<Vec<ImportInfo>> {
    let _content = std::fs::read_to_string(file_path)?;
    // TODO: Use tree-sitter to extract imports
    Ok(Vec::new())
}

/// Extract imports from Python source code
pub fn extract_imports_from_source(source: &str, file_path: &str) -> AstResult<Vec<ImportInfo>> {
    let mut imports = Vec::new();

    for (line_num, line) in source.lines().enumerate() {
        let trimmed = line.trim();

        // Simple import detection (TODO: use tree-sitter for accuracy)
        if trimmed.starts_with("import ") {
            let module = trimmed.strip_prefix("import ").unwrap_or("").split(',').next().unwrap_or("").trim();
            imports.push(ImportInfo {
                module: module.to_string(),
                file: file_path.to_string(),
                line: line_num + 1,
                import_type: ImportType::Direct,
            });
        } else if trimmed.starts_with("from ") && trimmed.contains(" import ") {
            let module_part = trimmed.strip_prefix("from ").unwrap_or("").split(" import ").next().unwrap_or("").trim();
            imports.push(ImportInfo {
                module: module_part.to_string(),
                file: file_path.to_string(),
                line: line_num + 1,
                import_type: ImportType::From,
            });
        }
    }

    Ok(imports)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_imports_from_source() {
        let source = "import requests\nfrom flask import Flask\n";
        let imports = extract_imports_from_source(source, "test.py").unwrap();
        assert_eq!(imports.len(), 2);
    }
}
