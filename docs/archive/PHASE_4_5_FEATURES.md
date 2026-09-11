# Phase 4-5: Drift Tracking & Enterprise Features

## Phase 4: Drift Tracking & Historical Snapshots

### Snapshot Management
```bash
# Save current scan as baseline
pydependencycheck snapshot --save

# View latest snapshot
pydependencycheck snapshot

# Show dependency history over N days
pydependencycheck history --days 30

# Detect drift since baseline
pydependencycheck drift --baseline main
```

### Drift Detection
- Automatically detects added/removed packages
- Tracks version upgrades and downgrades
- Compares against stored baseline
- Graph hashing for integrity verification
- Historical timeline with trends

### Storage Features
- SQLite database at `~/.pydep/cache.db`
- Automatic snapshot cleanup (keeps 30 most recent)
- 7-day cache TTL for vulnerability data
- Baseline management (named snapshots)
- Git-like commit timestamps and metadata

---

## Phase 5: Enterprise Observability & Supply Chain Security

### 1. CLI Dashboard (No Web Server)

#### Real-time Monitoring
```bash
# Show summary dashboard
pydependencycheck scan . --format table

# Show detailed health breakdown
pydependencycheck health

# Timeline view of changes
pydependencycheck history --days 90

# Live monitoring mode (continuous)
pydependencycheck monitor
```

#### Dashboard Features
- **Summary Stats**: Total, direct, transitive dependencies
- **Health Score**: Multi-factor assessment (0-100)
- **Drift Timeline**: Historical trends with visual bars
- **Health Breakdown**: 
  - Vulnerabilities (40% weight)
  - Maintenance (30% weight)
  - Quality/Dead Deps (20% weight)
  - Complexity (10% weight)
- **Recommendations**: Actionable guidance
- **Issues Detected**: Problems requiring attention
- Rich terminal output with colors and emoji

### 2. OpenTelemetry Instrumentation

#### Setup
```python
from pydependencycheck.telemetry import TelemetryConfig, init_telemetry

# Initialize OTEL
config = TelemetryConfig(
    enabled=True,
    exporter="jaeger",  # or "otlp", "prometheus"
    jaeger_host="localhost",
    jaeger_port=6831,
)
init_telemetry(config)
```

#### Supported Backends
- **Jaeger**: Distributed tracing (trace visualization)
- **OTLP**: OpenTelemetry Protocol (standard approach)
- **Prometheus**: Metrics scraping
- **stdout**: Debug/development mode

#### Instrumented Operations
```
scan_dependencies (span)
├─ project_path
├─ timestamp
└─ status

git_blame (span)
├─ package
└─ status

scan_vulnerabilities (span)
├─ package
└─ status
```

#### Metrics Emitted
- `pydep_total_dependencies` (counter)
- `pydep_direct_dependencies` (counter)
- `pydep_health_score` (gauge, 0-100)
- `pydep_vulnerabilities_critical/high/medium/low` (counters)
- `pydep_operation_duration_ms` (histogram)

### 3. SBOM Generation & Signing

#### Generate SBOM
```bash
# CycloneDX 1.4 format
pydependencycheck export --format cyclonedx --output sbom.json

# SPDX JSON format
pydependencycheck export --format spdx --output sbom.spdx.json
```

#### Sign SBOM (Optional)
```python
from pydependencycheck.sbom import SBOMSigner, SBOMGenerator

# Generate keys
signer = SBOMSigner()
signer.generate_keys("private.pem")

# Sign SBOM
sbom = SBOMGenerator.generate_cyclonedx(deps)
signed_sbom = signer.sign_sbom(sbom)

# Verify signature
is_valid = signer.verify_sbom(signed_sbom, "private.pub.pem")
```

#### SBOM Features
- **CycloneDX**: Industry standard format (NTIA recommended)
- **SPDX**: Alternative format for compliance
- **Component PURL**: Package URLs for consumption
- **Integrity Hash**: SHA256 verification
- **RSA Signing**: Cryptographic authentication
- **Supply Chain**: Full dependency tree with evidence

### 4. GitHub Actions Integration

#### Workflow Template
```yaml
name: Dependency Check

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 9 * * MON'  # Weekly

jobs:
  dependency-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - run: pip install pydependencycheck
      
      - run: pydependencycheck scan . --save-snapshot
      - run: pydependencycheck health
      - run: pydependencycheck drift --baseline main
      - run: pydependencycheck export --format cyclonedx
      
      - uses: actions/upload-artifact@v3
        with:
          name: sbom
          path: sbom.json
```

#### CI/CD Features
- **Annotations**: Warnings/errors in workflow output
- **Vulnerability Reporting**: Critical/High severity alerts
- **Health Checks**: Pass/fail on score threshold
- **Drift Detection**: Alert on dependency changes
- **SBOM Upload**: Artifact storage for compliance
- **Failure Criteria**:
  - Critical vulnerabilities → ERROR
  - Health score < 50 → ERROR
  - Dead deps > threshold → ERROR

---

## New Dependencies (Optional)

### OTEL Support
```bash
pip install "pydependencycheck[otel]"
```

Includes:
- opentelemetry-api
- opentelemetry-sdk
- opentelemetry-exporter-jaeger
- opentelemetry-exporter-otlp
- opentelemetry-exporter-prometheus

### SBOM Signing
```bash
pip install "pydependencycheck[sbom]"
```

Includes:
- cryptography (RSA signing/verification)

### All Enterprise Features
```bash
pip install "pydependencycheck[otel,sbom]"
```

---

## Configuration Examples

### Jaeger Tracing (Local Development)
```bash
# Start Jaeger container
docker run -d --name jaeger \
  -p 6831:6831/udp \
  -p 16686:16686 \
  jaegertracing/all-in-one

# Use with PyDependencyCheck
export PYDEP_TELEMETRY=jaeger
pydependencycheck scan .

# View traces at http://localhost:16686
```

### Prometheus Metrics
```bash
# Configure to emit Prometheus metrics
export PYDEP_TELEMETRY=prometheus

pydependencycheck scan .

# Scrape metrics from endpoint
# curl http://localhost:9090/metrics
```

### OTLP (Production)
```bash
# Use OTEL Collector
export PYDEP_TELEMETRY=otlp
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

pydependencycheck scan .
```

---

## Workflows

### Continuous Drift Monitoring
```bash
# 1. Set baseline
pydependencycheck snapshot --save

# 2. Run weekly scans (via cron or GitHub Actions)
pydependencycheck scan . --save-snapshot

# 3. Compare to baseline
pydependencycheck drift --baseline main

# 4. Alert on changes
if [ $? -eq 0 ]; then
  echo "No drift"
else
  echo "Drift detected - review changes"
fi
```

### Supply Chain Security
```bash
# 1. Generate SBOM for compliance
pydependencycheck export --format cyclonedx --output sbom.json

# 2. Sign for authenticity
pydependencycheck sbom --sign --key private.pem

# 3. Upload to artifact store
# gsutil cp sbom.json gs://my-sbom-bucket/

# 4. Verify in downstream
pydependencycheck sbom --verify sbom.json --key public.pem
```

### Health-Gated Deployments
```bash
# In CI/CD pipeline
HEALTH=$(pydependencycheck health --json)
SCORE=$(echo $HEALTH | jq '.score')

if [ $SCORE -lt 50 ]; then
  echo "Health score too low: $SCORE/100"
  exit 1
fi

echo "Dependencies healthy: $SCORE/100"
```

---

## API Usage

### Recording Metrics
```python
from pydependencycheck.telemetry import get_telemetry

telemetry = get_telemetry()

# Record scan
telemetry.record_scan_metric(
    total_deps=45,
    direct_deps=12,
    health_score=78
)

# Record vulnerabilities
telemetry.record_vulnerability_metric(
    critical=0,
    high=2,
    medium=5,
    low=3
)

# Record performance
telemetry.record_performance_metric("scan", 1234.5)  # milliseconds
```

### Tracing Operations
```python
telemetry = get_telemetry()

# Trace custom operation
with telemetry.trace_scan("/path/to/project") as span:
    # Do work here
    scan_result = scanner.scan()
    span.set_attribute("dependency_count", len(scan_result.dependencies))

# Span automatically ends and is exported
```

---

## Compliance Features

 **SBOM Support**: CycloneDX + SPDX compliance  
 **Cryptographic Signing**: RSA-SHA256 authentication  
 **Audit Trail**: Git-style blame for every dependency  
 **Drift Detection**: Track changes over time  
 **Observability**: OTEL instrumentation  
 **CI/CD Integration**: GitHub Actions ready  
 **Health Scoring**: Quantified risk assessment  
 **Vulnerability Tracking**: OSV integration  
 **License Compliance**: SPDX classification  

---

## Summary

PyDependencyCheck is now **production-ready** with:
-  All 5 phases implemented
-  Enterprise security features
-  Compliance tooling (SBOM, signing)
-  Observability (OTEL)
-  CI/CD integration (GitHub Actions)
-  CLI-only (no web dependencies)
-  21+ Rust tests passing
