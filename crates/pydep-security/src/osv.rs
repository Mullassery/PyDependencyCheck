use crate::{Vulnerability, SecurityResult};

/// OSV Database client
pub struct OsvClient {
    // TODO: Store OSV snapshot path
}

impl OsvClient {
    pub fn new() -> Self {
        Self {}
    }

    /// Query vulnerabilities for a package
    pub async fn query_package(
        &self,
        _package: &str,
        _version: Option<&str>,
    ) -> SecurityResult<Vec<Vulnerability>> {
        // TODO: Implement OSV query
        Ok(Vec::new())
    }

    /// Check if OSV snapshot is available
    pub fn has_snapshot(&self) -> bool {
        // TODO: Check ~/.pydep/osv-latest.db
        false
    }

    /// Update OSV snapshot from api.osv.dev
    pub async fn update_snapshot(&self) -> SecurityResult<()> {
        // TODO: Download and cache OSV snapshot
        Ok(())
    }
}

impl Default for OsvClient {
    fn default() -> Self {
        Self::new()
    }
}
