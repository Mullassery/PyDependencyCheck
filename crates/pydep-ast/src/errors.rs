use thiserror::Error;

pub type AstResult<T> = Result<T, AstError>;

#[derive(Error, Debug)]
pub enum AstError {
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Parse error: {0}")]
    ParseError(String),

    #[error("Invalid file: {0}")]
    InvalidFile(String),

    #[error("Unknown error: {0}")]
    Unknown(String),
}
