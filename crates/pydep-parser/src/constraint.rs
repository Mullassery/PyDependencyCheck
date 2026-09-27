use crate::requirements::parse_pep508_requirement;
use crate::{Dependency, ParserResult};
use std::path::Path;

/// Parse a constraints.txt file
pub fn parse_constraints_file(path: &Path) -> ParserResult<Vec<Dependency>> {
    let content = std::fs::read_to_string(path)?;
    parse_constraints(&content, path.to_string_lossy().to_string())
}

/// Parse constraints.txt format. Per pip's own docs, a constraints file uses
/// exactly the same PEP 508 requirement-line syntax as requirements.txt
/// (`name==1.2.3`, `name>=1.0,<2.0`, etc.) -- it's just restricted to
/// pinning/bounding versions rather than declaring what to install. This
/// used to be hand-rolled here with `line.split('=').next()` to grab the
/// name and *always* set `version_constraint: None`, which had two real
/// bugs: (1) every constraint's version was silently discarded regardless
/// of what was written, so a package pinned only via constraints.txt was
/// never checked for vulnerabilities against a real version; and (2) for
/// any operator other than a bare `=` (e.g. `requests>=2.28.0,<3.0`),
/// splitting on the first `=` character corrupted the name itself --
/// `"requests>=2.28.0,<3.0".split('=').next()` returns `"requests>"`, a
/// stray `>` left attached to the package name. Delegating to the same
/// `parse_pep508_requirement` requirements.txt already uses (7 existing
/// unit tests covering extras/markers/complex constraints) fixes both.
pub fn parse_constraints(content: &str, source_path: String) -> ParserResult<Vec<Dependency>> {
    let mut dependencies = Vec::new();

    for line in content.lines() {
        let line = line.trim();

        if line.is_empty() || line.starts_with('#') {
            continue;
        }

        if line.starts_with('-') {
            continue;
        }

        let line = line.strip_suffix('\\').unwrap_or(line);

        if let Ok(dep) = parse_pep508_requirement(line, &source_path) {
            dependencies.push(dep);
        }
    }

    Ok(dependencies)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Regression test: an exact pin's version used to be silently
    /// discarded (`version_constraint` was hardcoded to `None` for every
    /// constraints.txt line, regardless of content).
    #[test]
    fn exact_pin_keeps_its_version_constraint() {
        let deps = parse_constraints("django==4.2.1\n", "constraints.txt".to_string()).unwrap();
        assert_eq!(deps.len(), 1);
        assert_eq!(deps[0].name, "django");
        let constraint = deps[0]
            .version_constraint
            .as_ref()
            .expect("version constraint should be preserved, not discarded");
        assert_eq!(constraint.raw, "==4.2.1");
    }

    /// Regression test: any operator other than a bare `=` used to corrupt
    /// the package name, since the old implementation split on the first
    /// literal `=` character -- `"requests>=2.28.0,<3.0".split('=').next()`
    /// returned `"requests>"` (a stray `>` left on the name) with the
    /// version thrown away entirely.
    #[test]
    fn range_constraint_keeps_clean_name_and_version() {
        let deps =
            parse_constraints("requests>=2.28.0,<3.0\n", "constraints.txt".to_string()).unwrap();
        assert_eq!(deps.len(), 1);
        assert_eq!(deps[0].name, "requests");
        let constraint = deps[0].version_constraint.as_ref().unwrap();
        assert_eq!(constraint.raw, ">=2.28.0,<3.0");
    }

    #[test]
    fn comments_and_directives_are_skipped() {
        let content = "# a comment\n-r requirements.txt\nflask==2.3.0\n";
        let deps = parse_constraints(content, "constraints.txt".to_string()).unwrap();
        assert_eq!(deps.len(), 1);
        assert_eq!(deps[0].name, "flask");
    }
}
