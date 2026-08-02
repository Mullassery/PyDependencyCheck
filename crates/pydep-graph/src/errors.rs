use thiserror::Error;

pub type GraphResult<T> = Result<T, GraphError>;

#[derive(Error, Debug)]
pub enum GraphError {
    #[error("Cycle detected in dependency graph")]
    CycleDetected,

    #[error("Node not found: {0}")]
    NodeNotFound(String),

    #[error("Invalid dependency: {0}")]
    InvalidDependency(String),

    #[error("Graph construction failed: {0}")]
    ConstructionFailed(String),

    #[error("Serialization error: {0}")]
    SerializationError(String),

    #[error("Analysis error: {0}")]
    AnalysisError(String),

    #[error("Unknown error: {0}")]
    Unknown(String),
}
