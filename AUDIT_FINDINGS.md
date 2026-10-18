# Audit findings — 2026-10-19

This file records the repository-specific findings from the portfolio audit
conducted on 2026-10-19. It is documentation only; no code or release artifacts
were changed in this pass unless explicitly noted under "Implementation status".

Sources: the repository's own README/source/workflows, GitHub metadata and
Actions runs, PyPI metadata, and official competitor documentation. Claims are
marked as verified, inferred, or open questions. "Absent" means not found in the
inspected repository/docs, not proof that it cannot exist.

## What it is

Python dependency intelligence: provenance (`why`/`trace`), OSV scanning, unused-dependency detection, license checks, signed SBOMs, health scoring, and CI gating.

## Verified strengths

- OSV checks; AST unused detection; git provenance; license compatibility; RSA-signed CycloneDX/SPDX; health score; GitHub annotations; 12 test files; Security Audit workflow.
- Provenance and signed SBOM are genuinely differentiated.

## Verified gaps and user-facing risks

- Python-only; overlaps PyDeepMesh; exact-pin-only remediation; transitive scope varies; no reachability; no GitHub release.
- No multi-ecosystem story despite the sibling tool.

## Direct competitors

- pip-audit (PyPA), deptry (unused), Syft, Dependabot.

## Ranked next actions

- P1: merge into PyDeepMesh or publish a clear boundary (M).
- P2: SARIF + official GitHub Action (S).

## Do not build

- Duplicate multi-ecosystem scanning; PyDeepMesh owns it.

## Evidence gaps / validation needed

- No user validation; no SBOM interoperability test.

## Recommended disposition

Merge or narrow; do not maintain two overlapping scanners.

## Implementation status

No code changes in this pass.
