"""Recon workflow orchestration for bare-target intake.

Responsibilities:
- Define recon phase ordering (DNS → ports → subdomains → dirs → WAF → tech stack)
- Declare required capabilities per recon sub-phase
- Normalize recon artifact schemas for downstream consumption
- Provide a ReconProfile dataclass that holds aggregated recon results
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence


# ---------------------------------------------------------------------------
# Recon Phase Ordering
# ---------------------------------------------------------------------------

RECON_PHASE_ORDER: tuple[str, ...] = (
    "dns_resolve",
    "port_scan",
    "subdomain_enum",
    "directory_inventory",
    "waf_detect",
    "http_fingerprint",
    "tech_stack",
)

# Each recon sub-phase maps to its required capability and expected artifact
RECON_PHASE_SPEC: dict[str, dict[str, str]] = {
    "dns_resolve": {
        "capability": "dns_resolve",
        "expected_artifact": "dns_records",
        "description": "DNS A/AAAA/CNAME/MX/NS resolution",
    },
    "port_scan": {
        "capability": "port_scan",
        "expected_artifact": "port_scan_result",
        "description": "TCP/UDP port discovery and service detection",
    },
    "subdomain_enum": {
        "capability": "subdomain_enum",
        "expected_artifact": "subdomain_list",
        "description": "Subdomain enumeration via wordlist and DNS brute",
    },
    "directory_inventory": {
        "capability": "directory_inventory",
        "expected_artifact": "directory_list",
        "description": "Web directory and path discovery",
    },
    "waf_detect": {
        "capability": "waf_detect",
        "expected_artifact": "waf_fingerprint",
        "description": "WAF/CDN fingerprinting",
    },
    "http_fingerprint": {
        "capability": "http_fingerprint",
        "expected_artifact": "service_fingerprint",
        "description": "HTTP header analysis, server identification",
    },
    "tech_stack": {
        "capability": "tech_stack_detect",
        "expected_artifact": "tech_stack_profile",
        "description": "Technology stack detection (frameworks, CMS, libraries)",
    },
}


# ---------------------------------------------------------------------------
# Recon Capability List (for planner integration)
# ---------------------------------------------------------------------------

RECON_CAPABILITIES: tuple[str, ...] = tuple(
    spec["capability"] for spec in RECON_PHASE_SPEC.values()
)

# Minimum capabilities required for a valid recon profile
RECON_MIN_CAPABILITIES: tuple[str, ...] = (
    "dns_resolve",
    "port_scan",
    "http_fingerprint",
)

# Artifacts that constitute a complete recon profile (matches SKILL.md exit gate)
RECON_EXIT_ARTIFACTS: tuple[str, ...] = (
    "recon_profile",
    "port_scan_result",
    "service_fingerprint",
)


# ---------------------------------------------------------------------------
# Artifact Schema Normalization
# ---------------------------------------------------------------------------

@dataclass
class ReconArtifact:
    """Normalized recon artifact record."""
    artifact_type: str
    source_phase: str
    target: str
    data: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0  # 0.0 ~ 1.0
    raw_output: str = ""


@dataclass
class ReconProfile:
    """Aggregated recon profile for a target.

    This is the primary output of the recon-intake phase.
    Downstream decision_tree uses this to route to cve-lookup or attack paths.
    """
    target: str
    target_type: str = "domain"  # domain | ipv4 | ipv6 | url | cidr
    dns_records: dict[str, Any] = field(default_factory=dict)
    open_ports: list[int] = field(default_factory=list)
    services: dict[int, str] = field(default_factory=dict)  # port -> service_name
    subdomains: list[str] = field(default_factory=list)
    directories: list[str] = field(default_factory=list)
    waf: str = ""  # WAF product name or empty
    tech_stack: list[str] = field(default_factory=list)
    http_headers: dict[str, str] = field(default_factory=dict)
    server: str = ""
    tls_info: dict[str, Any] = field(default_factory=dict)
    artifacts: list[ReconArtifact] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Check if minimum recon data is present for downstream routing."""
        return bool(self.open_ports) and bool(self.services or self.server)

    @property
    def has_web_service(self) -> bool:
        """Check if target exposes HTTP/HTTPS."""
        web_ports = {80, 443, 8080, 8443, 8000, 3000, 5000}
        return bool(set(self.open_ports) & web_ports)

    @property
    def attack_surface_hints(self) -> list[str]:
        """Derive attack surface hints from recon data."""
        hints: list[str] = []
        if self.has_web_service:
            hints.append("web_application")
        if self.waf:
            hints.append(f"waf_present:{self.waf}")
        ssh_ports = {22, 2222}
        if set(self.open_ports) & ssh_ports:
            hints.append("ssh_exposed")
        db_ports = {3306, 5432, 1433, 27017, 6379}
        if set(self.open_ports) & db_ports:
            hints.append("database_exposed")
        if any("wordpress" in t.lower() for t in self.tech_stack):
            hints.append("wordpress")
        if any("api" in d.lower() for d in self.directories[:50]):
            hints.append("api_endpoints")
        return hints


def normalize_artifact(
    raw_data: Any,
    artifact_type: str,
    source_phase: str,
    target: str,
) -> ReconArtifact:
    """Normalize raw tool output into a ReconArtifact.

    Handles various tool output formats (dict, list, string).
    """
    if isinstance(raw_data, dict):
        data = raw_data
        raw_output = ""
    elif isinstance(raw_data, (list, tuple)):
        data = {"items": list(raw_data)}
        raw_output = ""
    elif isinstance(raw_data, str):
        data = {}
        raw_output = raw_data
    else:
        data = {"value": str(raw_data)}
        raw_output = str(raw_data)

    return ReconArtifact(
        artifact_type=artifact_type,
        source_phase=source_phase,
        target=target,
        data=data,
        raw_output=raw_output,
    )


def merge_into_profile(
    profile: ReconProfile,
    artifact: ReconArtifact,
) -> ReconProfile:
    """Merge a single recon artifact into the profile.

    Non-destructive: existing data is preserved, new data is appended/merged.
    """
    profile.artifacts.append(artifact)
    data = artifact.data

    if artifact.artifact_type == "dns_records":
        profile.dns_records.update(data)

    elif artifact.artifact_type == "port_scan_result":
        ports = data.get("ports") or data.get("open_ports") or data.get("items", [])
        if isinstance(ports, list):
            for p in ports:
                if isinstance(p, int):
                    if p not in profile.open_ports:
                        profile.open_ports.append(p)
                elif isinstance(p, dict):
                    port_num = p.get("port") or p.get("number")
                    if isinstance(port_num, int) and port_num not in profile.open_ports:
                        profile.open_ports.append(port_num)
                    svc = p.get("service") or p.get("name", "")
                    if port_num and svc:
                        profile.services[int(port_num)] = str(svc)

    elif artifact.artifact_type == "subdomain_list":
        subs = data.get("subdomains") or data.get("items", [])
        if isinstance(subs, list):
            for s in subs:
                if isinstance(s, str) and s not in profile.subdomains:
                    profile.subdomains.append(s)

    elif artifact.artifact_type == "directory_list":
        dirs = data.get("directories") or data.get("paths") or data.get("items", [])
        if isinstance(dirs, list):
            for d in dirs:
                if isinstance(d, str) and d not in profile.directories:
                    profile.directories.append(d)

    elif artifact.artifact_type == "waf_fingerprint":
        waf_name = data.get("waf") or data.get("product") or data.get("name", "")
        if waf_name:
            profile.waf = str(waf_name)

    elif artifact.artifact_type == "service_fingerprint":
        profile.server = data.get("server") or data.get("product", profile.server)
        headers = data.get("headers") or {}
        if isinstance(headers, dict):
            profile.http_headers.update(headers)
        tls = data.get("tls") or data.get("ssl", {})
        if isinstance(tls, dict):
            profile.tls_info.update(tls)

    elif artifact.artifact_type == "tech_stack_profile":
        techs = data.get("technologies") or data.get("stack") or data.get("items", [])
        if isinstance(techs, list):
            for t in techs:
                name = t if isinstance(t, str) else (t.get("name", "") if isinstance(t, dict) else str(t))
                if name and name not in profile.tech_stack:
                    profile.tech_stack.append(name)

    return profile


# ---------------------------------------------------------------------------
# Workflow Orchestration
# ---------------------------------------------------------------------------

def get_recon_plan(
    target: str,
    target_type: str = "domain",
    *,
    skip_phases: Sequence[str] = (),
) -> list[dict[str, str]]:
    """Generate ordered recon steps for a target.

    Returns list of {phase, capability, expected_artifact, description} dicts
    in recommended execution order.
    """
    plan: list[dict[str, str]] = []
    for phase_name in RECON_PHASE_ORDER:
        if phase_name in skip_phases:
            continue
        spec = RECON_PHASE_SPEC[phase_name]
        # Skip web-specific phases for non-web targets
        if target_type in ("ipv4", "ipv6", "cidr"):
            if phase_name in ("directory_inventory", "waf_detect", "tech_stack"):
                continue
        plan.append({
            "phase": phase_name,
            "capability": spec["capability"],
            "expected_artifact": spec["expected_artifact"],
            "description": spec["description"],
        })
    return plan


def get_required_capabilities(
    target_type: str = "domain",
    *,
    minimal: bool = False,
) -> tuple[str, ...]:
    """Get required capabilities for recon based on target type.

    Args:
        target_type: The type of target (domain, ipv4, ipv6, url, cidr)
        minimal: If True, return only minimum required capabilities
    """
    if minimal:
        return RECON_MIN_CAPABILITIES

    caps: list[str] = []
    for phase_name in RECON_PHASE_ORDER:
        if target_type in ("ipv4", "ipv6", "cidr"):
            if phase_name in ("directory_inventory", "waf_detect", "tech_stack"):
                continue
        caps.append(RECON_PHASE_SPEC[phase_name]["capability"])
    return tuple(caps)


def check_recon_exit(profile: ReconProfile) -> tuple[bool, str]:
    """Check if recon phase can exit based on collected artifacts.

    Mirrors the exit gate logic from redteam-recon-intake/SKILL.md:
    - Required: recon_profile, port_scan_result, service_fingerprint
    - min_attempts: 4
    """
    collected_types = {a.artifact_type for a in profile.artifacts}
    missing = [t for t in RECON_EXIT_ARTIFACTS if t not in collected_types]

    # Also accept if profile is_complete (has ports + services)
    if not missing or profile.is_complete:
        return True, "recon_profile_ready"

    return False, f"missing_artifacts:{','.join(missing)}"
