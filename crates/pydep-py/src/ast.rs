use pydep_ast::dead_code::{DeadCodeConfidence, DeadCodeDetector};
use pydep_ast::imports::{extract_imports_from_source, extract_package_name};
use pyo3::prelude::*;
use std::path::Path;

const SKIP_DIRS: &[&str] = &[
    ".git", "__pycache__", ".venv", "venv", "env", "node_modules", "target", ".tox", ".mypy_cache",
    ".pytest_cache", "build", "dist", "site-packages",
];

fn collect_py_files(dir: &Path, out: &mut Vec<std::path::PathBuf>) -> std::io::Result<()> {
    if !dir.is_dir() {
        return Ok(());
    }
    for entry in std::fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir() {
            let name = path.file_name().and_then(|n| n.to_str()).unwrap_or("");
            if SKIP_DIRS.contains(&name) {
                continue;
            }
            collect_py_files(&path, out)?;
        } else if path.extension().and_then(|e| e.to_str()) == Some("py") {
            out.push(path);
        }
    }
    Ok(())
}

/// Scan a project directory for all imported top-level package names
/// (deduplicated, normalized to their import-time name).
#[pyfunction]
pub fn scan_imports(project_path: &str) -> PyResult<Vec<String>> {
    let mut files = Vec::new();
    collect_py_files(Path::new(project_path), &mut files)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;

    let mut packages: Vec<String> = Vec::new();
    for file in &files {
        let content = match std::fs::read_to_string(file) {
            Ok(c) => c,
            Err(_) => continue, // skip unreadable files (binary, permissions, etc.)
        };
        let file_str = file.to_string_lossy();
        if let Ok(imports) = extract_imports_from_source(&content, &file_str) {
            for import in imports {
                let package = extract_package_name(&import.module);
                if !packages.contains(&package) {
                    packages.push(package);
                }
            }
        }
    }
    Ok(packages)
}

/// Find dependencies declared as installed but never imported anywhere in
/// the project's source tree. Returns (package_name, confidence) pairs,
/// confidence being one of "High" | "Medium" | "Low".
#[pyfunction]
pub fn find_dead_packages(project_path: &str, installed: Vec<String>) -> PyResult<Vec<(String, String)>> {
    let imports = scan_imports(project_path)?;

    let dead = DeadCodeDetector::find_dead_packages_with_confidence(imports, installed)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(dead
        .into_iter()
        .map(|d| {
            let confidence = match d.confidence {
                DeadCodeConfidence::High => "High",
                DeadCodeConfidence::Medium => "Medium",
                DeadCodeConfidence::Low => "Low",
            };
            (d.name, confidence.to_string())
        })
        .collect())
}

pub fn register_ast(module: &PyModule) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(scan_imports, module)?)?;
    module.add_function(wrap_pyfunction!(find_dead_packages, module)?)?;
    Ok(())
}
