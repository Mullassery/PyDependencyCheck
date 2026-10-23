use crate::{Dependency, ParserResult};
use std::path::Path;

/// Parse a setup.py file
pub fn parse_setup_py(path: &Path) -> ParserResult<Vec<Dependency>> {
    let content = std::fs::read_to_string(path)?;
    let source_path = path.to_string_lossy().to_string();
    let mut dependencies = Vec::new();

    if let Some(block) = extract_list_block(&content, "install_requires") {
        parse_requirement_literals(block, &source_path, false, &mut dependencies);
    }

    if let Some(block) = extract_braced_block(&content, "extras_require") {
        for list in extract_nested_lists(block) {
            parse_requirement_literals(list, &source_path, true, &mut dependencies);
        }
    }

    Ok(dependencies)
}

/// Parse a setup.cfg file.
///
/// Both ``[options] install_requires`` and ``[options.extras_require]`` are
/// collected. Extras are marked as development dependencies so scanners and
/// remediation logic can distinguish runtime requirements from optional ones.
pub fn parse_setup_cfg(path: &Path) -> ParserResult<Vec<Dependency>> {
    let content = std::fs::read_to_string(path)?;
    let source_path = path.to_string_lossy().to_string();
    let mut dependencies = Vec::new();
    let mut section = String::new();
    let mut active_requirement_block: Option<bool> = None;

    for raw_line in content.lines() {
        let line = strip_inline_comment(raw_line);
        let trimmed = line.trim();

        if trimmed.is_empty() || trimmed.starts_with('#') || trimmed.starts_with(';') {
            continue;
        }

        if trimmed.starts_with('[') && trimmed.ends_with(']') {
            section = trimmed[1..trimmed.len() - 1].trim().to_ascii_lowercase();
            active_requirement_block = None;
            continue;
        }

        let is_indented = line.starts_with(' ') || line.starts_with('\t');

        if !is_indented {
            if let Some((key, value)) = trimmed.split_once('=') {
                let key = key.trim().to_ascii_lowercase();
                let is_install_requires = section == "options" && key == "install_requires";
                let is_extra = section == "options.extras_require";

                if is_install_requires || is_extra {
                    active_requirement_block = Some(is_extra);
                    let value = value.trim();
                    if !value.is_empty() {
                        if let Ok(dep) =
                            crate::requirements::parse_pep508_requirement(value, &source_path)
                        {
                            dependencies.push(Dependency {
                                dev: is_extra,
                                ..dep
                            });
                        }
                    }
                    continue;
                }
            }

            active_requirement_block = None;
            continue;
        }

        if let Some(dev) = active_requirement_block {
            let requirement = trimmed.trim_start_matches("- ").trim();
            if !requirement.is_empty() && !requirement.starts_with('#') {
                if let Ok(dep) =
                    crate::requirements::parse_pep508_requirement(requirement, &source_path)
                {
                    dependencies.push(Dependency { dev, ..dep });
                }
            }
        }
    }

    Ok(dependencies)
}

/// Find ``key = [ ... ]`` and return the contents of the list, ignoring
/// brackets that appear inside string literals (for example ``foo[extra]``).
fn extract_list_block<'a>(content: &'a str, key: &str) -> Option<&'a str> {
    let start = content.find(key)?;
    let after_key = &content[start + key.len()..];
    let bracket_start = after_key.find('[')?;
    extract_delimited(&after_key[bracket_start..], '[', ']')
}

/// Find ``key = { ... }`` and return the contents of the mapping.
fn extract_braced_block<'a>(content: &'a str, key: &str) -> Option<&'a str> {
    let start = content.find(key)?;
    let after_key = &content[start + key.len()..];
    let brace_start = after_key.find('{')?;
    extract_delimited(&after_key[brace_start..], '{', '}')
}

/// Return the contents between matching delimiters, skipping delimiters inside
/// Python string literals.
fn extract_delimited(text: &str, open: char, close: char) -> Option<&str> {
    let mut depth = 0usize;
    let mut quote: Option<char> = None;
    let mut escaped = false;

    for (offset, ch) in text.char_indices() {
        if let Some(active_quote) = quote {
            if escaped {
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if ch == active_quote {
                quote = None;
            }
            continue;
        }

        match ch {
            '\'' | '"' => quote = Some(ch),
            c if c == open => {
                depth += 1;
                if depth == 1 {
                    // Return the slice after the opening delimiter.
                    return extract_delimited_from(&text[offset + ch.len_utf8()..], open, close);
                }
            }
            _ => {}
        }
    }

    None
}

fn extract_delimited_from(text: &str, open: char, close: char) -> Option<&str> {
    let mut depth = 1usize;
    let mut quote: Option<char> = None;
    let mut escaped = false;

    for (offset, ch) in text.char_indices() {
        if let Some(active_quote) = quote {
            if escaped {
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if ch == active_quote {
                quote = None;
            }
            continue;
        }

        match ch {
            '\'' | '"' => quote = Some(ch),
            c if c == open => depth += 1,
            c if c == close => {
                depth -= 1;
                if depth == 0 {
                    return Some(&text[..offset]);
                }
            }
            _ => {}
        }
    }

    None
}

/// Find every ``[...]`` list inside ``text`` and return their contents.
fn extract_nested_lists(text: &str) -> Vec<&str> {
    let mut lists = Vec::new();
    let mut offset = 0usize;

    while let Some(relative_start) = text[offset..].find('[') {
        let start = offset + relative_start;
        let Some(block) = extract_delimited(&text[start..], '[', ']') else {
            break;
        };
        lists.push(block);

        let block_start = start + 1;
        offset = block_start + block.len() + 1;

        if offset >= text.len() {
            break;
        }
    }

    lists
}

/// Parse quoted requirement strings from a Python list literal. Splitting on
/// commas is wrong because constraints such as ``requests>=2.0,<3`` contain
/// commas themselves.
fn parse_requirement_literals(
    text: &str,
    source_path: &str,
    dev: bool,
    dependencies: &mut Vec<Dependency>,
) {
    let mut chars = text.char_indices().peekable();

    while let Some((_, ch)) = chars.next() {
        if ch != '\'' && ch != '"' {
            continue;
        }

        let quote = ch;
        let mut value = String::new();
        let mut escaped = false;

        for (_, inner) in chars.by_ref() {
            if escaped {
                value.push(inner);
                escaped = false;
            } else if inner == '\\' {
                escaped = true;
            } else if inner == quote {
                break;
            } else {
                value.push(inner);
            }
        }

        let requirement = value.trim();
        if requirement.is_empty() {
            continue;
        }

        if let Ok(dep) = crate::requirements::parse_pep508_requirement(requirement, source_path) {
            dependencies.push(Dependency { dev, ..dep });
        }
    }
}

/// Strip a ``#`` comment while leaving URL fragments such as ``#egg=`` alone.
fn strip_inline_comment(line: &str) -> &str {
    let mut previous_is_whitespace = true;

    for (offset, ch) in line.char_indices() {
        if ch == '#' && previous_is_whitespace {
            return line[..offset].trim_end();
        }
        previous_is_whitespace = ch.is_whitespace();
    }

    line
}
