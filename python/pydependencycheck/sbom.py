"""SBOM (Software Bill of Materials) generation and signing"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from . import __version__

logger = logging.getLogger(__name__)

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


class SBOMGenerator:
    """Generate Software Bill of Materials in multiple formats"""

    @staticmethod
    def generate_cyclonedx(
        dependencies: List[Dict[str, Any]],
        project_name: str = "Unknown",
        project_version: str = "0.0.0",
    ) -> Dict[str, Any]:
        """Generate CycloneDX 1.4 SBOM"""
        components = []

        for dep in dependencies:
            component = {
                "type": "library",
                "bom-ref": f"pkg:pypi/{dep['name']}@{dep.get('version', 'unknown')}",
                "name": dep["name"],
                "version": dep.get("version") or "unknown",
                "purl": f"pkg:pypi/{dep['name']}@{dep.get('version', 'unknown')}",
                "scope": "required" if dep.get("direct") else "optional",
            }

            # Add evidence of usage
            if dep.get("source"):
                component["evidence"] = {
                    "identity": {"field": "purl", "confidence": 100, "methods": [{"technique": "manifest"}]}
                }

            components.append(component)

        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "serialNumber": f"urn:uuid:pydep-{datetime.now().isoformat()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "tools": [
                    {
                        "vendor": "PyDependencyCheck",
                        "name": "pydependencycheck",
                        "version": __version__,
                    }
                ],
                "component": {
                    "type": "application",
                    "name": project_name,
                    "version": project_version,
                },
            },
            "components": components,
        }

        return sbom

    @staticmethod
    def generate_spdx(
        dependencies: List[Dict[str, Any]],
        project_name: str = "Unknown",
        project_version: str = "0.0.0",
    ) -> Dict[str, Any]:
        """Generate SPDX JSON SBOM"""
        packages = []
        relationships = []
        document_id = "SPDXRef-DOCUMENT"
        project_id = f"SPDXRef-{project_name.replace(' ', '-')}"

        for i, dep in enumerate(dependencies):
            pkg_id = f"SPDXRef-Package-{i}"

            package = {
                "SPDXID": pkg_id,
                "name": dep["name"],
                "versionInfo": dep.get("version") or "NOASSERTION",
                "downloadLocation": f"https://pypi.org/project/{dep['name']}/",
                "filesAnalyzed": False,
                "supplier": "Organization: PyPI (https://pypi.org)",
            }

            packages.append(package)

            # Add relationship
            rel_type = "DEPENDS_ON"
            relationships.append(
                {
                    "spdxElementId": project_id,
                    "relatedSpdxElement": pkg_id,
                    "relationshipType": rel_type,
                }
            )

        sbom = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": document_id,
            "name": f"{project_name} SBOM",
            "documentNamespace": f"https://pydependencycheck.io/sbom/{project_name}/{datetime.now().isoformat()}",
            "creationInfo": {
                "created": datetime.now().isoformat(),
                "creators": [f"Tool: pydependencycheck-{__version__}"],
                "licenseListVersion": "3.19",
            },
            "packages": [
                {
                    "SPDXID": project_id,
                    "name": project_name,
                    "versionInfo": project_version,
                    "downloadLocation": "NOASSERTION",
                    "filesAnalyzed": False,
                }
            ]
            + packages,
            "relationships": [
                {
                    "spdxElementId": document_id,
                    "relatedSpdxElement": project_id,
                    "relationshipType": "DESCRIBES",
                }
            ]
            + relationships,
        }

        return sbom

    @staticmethod
    def compute_integrity_hash(sbom: Dict[str, Any]) -> str:
        """Compute SHA256 hash of SBOM for integrity verification"""
        sbom_str = json.dumps(sbom, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(sbom_str.encode()).hexdigest()


class SBOMSigner:
    """Sign and verify SBOMs with cryptographic signatures"""

    def __init__(self, private_key_path: Optional[str] = None):
        self.private_key_path = private_key_path
        self.private_key = None
        self.public_key = None

        if private_key_path and HAS_CRYPTO:
            self._load_keys()

    def _load_keys(self) -> None:
        """Load RSA keys from file"""
        if not self.private_key_path:
            return

        try:
            with open(self.private_key_path, "rb") as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                )
            # Derive public key
            self.public_key = self.private_key.public_key()
            logger.info(f"Loaded RSA keys from {self.private_key_path}")
        except Exception as e:
            logger.error(f"Failed to load keys: {e}")

    def generate_keys(self, output_path: str) -> None:
        """Generate new RSA key pair"""
        if not HAS_CRYPTO:
            logger.error("cryptography library not installed. Install with: pip install cryptography")
            return

        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )

            # Save private key
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )

            with open(output_path, "wb") as f:
                f.write(private_pem)

            # Save public key
            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            public_path = output_path.replace(".pem", ".pub.pem")
            with open(public_path, "wb") as f:
                f.write(public_pem)

            logger.info(f"Generated RSA keys: {output_path}, {public_path}")
        except Exception as e:
            logger.error(f"Failed to generate keys: {e}")

    def sign_sbom(self, sbom: Dict[str, Any]) -> Dict[str, Any]:
        """Sign an SBOM and return it with signature"""
        if not self.private_key or not HAS_CRYPTO:
            logger.warning("Private key not available for signing")
            return sbom

        try:
            sbom_json = json.dumps(sbom, sort_keys=True, separators=(",", ":"))
            sbom_bytes = sbom_json.encode()

            signature = self.private_key.sign(
                sbom_bytes,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )

            signed_sbom = sbom.copy()
            signed_sbom["signatures"] = [
                {
                    "keyid": "pydependencycheck-signer",
                    "method": "rsa-sha256",
                    "sig": signature.hex(),
                }
            ]

            return signed_sbom
        except Exception as e:
            logger.error(f"Failed to sign SBOM: {e}")
            return sbom

    def verify_sbom(self, signed_sbom: Dict[str, Any], public_key_path: str) -> bool:
        """Verify SBOM signature"""
        if not HAS_CRYPTO:
            logger.warning("cryptography library not available")
            return False

        try:
            if "signatures" not in signed_sbom:
                logger.warning("SBOM has no signatures")
                return False

            # Load public key
            with open(public_key_path, "rb") as f:
                public_key = serialization.load_pem_public_key(f.read())

            # Remove signature from copy for verification
            sbom_copy = signed_sbom.copy()
            signature_data = sbom_copy.pop("signatures")[0]

            sbom_json = json.dumps(sbom_copy, sort_keys=True, separators=(",", ":"))
            sbom_bytes = sbom_json.encode()

            signature = bytes.fromhex(signature_data["sig"])

            public_key.verify(
                signature,
                sbom_bytes,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )

            logger.info("SBOM signature verified successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to verify SBOM: {e}")
            return False
