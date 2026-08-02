use std::path::Path;
use crate::{Dependency, DependencySource, ParserResult};

/// Parse a pyproject.toml file
pub fn parse_pyproject(path: &Path) -> ParserResult<Vec<Dependency>> {
    let content = std::fs::read_to_string(path)?;
    let toml_value: toml::Value = toml::from_str(&content)?;

    let mut dependencies = Vec::new();

    // Extract from [project] dependencies
    if let Some(project) = toml_value.get("project") {
        if let Some(deps) = project.get("dependencies").and_then(|d| d.as_array()) {
            for dep in deps {
                if let Some(dep_str) = dep.as_str() {
                    if let Ok(parsed) = parse_pep508_requirement(dep_str, path.to_string_lossy().to_string()) {
                        dependencies.push(parsed);
                    }
                }
            }
        }

        // Extract from [project.optional-dependencies]
        if let Some(optional) = project.get("optional-dependencies").and_then(|o| o.as_table()) {
            for (_key, deps) in optional {
                if let Some(deps_array) = deps.as_array() {
                    for dep in deps_array {
                        if let Some(dep_str) = dep.as_str() {
                            if let Ok(mut parsed) = parse_pep508_requirement(dep_str, path.to_string_lossy().to_string()) {
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
        if let Some(deps) = poetry.get("dependencies").and_then(|d| d.as_table()) {
            for (name, _version) in deps {
                if name != "python" {
                    dependencies.push(Dependency {
                        name: name.to_lowercase(),
                        version_constraint: None,
                        source: DependencySource::PyProjectToml(path.to_string_lossy().to_string()),
                        direct: true,
                        extras: Vec::new(),
                        markers: None,
                        dev: false,
                        url: None,
                        path: None,
                    });
                }
            }
        }

        if let Some(dev_deps) = poetry.get("dev-dependencies").and_then(|d| d.as_table()) {
            for (name, _version) in dev_deps {
                dependencies.push(Dependency {
                    name: name.to_lowercase(),
                    version_constraint: None,
                    source: DependencySource::PyProjectToml(path.to_string_lossy().to_string()),
                    direct: true,
                    extras: Vec::new(),
                    markers: None,
                    dev: true,
                    url: None,
                    path: None,
                });
            }
        }
    }

    Ok(dependencies)
}

fn parse_pep508_requirement(req: &str, source_path: String) -> ParserResult<Dependency> {
    let name = req.split('=').next().unwrap_or(req).trim();

    Ok(Dependency {
        name: name.to_lowercase(),
        version_constraint: None,
        source: DependencySource::PyProjectToml(source_path),
        direct: true,
        extras: Vec::new(),
        markers: None,
        dev: false,
        url: None,
        path: None,
    })
}
