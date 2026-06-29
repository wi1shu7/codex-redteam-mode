"""Graded feedback gate engine.

Gate grades:
  pass       - can advance
  soft_fail  - evidence insufficient, but allowed to continue collecting
  pivot      - current path low-yield, suggest fuzzy pivot via SKILL.md hints
  blocked    - missing scope/target, unsafe, or cannot continue

Design principle: gates guide the model ("what evidence to collect next" or
"switch direction"), they do NOT hard-block unless safety requires it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


# ---------------------------------------------------------------------------
# Core result type
# ---------------------------------------------------------------------------

GATE_GRADES = ("pass", "soft_fail", "pivot", "blocked")


@dataclass(frozen=True)
class GateResult:
    """Result of a single gate evaluation."""

    gate_name: str
    grade: str  # one of GATE_GRADES
    missing: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    next_required_action: str = ""
    hint: str = ""

    @property
    def passed(self) -> bool:
        """Backward compat: treat pass as True, everything else as False."""
        return self.grade == "pass"

    @property
    def should_pivot(self) -> bool:
        return self.grade == "pivot"

    @property
    def is_blocked(self) -> bool:
        return self.grade == "blocked"


# ---------------------------------------------------------------------------
# Artifact Gate
# ---------------------------------------------------------------------------

def evaluate_artifact_gate(
    *,
    expected_artifacts: Sequence[str],
    available_artifacts: Sequence[str],
    stagnation_count: int = 0,
    phase: str = "",
) -> GateResult:
    """Graded artifact gate.

    Grading logic:
      pass      - all expected artifacts present (or phase minimum met)
      soft_fail - missing artifacts, first/second attempt
      pivot     - same artifacts missing repeatedly (stagnation >= 3)
      blocked   - no target/scope artifact and cannot continue
    """
    expected = tuple(dict.fromkeys(item for item in expected_artifacts if item))
    available = set(item for item in available_artifacts if item)
    missing = tuple(item for item in expected if item not in available)

    if not missing:
        return GateResult(
            gate_name="Artifact Gate",
            grade="pass",
            reasons=("all_expected_artifacts_present",),
            next_required_action="advance",
        )

    # Phase-aware minimum sufficiency
    if phase == "recon" and "target" in available and len(available) >= 2:
        return GateResult(
            gate_name="Artifact Gate",
            grade="pass",
            missing=missing,
            reasons=("recon_minimum_met",),
            next_required_action="advance",
            hint="target + at least one recon artifact present",
        )

    # Stagnation drives pivot
    if stagnation_count >= 3:
        return GateResult(
            gate_name="Artifact Gate",
            grade="pivot",
            missing=missing,
            reasons=("repeated_missing_artifact",),
            next_required_action="use_pivot_hints",
            hint="same artifacts missing across multiple iterations",
        )

    # No target/scope at all -> blocked
    critical = {"target", "scope"}
    if critical & set(missing) and not available:
        return GateResult(
            gate_name="Artifact Gate",
            grade="blocked",
            missing=missing,
            reasons=("no_target_or_scope",),
            next_required_action="request_target",
        )

    # Default: soft_fail - keep collecting
    return GateResult(
        gate_name="Artifact Gate",
        grade="soft_fail",
        missing=missing,
        reasons=("missing_artifacts_continue_collecting",),
        next_required_action="collect_required_artifact",
        hint=f"missing: {', '.join(missing)}",
    )


# ---------------------------------------------------------------------------
# Tool Gate
# ---------------------------------------------------------------------------

def evaluate_tool_gate(
    *,
    required_capabilities: Sequence[str],
    missing_capabilities: Sequence[str],
    has_equivalent: bool = False,
    plan_only_allowed: bool = True,
) -> GateResult:
    """Graded tool availability gate.

    Degradation chain:
      preferred MCP -> equivalent tool -> plan-only -> blocked

    Grading:
      pass      - preferred or equivalent available
      soft_fail - no tool but plan-only allowed
      blocked   - required external access impossible, no safe fallback
    """
    missing = tuple(dict.fromkeys(item for item in missing_capabilities if item))

    if not missing:
        return GateResult(
            gate_name="Tool Gate",
            grade="pass",
            reasons=("required_capabilities_available",),
            next_required_action="advance",
        )

    if has_equivalent:
        return GateResult(
            gate_name="Tool Gate",
            grade="pass",
            missing=missing,
            reasons=("equivalent_tool_available",),
            next_required_action="use_equivalent_tool",
            hint="preferred tool missing but equivalent found",
        )

    if plan_only_allowed:
        return GateResult(
            gate_name="Tool Gate",
            grade="soft_fail",
            missing=missing,
            reasons=("no_tool_plan_only",),
            next_required_action="plan_without_tool",
            hint="no tool available, proceeding in plan-only mode",
        )

    return GateResult(
        gate_name="Tool Gate",
        grade="blocked",
        missing=missing,
        reasons=("required_capability_impossible",),
        next_required_action="ask_user_for_capability",
    )


# ---------------------------------------------------------------------------
# Scope Gate (graded)
# ---------------------------------------------------------------------------

def evaluate_scope_gate(
    *,
    has_target: bool,
    has_scope: bool,
    is_in_scope: bool = True,
    is_plan_only: bool = False,
) -> GateResult:
    """Graded scope gate.

    Rules:
      Real execution: must have target + scope, in-scope check passes
      Plan-only: allow continuation with scope_missing note
      Cross-target / out-of-scope: always blocked
    """
    if not is_in_scope:
        return GateResult(
            gate_name="Scope Gate",
            grade="blocked",
            reasons=("out_of_scope_or_cross_target",),
            next_required_action="abort_action",
        )

    if has_target and has_scope:
        return GateResult(
            gate_name="Scope Gate",
            grade="pass",
            reasons=("target_and_scope_present",),
            next_required_action="advance",
        )

    # Plan-only mode: allow with warning
    if is_plan_only:
        missing_items = []
        if not has_target:
            missing_items.append("target")
        if not has_scope:
            missing_items.append("scope")
        return GateResult(
            gate_name="Scope Gate",
            grade="soft_fail",
            missing=tuple(missing_items),
            reasons=("plan_only_scope_missing",),
            next_required_action="continue_planning",
            hint="scope/target missing but plan-only mode allows continuation",
        )

    # Real execution without target/scope
    return GateResult(
        gate_name="Scope Gate",
        grade="blocked",
        missing=("target",) if not has_target else ("scope",),
        reasons=("missing_target_or_scope_for_execution",),
        next_required_action="request_scope",
    )


# ---------------------------------------------------------------------------
# Rhythm Gate (stagnation detection)
# ---------------------------------------------------------------------------

def evaluate_rhythm_gate(
    *,
    stagnation_count: int,
    pivot_hints: Sequence[str] = (),
) -> GateResult:
    """Rhythm gate: drives pace adjustment based on stagnation.

    Rules:
      stagnation 0-2: pass (continue)
      stagnation 3-4: pivot (suggest direction change)
      stagnation >=5: blocked (ask user or stop)
    """
    if stagnation_count <= 2:
        return GateResult(
            gate_name="Rhythm Gate",
            grade="pass",
            reasons=("rhythm_healthy",),
            next_required_action="continue",
        )

    if stagnation_count <= 4:
        hint = ""
        if pivot_hints:
            hint = f"pivot suggestions: {'; '.join(pivot_hints[:3])}"
        return GateResult(
            gate_name="Rhythm Gate",
            grade="pivot",
            reasons=("stagnation_detected",),
            next_required_action="use_pivot_hints",
            hint=hint,
        )

    return GateResult(
        gate_name="Rhythm Gate",
        grade="blocked",
        reasons=("excessive_stagnation",),
        next_required_action="ask_user_or_stop",
        hint=f"stagnation count: {stagnation_count}, no progress detected",
    )


# ---------------------------------------------------------------------------
# Aggregate: evaluate all gates and return worst grade
# ---------------------------------------------------------------------------

def aggregate_gates(*results: GateResult) -> GateResult:
    """Aggregate multiple gate results into a single worst-grade result.

    Priority: blocked > pivot > soft_fail > pass
    """
    if not results:
        return GateResult(gate_name="Aggregate", grade="pass")

    grade_priority = {"blocked": 3, "pivot": 2, "soft_fail": 1, "pass": 0}
    worst = results[0]
    worst_priority = grade_priority.get(worst.grade, 0)

    for r in results[1:]:
        r_priority = grade_priority.get(r.grade, 0)
        if r_priority > worst_priority:
            worst = r
            worst_priority = r_priority

    all_missing: list[str] = []
    all_reasons: list[str] = []
    all_hints: list[str] = []

    for r in results:
        all_missing.extend(r.missing)
        all_reasons.extend(r.reasons)
        if r.hint:
            all_hints.append(f"[{r.gate_name}] {r.hint}")

    return GateResult(
        gate_name="Aggregate",
        grade=worst.grade,
        missing=tuple(dict.fromkeys(all_missing)),
        reasons=tuple(all_reasons),
        next_required_action=worst.next_required_action,
        hint=" | ".join(all_hints) if all_hints else "",
    )
