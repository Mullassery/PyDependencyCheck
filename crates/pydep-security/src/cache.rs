use crate::{SecurityError, SecurityResult};
use std::fs;
use std::path::PathBuf;
use std::time::{Duration, SystemTime};

const DEFAULT_TTL: Duration = Duration::from_secs(7 * 24 * 60 * 60);

/// Vulnerability cache management. Caches OSV query responses on disk,
/// keyed by ecosystem/package/version, so repeated scans don't re-hit
/// the network for packages that haven't changed.
pub struct VulnerabilityCache {
    cache_dir: PathBuf,
    ttl: Duration,
}

impl VulnerabilityCache {
    pub fn new() -> SecurityResult<Self> {
        let cache_dir = dirs::home_dir()
            .map(|home| home.join(".pydep"))
            .ok_or_else(|| {
                SecurityError::CacheError("could not resolve home directory".to_string())
            })?;
        fs::create_dir_all(&cache_dir).map_err(|e| {
            SecurityError::CacheError(format!("failed to create cache dir {:?}: {e}", cache_dir))
        })?;
        Ok(Self {
            cache_dir,
            ttl: DEFAULT_TTL,
        })
    }

    /// Get cache directory
    pub fn cache_dir(&self) -> &PathBuf {
        &self.cache_dir
    }

    fn entries_dir(&self) -> PathBuf {
        self.cache_dir.join("osv-cache")
    }

    fn entry_path(&self, ecosystem: &str, package: &str, version: Option<&str>) -> PathBuf {
        let key = match version {
            Some(v) => format!("{ecosystem}__{package}__{v}"),
            None => format!("{ecosystem}__{package}__any"),
        };
        // Filesystem-safe key: keep alphanumerics/./- and replace everything else with '_'
        let safe: String = key
            .chars()
            .map(|c| {
                if c.is_ascii_alphanumeric() || c == '.' || c == '-' {
                    c
                } else {
                    '_'
                }
            })
            .collect();
        self.entries_dir().join(format!("{safe}.json"))
    }

    /// Read a cached response if present and not older than the TTL.
    pub fn get(&self, ecosystem: &str, package: &str, version: Option<&str>) -> Option<String> {
        let path = self.entry_path(ecosystem, package, version);
        let metadata = fs::metadata(&path).ok()?;
        let modified = metadata.modified().ok()?;
        if SystemTime::now().duration_since(modified).ok()? > self.ttl {
            return None;
        }
        fs::read_to_string(&path).ok()
    }

    /// Write a response body to the cache.
    pub fn put(
        &self,
        ecosystem: &str,
        package: &str,
        version: Option<&str>,
        body: &str,
    ) -> SecurityResult<()> {
        let dir = self.entries_dir();
        fs::create_dir_all(&dir)
            .map_err(|e| SecurityError::CacheError(format!("failed to create {:?}: {e}", dir)))?;
        let path = self.entry_path(ecosystem, package, version);
        fs::write(&path, body).map_err(|e| {
            SecurityError::CacheError(format!("failed to write cache entry {:?}: {e}", path))
        })
    }

    /// Remove cached entries older than the TTL (default 7 days).
    pub fn cleanup_stale_cache(&self) -> SecurityResult<()> {
        let dir = self.entries_dir();
        if !dir.exists() {
            return Ok(());
        }
        let now = SystemTime::now();
        for entry in fs::read_dir(&dir)
            .map_err(|e| SecurityError::CacheError(format!("failed to read {:?}: {e}", dir)))?
        {
            let entry = match entry {
                Ok(e) => e,
                Err(_) => continue,
            };
            let path = entry.path();
            let is_stale = entry
                .metadata()
                .and_then(|m| m.modified())
                .map(|modified| now.duration_since(modified).unwrap_or_default() > self.ttl)
                .unwrap_or(false);
            if is_stale {
                let _ = fs::remove_file(&path);
            }
        }
        Ok(())
    }

    /// Get OSV snapshot path
    pub fn osv_snapshot_path(&self) -> PathBuf {
        self.cache_dir.join("osv-latest.db")
    }

    /// Get database path
    pub fn db_path(&self) -> PathBuf {
        self.cache_dir.join("cache.db")
    }
}

impl Default for VulnerabilityCache {
    fn default() -> Self {
        Self::new().unwrap_or_else(|_| Self {
            cache_dir: std::env::temp_dir().join(".pydep"),
            ttl: DEFAULT_TTL,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn put_then_get_returns_body() {
        let cache_dir = tempfile::tempdir().unwrap();
        let cache = VulnerabilityCache {
            cache_dir: cache_dir.path().to_path_buf(),
            ttl: DEFAULT_TTL,
        };
        cache
            .put("PyPI", "django", Some("3.2.0"), "{\"vulns\":[]}")
            .unwrap();
        let got = cache.get("PyPI", "django", Some("3.2.0"));
        assert_eq!(got.as_deref(), Some("{\"vulns\":[]}"));
    }

    #[test]
    fn get_returns_none_when_absent() {
        let cache_dir = tempfile::tempdir().unwrap();
        let cache = VulnerabilityCache {
            cache_dir: cache_dir.path().to_path_buf(),
            ttl: DEFAULT_TTL,
        };
        assert!(cache.get("PyPI", "nonexistent", None).is_none());
    }

    #[test]
    fn cleanup_removes_stale_entries_only() {
        let cache_dir = tempfile::tempdir().unwrap();
        let cache = VulnerabilityCache {
            cache_dir: cache_dir.path().to_path_buf(),
            ttl: Duration::from_secs(0), // everything is immediately stale
        };
        cache.put("PyPI", "django", Some("3.2.0"), "{}").unwrap();
        cache.cleanup_stale_cache().unwrap();
        assert!(cache.get("PyPI", "django", Some("3.2.0")).is_none());
        assert_eq!(fs::read_dir(cache.entries_dir()).unwrap().count(), 0);
    }
}
