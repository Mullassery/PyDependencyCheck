"""Tests for SBOM generation and signing."""

import json

import pytest

from pydependencycheck.sbom import SBOMGenerator, SBOMSigner


SAMPLE_DEPS = [
    {"name": "requests", "version": "2.32.0", "direct": True, "source": "requirements.txt"},
    {"name": "urllib3", "version": "2.0.0", "direct": False, "source": "requirements.txt"},
]


class TestSBOMGeneratorCycloneDx:
    def test_generates_valid_cyclonedx_structure(self):
        sbom = SBOMGenerator.generate_cyclonedx(SAMPLE_DEPS, project_name="myapp", project_version="1.0.0")

        assert sbom["bomFormat"] == "CycloneDX"
        assert sbom["specVersion"] == "1.4"
        assert sbom["metadata"]["component"]["name"] == "myapp"
        assert len(sbom["components"]) == 2

    def test_component_purl_and_scope(self):
        sbom = SBOMGenerator.generate_cyclonedx(SAMPLE_DEPS, project_name="myapp")
        by_name = {c["name"]: c for c in sbom["components"]}

        assert by_name["requests"]["purl"] == "pkg:pypi/requests@2.32.0"
        assert by_name["requests"]["scope"] == "required"
        assert by_name["urllib3"]["scope"] == "optional"

    def test_tool_version_matches_package_version(self):
        from pydependencycheck import __version__

        sbom = SBOMGenerator.generate_cyclonedx(SAMPLE_DEPS)
        assert sbom["metadata"]["tools"][0]["version"] == __version__

    def test_output_is_json_serializable(self):
        sbom = SBOMGenerator.generate_cyclonedx(SAMPLE_DEPS)
        json.dumps(sbom)  # must not raise


class TestSBOMGeneratorSPDX:
    def test_generates_valid_spdx_structure(self):
        sbom = SBOMGenerator.generate_spdx(SAMPLE_DEPS, project_name="myapp", project_version="1.0.0")

        assert sbom["spdxVersion"] == "SPDX-2.3"
        assert sbom["name"] == "myapp SBOM"
        # +1 for the project's own package entry
        assert len(sbom["packages"]) == len(SAMPLE_DEPS) + 1

    def test_relationships_describe_and_depend(self):
        sbom = SBOMGenerator.generate_spdx(SAMPLE_DEPS, project_name="myapp")
        rel_types = {r["relationshipType"] for r in sbom["relationships"]}
        assert "DESCRIBES" in rel_types
        assert "DEPENDS_ON" in rel_types


class TestIntegrityHash:
    def test_hash_is_deterministic(self):
        sbom = SBOMGenerator.generate_cyclonedx(SAMPLE_DEPS)
        h1 = SBOMGenerator.compute_integrity_hash(sbom)
        h2 = SBOMGenerator.compute_integrity_hash(sbom)
        assert h1 == h2
        assert len(h1) == 64  # sha256 hex digest

    def test_hash_changes_with_content(self):
        sbom_a = SBOMGenerator.generate_cyclonedx(SAMPLE_DEPS)
        sbom_b = SBOMGenerator.generate_cyclonedx(SAMPLE_DEPS[:1])
        assert SBOMGenerator.compute_integrity_hash(sbom_a) != SBOMGenerator.compute_integrity_hash(sbom_b)


@pytest.fixture
def rsa_keypair(tmp_path):
    cryptography = pytest.importorskip("cryptography")
    private_path = tmp_path / "key.pem"
    signer = SBOMSigner()
    signer.generate_keys(str(private_path))
    return str(private_path), str(tmp_path / "key.pub.pem")


class TestSBOMSigning:
    def test_sign_and_verify_round_trip(self, rsa_keypair):
        private_path, public_path = rsa_keypair
        sbom = SBOMGenerator.generate_cyclonedx(SAMPLE_DEPS)

        signer = SBOMSigner(private_key_path=private_path)
        signed = signer.sign_sbom(sbom)

        assert "signatures" in signed
        assert signed["signatures"][0]["method"] == "rsa-sha256"

        verifier = SBOMSigner()
        assert verifier.verify_sbom(signed, public_path) is True

    def test_verify_fails_on_tampered_sbom(self, rsa_keypair):
        private_path, public_path = rsa_keypair
        sbom = SBOMGenerator.generate_cyclonedx(SAMPLE_DEPS)

        signer = SBOMSigner(private_key_path=private_path)
        signed = signer.sign_sbom(sbom)

        # Tamper with a component after signing.
        signed["components"][0]["name"] = "malicious-package"

        verifier = SBOMSigner()
        assert verifier.verify_sbom(signed, public_path) is False

    def test_sign_without_key_returns_sbom_unmodified(self):
        sbom = SBOMGenerator.generate_cyclonedx(SAMPLE_DEPS)
        signer = SBOMSigner(private_key_path=None)
        result = signer.sign_sbom(sbom)
        assert "signatures" not in result

    def test_verify_without_signatures_returns_false(self, rsa_keypair):
        _, public_path = rsa_keypair
        sbom = SBOMGenerator.generate_cyclonedx(SAMPLE_DEPS)
        verifier = SBOMSigner()
        assert verifier.verify_sbom(sbom, public_path) is False
