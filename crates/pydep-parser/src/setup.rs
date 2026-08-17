use crate::{Dependency, ParserResult};
use std::path::Path;

/// Parse a setup.py file
pub fn parse_setup_py(path: &Path) -> ParserResult<Vec<Dependency>> {
    let _content = std::fs::read_to_string(path)?;
    // TODO: Implement AST parsing of setup.py
    Ok(Vec::new())
}

/// Parse a setup.cfg file
pub fn parse_setup_cfg(path: &Path) -> ParserResult<Vec<Dependency>> {
    let _content = std::fs::read_to_string(path)?;
    // TODO: Implement INI parsing of setup.cfg
    Ok(Vec::new())
}
