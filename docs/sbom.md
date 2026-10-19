# SBOM export and signing

PyDependencyCheck exports SBOMs for the declared dependency set. Supported
formats:

| Format | Command | Spec version |
|---|---|---|
| CycloneDX | `--format cyclonedx` | 1.4 |
| SPDX | `--format spdx` | 2.3 |

Every SBOM includes a SHA-256 integrity hash. With the `sbom` extra you can
also attach an RSA signature.

## Basic export

```bash
# CycloneDX JSON
pydependencycheck export --format cyclonedx --output sbom.cdx.json

# SPDX JSON
pydependencycheck export --format spdx --output sbom.spdx.json
```

Omit `--output` to write to stdout. Use `-p/--path` to select the project.

## Signing

Install the extra (provides `cryptography`):

```bash
pip install "pydependencycheck[sbom]"
```

Generate a key pair:

```bash
openssl genrsa -out sbom-key.pem 2048
openssl rsa -in sbom-key.pem -pubout -out sbom-key.pub.pem
```

Export a signed SBOM:

```bash
pydependencycheck export \
  --format cyclonedx \
  --sign \
  --key sbom-key.pem \
  --output sbom.signed.cdx.json
```

The output gains a top-level `signatures` array:

```json
{
  "signatures": [
    {
      "keyid": "pydependencycheck-signer",
      "method": "rsa-sha256",
      "sig": "<hex-encoded signature>"
    }
  ]
}
```

### What exactly is signed

The signature is **RSA-PSS with SHA-256** (MGF1-SHA256, maximum salt length)
over the compact, key-sorted JSON serialization of the SBOM **excluding** the
`signatures` field. The same serialization is used for the `integrityHash`.

### Verify a signature

There is no `verify` subcommand yet. Verify with the Python API:

```python
import json
from pydependencycheck.sbom import SBOMSigner

with open("sbom.signed.cdx.json", encoding="utf-8") as f:
    signed = json.load(f)

ok = SBOMSigner().verify_sbom(signed, "sbom-key.pub.pem")
print("verified" if ok else "INVALID")
```

## Integrity hash

`integrityHash` is the SHA-256 of the compact, key-sorted JSON of the SBOM
without signatures. It detects accidental modification but is not
authentication; use the signature when you need to prove origin.

## Limitations

- Signing covers the SBOM document, not the dependency contents.
- `--sign` requires `cryptography`; without it, signing is skipped with a
  warning. Always check that `signatures` exists in the output.
- SBOMs describe **declared** dependencies; transitive resolution depends on
  context. See [Limitations](limitations.md).
- VEX is a separate export; see [VEX](vex.md).
