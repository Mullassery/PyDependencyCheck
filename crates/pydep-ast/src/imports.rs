use crate::{AstResult, ImportInfo, ImportType};
use std::collections::HashSet;
use std::path::Path;

/// Extract all imports from a Python file
pub fn extract_imports(file_path: &Path) -> AstResult<Vec<ImportInfo>> {
    let content = std::fs::read_to_string(file_path)?;
    extract_imports_from_source(&content, &file_path.to_string_lossy())
}

/// Extract imports from Python source code (simple regex-based approach)
/// Handles:
/// - `import module`
/// - `import module as alias`
/// - `import module1, module2`
/// - `from module import name`
/// - `from module import name as alias`
/// - `from . import module` (relative imports)
pub fn extract_imports_from_source(source: &str, file_path: &str) -> AstResult<Vec<ImportInfo>> {
    let mut imports = Vec::new();
    let mut seen = HashSet::new();

    for (line_num, line) in source.lines().enumerate() {
        let trimmed = line.trim();

        // Skip comments and empty lines
        if trimmed.is_empty() || trimmed.starts_with('#') {
            continue;
        }

        // Handle line continuations
        let line_to_parse = trimmed.strip_suffix('\\').unwrap_or(trimmed);

        // Handle `import` statements
        if let Some(rest) = line_to_parse.strip_prefix("import ") {
            let imports_str = rest.split('#').next().unwrap_or(rest); // Remove comments

            for import in imports_str.split(',') {
                let import = import.trim();
                if import.is_empty() {
                    continue;
                }

                // Extract module name (before "as" alias)
                let module = import.split(" as ").next().unwrap_or(import).trim();

                if !seen.insert((module.to_string(), ImportType::Direct)) {
                    continue; // Skip duplicates
                }

                imports.push(ImportInfo {
                    module: module.to_string(),
                    file: file_path.to_string(),
                    line: line_num + 1,
                    import_type: ImportType::Direct,
                });
            }
        }
        // Handle `from ... import` statements
        else if let Some(rest) = line_to_parse.strip_prefix("from ") {
            if let Some(import_part) = rest.split(" import ").next() {
                let module = import_part.trim();

                if !module.is_empty() && !seen.insert((module.to_string(), ImportType::From)) {
                    continue;
                }

                imports.push(ImportInfo {
                    module: module.to_string(),
                    file: file_path.to_string(),
                    line: line_num + 1,
                    import_type: ImportType::From,
                });
            }
        }
        // Handle dynamic imports: importlib.import_module, __import__
        else if line_to_parse.contains("importlib.import_module")
            || line_to_parse.contains("__import__")
        {
            // Extract string literal from import_module("module_name")
            if let Some(start) = line_to_parse.find('(') {
                if let Some(end) = line_to_parse[start..].find(')') {
                    let module_expr = &line_to_parse[start + 1..start + end];
                    // Try to extract quoted string
                    for quote_char in &['"', '\''] {
                        if let Some(quote_start) = module_expr.find(*quote_char) {
                            if let Some(quote_end) =
                                module_expr[quote_start + 1..].find(*quote_char)
                            {
                                let module =
                                    &module_expr[quote_start + 1..quote_start + 1 + quote_end];
                                if !seen.insert((module.to_string(), ImportType::Dynamic)) {
                                    continue;
                                }

                                imports.push(ImportInfo {
                                    module: module.to_string(),
                                    file: file_path.to_string(),
                                    line: line_num + 1,
                                    import_type: ImportType::Dynamic,
                                });
                                break;
                            }
                        }
                    }
                }
            }
        }
    }

    Ok(imports)
}

/// Extract top-level package name from a module path
/// e.g., "requests.auth" -> "requests"
pub fn extract_package_name(module: &str) -> String {
    module.split('.').next().unwrap_or(module).to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simple_import() {
        let source = "import requests\n";
        let imports = extract_imports_from_source(source, "test.py").unwrap();
        assert_eq!(imports.len(), 1);
        assert_eq!(imports[0].module, "requests");
        assert_eq!(imports[0].import_type, ImportType::Direct);
    }

    #[test]
    fn test_from_import() {
        let source = "from flask import Flask\n";
        let imports = extract_imports_from_source(source, "test.py").unwrap();
        assert_eq!(imports.len(), 1);
        assert_eq!(imports[0].module, "flask");
        assert_eq!(imports[0].import_type, ImportType::From);
    }

    #[test]
    fn test_multiple_imports() {
        let source = "import os, sys, requests\n";
        let imports = extract_imports_from_source(source, "test.py").unwrap();
        assert_eq!(imports.len(), 3);
    }

    #[test]
    fn test_alias_import() {
        let source = "import numpy as np\n";
        let imports = extract_imports_from_source(source, "test.py").unwrap();
        assert_eq!(imports.len(), 1);
        assert_eq!(imports[0].module, "numpy");
    }

    #[test]
    fn test_dynamic_import() {
        let source = "importlib.import_module('requests')\n";
        let imports = extract_imports_from_source(source, "test.py").unwrap();
        assert_eq!(imports.len(), 1);
        assert_eq!(imports[0].module, "requests");
        assert_eq!(imports[0].import_type, ImportType::Dynamic);
    }

    #[test]
    fn test_extract_package_name() {
        assert_eq!(extract_package_name("requests.auth"), "requests");
        assert_eq!(extract_package_name("requests"), "requests");
        assert_eq!(extract_package_name("django.contrib.auth"), "django");
    }

    #[test]
    fn test_skip_duplicates() {
        let source = "import requests\nimport requests\n";
        let imports = extract_imports_from_source(source, "test.py").unwrap();
        assert_eq!(imports.len(), 1);
    }
}
