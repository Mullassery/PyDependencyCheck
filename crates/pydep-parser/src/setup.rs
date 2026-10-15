use crate::{Dependency, ParserResult};
use std::path::Path;

/// Parse a setup.py file
pub fn parse_setup_py(path: &Path) -> ParserResult<Vec<Dependency>> {
    let content = std::fs::read_to_string(path)?;
    let source_path = path.to_string_lossy().to_string();
    let mut dependencies = Vec::new();

    if let Some(start_idx) = content.find("install_requires") {
        if let Some(bracket_start) = content[start_idx..].find('[') {
            let start = start_idx + bracket_start + 1;
            if let Some(bracket_end) = content[start..].find(']') {
                let block = &content[start..start + bracket_end];
                for part in block.split(',') {
                    let cleaned = part.trim().trim_matches(|c| c == '\'' || c == '"' || c == ' ' || c == '\n' || c == '\r');
                    if !cleaned.is_empty() && !cleaned.starts_with('#') {
                        if let Ok(dep) = crate::requirements::parse_pep508_requirement(cleaned, &source_path) {
                            dependencies.push(dep);
                        }
                    }
                }
            }
        }
    }

    Ok(dependencies)
}

/// Parse a setup.cfg file
pub fn parse_setup_cfg(path: &Path) -> ParserResult<Vec<Dependency>> {
    let content = std::fs::read_to_string(path)?;
    let source_path = path.to_string_lossy().to_string();
    let mut dependencies = Vec::new();

    let mut in_install_requires = false;
    for line in content.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("install_requires") && trimmed.contains('=') {
            in_install_requires = true;
            let after_eq = trimmed.split('=').nth(1).unwrap_or("").trim();
            if !after_eq.is_empty() {
                if let Ok(dep) = crate::requirements::parse_pep508_requirement(after_eq, &source_path) {
                    dependencies.push(dep);
                }
            }
            continue;
        }

        if in_install_requires {
            if line.starts_with(' ') || line.starts_with('\t') {
                let dep_str = trimmed.trim_start_matches("- ");
                if !dep_str.is_empty() && !dep_str.starts_with('#') {
                    if let Ok(dep) = crate::requirements::parse_pep508_requirement(dep_str, &source_path) {
                        dependencies.push(dep);
                    }
                }
            } else if !trimmed.is_empty() {
                in_install_requires = false;
            }
        }
    }

    Ok(dependencies)
}
