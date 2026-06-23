from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    missing: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    next_required_action: str = ""
    exit_signal: str = ""


def evaluate_artifact_gate(
    *,
    expected_artifacts: Sequence[str],
    available_artifacts: Sequence[str],
) -> GateResult:
    expected = tuple(dict.fromkeys(item for item in expected_artifacts if item))
    available = set(item for item in available_artifacts if item)
    missing = tuple(item for item in expected if item not in available)
    if missing:
        return GateResult(
            gate_name="Artifact Gate",
            passed=False,
            missing=missing,
            reasons=("expected_artifact_missing",),
            next_required_action="collect_required_artifact",
            exit_signal="verify",
        )
    return GateResult(
        gate_name="Artifact Gate",
        passed=True,
        reasons=("expected_artifact_present",),
        next_required_action="advance",
        exit_signal="advance",
    )


def evaluate_tool_gate(
    *,
    required_capabilities: Sequence[str],
    missing_capabilities: Sequence[str],
) -> GateResult:
    missing = tuple(dict.fromkeys(item for item in missing_capabilities if item))
    if missing:
        return GateResult(
            gate_name="Tool Availability Gate",
            passed=False,
            missing=missing,
            reasons=("required_capability_missing",),
            next_required_action="select_equivalent_tool_or_block",
            exit_signal="blocked",
        )
    return GateResult(
        gate_name="Tool Availability Gate",
        passed=True,
        reasons=("required_capabilities_available",),
        next_required_action="preflight_scope",
        exit_signal="continue",
    )
