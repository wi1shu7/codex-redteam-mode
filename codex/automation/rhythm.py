from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RhythmDecision:
    state: str
    drift_score: float
    reason: str


def classify_rhythm(
    *,
    stagnation_count: int = 0,
    tool_failure_count: int = 0,
    pseudo_complete_count: int = 0,
    loop_iteration: int = 0,
) -> RhythmDecision:
    if pseudo_complete_count >= 2:
        return RhythmDecision("pseudo_complete", 0.85, "completion_claim_without_evidence")
    if tool_failure_count >= 2:
        return RhythmDecision("tool_blocked", 0.7, "repeated_tool_failure")
    if stagnation_count >= 3:
        return RhythmDecision("stagnant", 0.75, "repeated_same_path")
    if stagnation_count or (loop_iteration and loop_iteration % 5 == 0):
        return RhythmDecision("drifting", 0.35, "periodic_or_minor_drift")
    return RhythmDecision("healthy", 0.0, "normal_operation")
