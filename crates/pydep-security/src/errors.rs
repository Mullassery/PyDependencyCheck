use thiserror::Error;

pub type SecurityResult<T> = Result<T, SecurityError>;

#[derive(Error, Debug)]
pub enum SecurityError {
    #[error("OSV API error: {0}")]
    OsvError(String),

    #[error("Network error: {0}")]
    NetworkError(String),

    #[error("Cache error: {0}")]
    CacheError(String),

    #[error("Invalid vulnerability data: {0}")]
    InvalidData(String),

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Unknown error: {0}")]
    Unknown(String),
}
