"""CVE Lookup workflow orchestration.

Responsibilities:
- Define CVE lookup phase ordering (extract → search → filter → assess → patch check)
- Declare required capabilities per CVE sub-phase
- Normalize CVE artifact schemas for downstream consumption
- Provide CveLookupResult dataclass that holds aggregated CVE findings
- Check exit conditions to route to cve-validation, evidence-router, or recon-补证
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence


# ---------------------------------------------------------------------------
# CVE Phase Ordering
# ---------------------------------------------------------------------------

CVE_PHASE_ORDER: tuple[str, ...] = (
    "extract_products",
    "cve_search",
    "cve_filter",
    "applicability_assess",
    "patch_status_check",
)

# Each CVE sub-phase maps to its required capability and expected artifact
CVE_PHASE_SPEC: dict[str, dict[str, str]] = {
    "extract_products": {
        "capability": "code_generation",
        "expected_artifact": "product_version_list",
        "description": "Extract product/version/service list from recon_profile",
    },
    "cve_search": {
        "capability": "cve_lookup",
        "expected_artifact": "cve_candidate_list",
        "description": "Query CVE databases for known vulnerabilities matching products",
    },
    "cve_filter": {
        "capability": "code_generation",
        "expected_artifact": "cve_filtered_list",
        "description": "Filter CVE candidates by version range and relevance",
    },
    "applicability_assess": {
        "capability": "cve_applicability",
        "expected_artifact": "cve_applicability_matrix",
        "description": "Assess applicability of filtered CVEs to target environment",
    },
    "patch_status_check": {
        "capability": "patch_status_check",
        "expected_artifact": "cve_patch_status",
        "description": "Verify patch/fix status for applicable CVEs",
    },
}


# ---------------------------------------------------------------------------
# CVE Capability List (for planner integration)
# ---------------------------------------------------------------------------

CVE_CAPABILITIES: tuple[str, ...] = tuple(
    spec["capability"] for spec in CVE_PHASE_SPEC.values()
)

# Minimum capabilities required for a valid CVE lookup
CVE_MIN_CAPABILITIES: tuple[str, ...] = (
    "cve_lookup",
    "code_generation",
)

# Artifacts that constitute a complete CVE lookup (matches SKILL.md exit gate)
CVE_EXIT_ARTIFACTS: tuple[str, ...] = (
    "cve_candidate_list",
)

# Optional artifacts that strengthen the exit
CVE_OPTIONAL_ARTIFACTS: tuple[str, ...] = (
    "cve_applicability_matrix",
    "cve_patch_status",
)


# ---------------------------------------------------------------------------
# CVE Artifact Schema
# ---------------------------------------------------------------------------

@dataclass
class CveCandidate:
    """A single CVE candidate entry."""
    cve: str                    # CVE-YYYY-NNNN
    product: str                # Matched product name
    affected_versions: str      # Version range string
    source: str                 # NVD / MITRE / vendor advisory
    confidence: str             # low | medium | high
    reason: str                 # Why this CVE was selected
    cvss_score: float = 0.0    # CVSS base score if available
    cvss_vector: str = ""      # CVSS vector string


@dataclass
class CveApplicability:
    """Applicability assessment for a single CVE."""
    cve: str
    status: str                 # candidate | possibly_applicable | not_applicable | patched | unknown
    evidence: list[str] = field(default_factory=list)
    confidence: str = "low"     # low | medium | high


@dataclass
class CveLookupResult:
    """Aggregated CVE lookup result for a target.

    Primary output of the cve-lookup phase.
    Downstream decision_tree uses this to route to cve-validation or evidence-router.
    """
    target: str
    products: list[str] = field(default_factory=list)
    versions: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    fingerprints: list[str] = field(default_factory=list)
    candidates: list[CveCandidate] = field(default_factory=list)
    applicability: list[CveApplicability] = field(default_factory=list)
    next_candidates: list[str] = field(default_factory=list)  # CVEs needing further investigation

    @property
    def has_applicable(self) -> bool:
        """Check if any CVE is possibly applicable or candidate with medium+ confidence."""
        for item in self.applicability:
            if item.status in ("possibly_applicable", "candidate") and item.confidence in ("medium", "high"):
                return True
        # Also check candidates without applicability assessment
        if self.candidates and not self.applicability:
            return any(c.confidence in ("medium", "high") for c in self.candidates)
        return False

    @property
    def all_patched_or_na(self) -> bool:
        """Check if all assessed CVEs are patched or not applicable."""
        if not self.applicability:
            return False
        return all(
            item.status in ("not_applicable", "patched")
            for item in self.applicability
        )

    @property
    def insufficient_evidence(self) -> bool:
        """Check if we lack product/version info to make meaningful CVE queries."""
        return not self.products and not self.fingerprints

    @property
    def applicable_cves(self) -> list[str]:
        """Get list of CVE IDs that are possibly applicable."""
        result: list[str] = []
        for item in self.applicability:
            if item.status in ("possibly_applicable", "candidate") and item.confidence in ("medium", "high"):
                result.append(item.cve)
        return result


# ---------------------------------------------------------------------------
# Artifact Normalization
# ---------------------------------------------------------------------------

def normalize_cve_artifact(
    raw_data: Any,
    artifact_type: str,
    target: str,
) -> CveLookupResult | list[CveCandidate] | list[CveApplicability]:
    """Normalize raw CVE tool output into structured data.

    Handles various tool output formats from CVE MCP, NVD API, etc.
    """
    if artifact_type == "cve_candidate_list":
        return _parse_candidates(raw_data, target)
    elif artifact_type == "cve_applicability_matrix":
        return _parse_applicability(raw_data)
    elif artifact_type == "cve_patch_status":
        return _parse_applicability(raw_data)  # Same structure
    return CveLookupResult(target=target)


def _parse_candidates(raw_data: Any, target: str) -> list[CveCandidate]:
    """Parse raw CVE search results into CveCandidate list."""
    candidates: list[CveCandidate] = []

    if isinstance(raw_data, dict):
        items = raw_data.get("candidates") or raw_data.get("vulnerabilities") or raw_data.get("items", [])
    elif isinstance(raw_data, list):
        items = raw_data
    else:
        return candidates

    for item in items:
        if isinstance(item, dict):
            candidates.append(CveCandidate(
                cve=item.get("cve") or item.get("id") or item.get("cve_id", ""),
                product=item.get("product") or item.get("package", ""),
                affected_versions=item.get("affected_versions") or item.get("version_range", ""),
                source=item.get("source") or "unknown",
                confidence=item.get("confidence") or "low",
                reason=item.get("reason") or item.get("description", ""),
                cvss_score=float(item.get("cvss_score") or item.get("cvss", 0.0)),
                cvss_vector=item.get("cvss_vector") or "",
            ))
        elif isinstance(item, str) and item.startswith("CVE-"):
            candidates.append(CveCandidate(
                cve=item, product="", affected_versions="",
                source="unknown", confidence="low", reason="",
            ))

    return candidates


def _parse_applicability(raw_data: Any) -> list[CveApplicability]:
    """Parse raw applicability/patch status results."""
    results: list[CveApplicability] = []

    if isinstance(raw_data, dict):
        items = raw_data.get("applicability") or raw_data.get("results") or raw_data.get("items", [])
    elif isinstance(raw_data, list):
        items = raw_data
    else:
        return results

    for item in items:
        if isinstance(item, dict):
            results.append(CveApplicability(
                cve=item.get("cve") or item.get("id", ""),
                status=item.get("status") or "unknown",
                evidence=item.get("evidence") or [],
                confidence=item.get("confidence") or "low",
            ))

    return results


def merge_into_cve_result(
    result: CveLookupResult,
    artifact_type: str,
    raw_data: Any,
) -> CveLookupResult:
    """Merge a CVE artifact into the lookup result. Non-destructive."""
    if artifact_type == "product_version_list":
        if isinstance(raw_data, dict):
            result.products.extend(raw_data.get("products", []))
            result.versions.extend(raw_data.get("versions", []))
            result.services.extend(raw_data.get("services", []))
            result.fingerprints.extend(raw_data.get("fingerprints", []))

    elif artifact_type == "cve_candidate_list":
        candidates = _parse_candidates(raw_data, result.target)
        for c in candidates:
            if c.cve and c.cve not in [existing.cve for existing in result.candidates]:
                result.candidates.append(c)

    elif artifact_type in ("cve_applicability_matrix", "cve_patch_status"):
        assessments = _parse_applicability(raw_data)
        for a in assessments:
            existing_cves = [item.cve for item in result.applicability]
            if a.cve not in existing_cves:
                result.applicability.append(a)
            else:
                # Update existing entry if new assessment is more specific
                idx = existing_cves.index(a.cve)
                if a.status != "unknown":
                    result.applicability[idx] = a

    elif artifact_type == "cve_filtered_list":
        # Filtered list is just a refined candidate list
        candidates = _parse_candidates(raw_data, result.target)
        # Replace candidates with filtered set
        if candidates:
            result.candidates = candidates

    return result


# ---------------------------------------------------------------------------
# Workflow Orchestration
# ---------------------------------------------------------------------------

def get_cve_plan(
    target: str,
    *,
    has_products: bool = True,
    has_versions: bool = True,
    skip_phases: Sequence[str] = (),
) -> list[dict[str, str]]:
    """Generate ordered CVE lookup steps for a target.

    Returns list of {phase, capability, expected_artifact, description} dicts
    in recommended execution order.
    """
    plan: list[dict[str, str]] = []
    for phase_name in CVE_PHASE_ORDER:
        if phase_name in skip_phases:
            continue
        spec = CVE_PHASE_SPEC[phase_name]
        # Skip applicability/patch if no products identified
        if not has_products and phase_name in ("applicability_assess", "patch_status_check"):
            continue
        plan.append({
            "phase": phase_name,
            "capability": spec["capability"],
            "expected_artifact": spec["expected_artifact"],
            "description": spec["description"],
        })
    return plan


def get_cve_capabilities(*, minimal: bool = False) -> tuple[str, ...]:
    """Get required capabilities for CVE lookup.

    Args:
        minimal: If True, return only minimum required capabilities
    """
    if minimal:
        return CVE_MIN_CAPABILITIES
    return CVE_CAPABILITIES


def check_cve_exit(result: CveLookupResult) -> tuple[bool, str, str]:
    """Check if CVE lookup phase can exit and determine next routing.

    Returns:
        (can_exit, exit_reason, next_path)

    Mirrors the exit gate logic from redteam-cve-lookup/SKILL.md:
    - has_applicable → cve-validation
    - all_patched_or_na → evidence-based-router
    - insufficient_evidence → recon-intake (补证)
    - no candidates → evidence-based-router
    """
    # Case 1: insufficient evidence to even run queries
    if result.insufficient_evidence:
        return True, "insufficient_product_version_evidence", "recon-intake"

    # Case 2: no candidates found at all
    if not result.candidates:
        return True, "no_cve_candidates", "evidence-based-router"

    # Case 3: all assessed as patched or not applicable
    if result.all_patched_or_na:
        return True, "all_cve_patched_or_not_applicable", "evidence-based-router"

    # Case 4: has applicable CVEs → advance to validation
    if result.has_applicable:
        return True, "applicable_cve_found", "cve-validation"

    # Case 5: candidates exist but not yet assessed — need more work
    if result.candidates and not result.applicability:
        return False, "candidates_pending_assessment", ""

    # Default: still working
    return False, "assessment_in_progress", ""
