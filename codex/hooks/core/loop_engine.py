from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from orchestrator.state_graph import next_allowed_phases
from redteam_state import RedTeamState


@dataclass
class LoopDecision:
    action: str
    reason: str
    next_stage: str
    next_step: str


def _first_allowed_stage(stage: str) -> str:
    allowed = next_allowed_phases(stage or "recon")
    return allowed[0] if allowed else (stage or "recon")


def _task_count(taskbook: Any) -> int:
    items = getattr(taskbook, "todo_items", None)
    if isinstance(taskbook, dict):
        items = taskbook.get("todo_items")
    return len(items) if isinstance(items, list) else 0


def decide_loop_action(
    *,
    state: RedTeamState,
    evidence_level: str,
    gate_ok: bool,
    verify_passed: bool,
    taskbook: Any,
    current_task_id: str,
) -> LoopDecision:
    """Decide the bounded autonomous loop action for the current turn.

    The loop is intentionally bounded: it does not run background work or issue
    tool calls. It advances, verifies, pivots, or blocks based on the current
    state and gate evidence so the next assistant turn has one explicit action.
    """

    stage = state.workflow_phase or "recon"
    path = state.selected_path or state.leaf_skill or state.router or state.phase or "selected path"

    if gate_ok and verify_passed:
        next_stage = _first_allowed_stage(stage)
        return LoopDecision(
            action="advance",
            reason="gate_ok",
            next_stage=next_stage,
            next_step=f"Advance from {stage} to {next_stage} and validate {path} with the next artifact.",
        )

    if state.pseudo_complete_count >= 2:
        return LoopDecision(
            action="blocked",
            reason="repeated_pseudo_complete",
            next_stage=stage,
            next_step="Stop claiming completion; collect concrete evidence before closing the task.",
        )

    if state.stagnation_count >= 3:
        return LoopDecision(
            action="pivot",
            reason="stagnation_threshold",
            next_stage=stage,
            next_step=f"Pivot from the current {path} path or choose a narrower validation step.",
        )

    if evidence_level in {"unknown", "partial"} and not gate_ok:
        return LoopDecision(
            action="verify",
            reason="missing_gate_evidence",
            next_stage=stage,
            next_step=f"Gather concrete evidence for {path} before advancing the {stage} gate.",
        )

    if _task_count(taskbook) == 0 and not current_task_id:
        return LoopDecision(
            action="blocked",
            reason="empty_taskbook",
            next_stage=stage,
            next_step="Create a taskbook item before continuing the loop.",
        )

    return LoopDecision(
        action="continue",
        reason="task_in_progress",
        next_stage=stage,
        next_step=f"Continue the current {path} task and attach evidence to the next turn.",
    )
