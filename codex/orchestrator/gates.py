from __future__ import annotations

from dataclasses import dataclass, field

from .task_schema import ExploitArtifact, ReconArtifact, ReviewArtifact, StrategyArtifact


@dataclass
class GateDecision:
    ok: bool
    reasons: list[str] = field(default_factory=list)


def recon_gate(artifact: ReconArtifact) -> GateDecision:
    reasons: list[str] = []
    if not artifact.hosts:
        reasons.append("missing hosts")
    if not artifact.ports and not artifact.services:
        reasons.append("missing ports/services")
    if not artifact.evidence_refs:
        reasons.append("missing evidence references")
    return GateDecision(ok=not reasons, reasons=reasons)


def strategy_gate(artifact: StrategyArtifact) -> GateDecision:
    reasons: list[str] = []
    if not artifact.candidate_paths:
        reasons.append("no candidate paths")
    if not artifact.chosen_path:
        reasons.append("no chosen path")
    if not artifact.evidence_refs:
        reasons.append("missing strategy evidence references")
    return GateDecision(ok=not reasons, reasons=reasons)


def exploit_gate(artifact: ExploitArtifact) -> GateDecision:
    reasons: list[str] = []
    if not artifact.path_name:
        reasons.append("missing path name")
    if not artifact.target_constraints:
        reasons.append("missing target constraints")
    if not artifact.success_conditions:
        reasons.append("missing success conditions")
    return GateDecision(ok=not reasons, reasons=reasons)


def review_gate(artifact: ReviewArtifact) -> GateDecision:
    reasons: list[str] = []
    if artifact.status not in {"pass", "revise", "reject"}:
        reasons.append("invalid review status")
    if artifact.status != "pass":
        reasons.append("review not passed")
    else:
        # status == "pass": only fail on critical-severity issues
        critical_syntax = [i for i in artifact.syntax_issues if isinstance(i, dict) and i.get("severity") == "critical"] if isinstance(artifact.syntax_issues, list) else []
        critical_logic = [i for i in artifact.logic_issues if isinstance(i, dict) and i.get("severity") == "critical"] if isinstance(artifact.logic_issues, list) else []
        critical_opsec = [i for i in artifact.opsec_issues if isinstance(i, dict) and i.get("severity") == "critical"] if isinstance(artifact.opsec_issues, list) else []
        if critical_syntax:
            reasons.append("critical syntax issues present")
        if critical_logic:
            reasons.append("critical logic issues present")
        if critical_opsec:
            reasons.append("critical opsec issues present")
    return GateDecision(ok=not reasons, reasons=reasons)


def postex_gate(current_phase: str, foothold_present: bool) -> GateDecision:
    reasons: list[str] = []
    if current_phase not in {"postex", "ad", "payload", "reverse", "web"}:
        reasons.append("phase not suitable for postex planning")
    if not foothold_present:
        reasons.append("no foothold present")
    return GateDecision(ok=not reasons, reasons=reasons)
