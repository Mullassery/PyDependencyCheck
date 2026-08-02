use thiserror::Error;

pub type ParserResult<T> = Result<T, ParserError>;

#[derive(Error, Debug)]
pub enum ParserError {
    #[error("Invalid file path: {0}")]
    InvalidPath(String),

    #[error("Unknown file type: {0}")]
    UnknownFileType(String),

    #[error("Unsupported format: {0}")]
    UnsupportedFormat(String),

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Invalid TOML: {0}")]
    TomlError(#[from] toml::de::Error),

    #[error("Invalid JSON: {0}")]
    JsonError(#[from] serde_json::Error),

    #[error("Invalid version specifier: {0}")]
    InvalidVersion(String),

    #[error("Parse error at line {line}: {message}")]
    ParseError { line: usize, message: String },

    #[error("Invalid PEP 508 requirement: {0}")]
    InvalidRequirement(String),

    #[error("Unknown error: {0}")]
    Unknown(String),
}
