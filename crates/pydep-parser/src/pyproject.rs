use super::requirements;
use crate::{Dependency, ParserResult};
use std::path::Path;

/// Parse a pyproject.toml file
pub fn parse_pyproject(path: &Path) -> ParserResult<Vec<Dependency>> {
    let content = std::fs::read_to_string(path)?;
    let toml_value: toml::Value = toml::from_str(&content)?;

    let mut dependencies = Vec::new();
    let source_path = path.to_string_lossy().to_string();

    // Extract from [project] dependencies (PEP 621)
    if let Some(project) = toml_value.get("project") {
        if let Some(deps) = project.get("dependencies").and_then(|d| d.as_array()) {
            for dep in deps {
                if let Some(dep_str) = dep.as_str() {
                    if let Ok(parsed) =
                        requirements::parse_pep508_requirement(dep_str, &source_path)
                    {
                        dependencies.push(parsed);
                    }
                }
            }
        }

        // Extract from [project.optional-dependencies]
        if let Some(optional) = project
            .get("optional-dependencies")
            .and_then(|o| o.as_table())
        {
            for (_key, deps_value) in optional {
                if let Some(deps_array) = deps_value.as_array() {
                    for dep in deps_array {
                        if let Some(dep_str) = dep.as_str() {
                            if let Ok(mut parsed) =
                                requirements::parse_pep508_requirement(dep_str, &source_path)
                            {
                                parsed.dev = true;
                                dependencies.push(parsed);
                            }
                        }
                    }
                }
            }
        }
    }

    // Extract from [tool.poetry] dependencies
    if let Some(poetry) = toml_value.get("tool").and_then(|t| t.get("poetry")) {
        // Main dependencies
        if let Some(deps) = poetry.get("dependencies").and_then(|d| d.as_table()) {
            for (name, version_value) in deps {
                if name != "python" {
                    let dep_str = if let Some(version_str) = version_value.as_str() {
                        format!("{}=={}", name, version_str)
                    } else {
                        name.to_string()
                    };

                    if let Ok(parsed) =
                        requirements::parse_pep508_requirement(&dep_str, &source_path)
                    {
                        dependencies.push(parsed);
                    }
                }
            }
        }

        // Dev dependencies
        if let Some(dev_deps) = poetry.get("dev-dependencies").and_then(|d| d.as_table()) {
            for (name, version_value) in dev_deps {
                let dep_str = if let Some(version_str) = version_value.as_str() {
                    format!("{}=={}", name, version_str)
                } else {
                    name.to_string()
                };

                if let Ok(mut parsed) =
                    requirements::parse_pep508_requirement(&dep_str, &source_path)
                {
                    parsed.dev = true;
                    dependencies.push(parsed);
                }
            }
        }

        // Group dependencies (poetry 1.2+)
        if let Some(groups) = poetry.get("group").and_then(|g| g.as_table()) {
            for (group_name, group_value) in groups {
                let is_dev = matches!(group_name.as_str(), "dev" | "test" | "docs");

                if let Some(deps) = group_value.get("dependencies").and_then(|d| d.as_table()) {
                    for (name, version_value) in deps {
                        let dep_str = if let Some(version_str) = version_value.as_str() {
                            format!("{}=={}", name, version_str)
                        } else {
                            name.to_string()
                        };

                        if let Ok(mut parsed) =
                            requirements::parse_pep508_requirement(&dep_str, &source_path)
                        {
                            parsed.dev = is_dev;
                            dependencies.push(parsed);
                        }
                    }
                }
            }
        }
    }

    Ok(dependencies)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    fn write_temp_pyproject(content: &str, suffix: &str) -> std::path::PathBuf {
        let dir = std::env::temp_dir().join(format!(
            "pydep-pyproject-test-{}-{}",
            std::process::id(),
            suffix
        ));
        std::fs::create_dir_all(&dir).unwrap();
        let file_path = dir.join("pyproject.toml");
        let mut file = std::fs::File::create(&file_path).unwrap();
        file.write_all(content.as_bytes()).unwrap();
        file_path
    }

    #[test]
    fn test_parse_pep621_pyproject() {
        let content = r#"
[project]
dependencies = [
    "requests>=2.0",
    "flask[async]>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=6.0", "black>=22.0"]
"#;
        let path = write_temp_pyproject(content, "pep621");
        let deps = parse_pyproject(&path).unwrap();

        assert!(deps.iter().any(|d| d.name == "requests"));
        assert!(deps.iter().any(|d| d.name == "flask"));
        assert!(deps.iter().any(|d| d.name == "pytest"));
        assert!(deps.iter().any(|d| d.name == "black"));

        std::fs::remove_dir_all(path.parent().unwrap()).unwrap();
    }

    #[test]
    fn test_parse_poetry_pyproject() {
        let content = r#"
[tool.poetry.dependencies]
python = "^3.8"
requests = "^2.28.0"
flask = {version = "^2.0", extras = ["async"]}

[tool.poetry.dev-dependencies]
pytest = "^7.0"
black = "^22.0"
"#;
        let path = write_temp_pyproject(content, "poetry");
        let deps = parse_pyproject(&path).unwrap();

        // "python" itself should not be treated as a dependency
        assert!(!deps.iter().any(|d| d.name == "python"));
        assert!(deps.iter().any(|d| d.name == "requests"));
        assert!(deps.iter().any(|d| d.name == "flask"));

        std::fs::remove_dir_all(path.parent().unwrap()).unwrap();
    }
}
