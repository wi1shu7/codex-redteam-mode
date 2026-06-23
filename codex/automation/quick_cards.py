from __future__ import annotations

from typing import Sequence


def should_refresh_quick_card(decision: object, *, loop_iteration: int) -> bool:
    action = getattr(decision, "action", "")
    reason = getattr(decision, "reason", "")
    return (
        action in {"pivot", "report", "blocked", "refresh_context"}
        or "stagnation" in reason
        or "pseudo_complete" in reason
        or (loop_iteration > 0 and loop_iteration % 5 == 0)
    )


def build_quick_card(
    *,
    objective: str,
    selected_path: str,
    decision: object,
    recent_artifacts: Sequence[str] = (),
) -> str:
    artifacts = ",".join(item for item in recent_artifacts if item) or "none"
    return "\n".join(
        [
            "[quick-card]",
            f"objective={objective or 'unset'}",
            f"path={selected_path or 'unset'}",
            f"trigger={getattr(decision, 'trigger', '') or 'unspecified'}",
            f"gate={getattr(decision, 'feedback_gate', '') or 'unspecified'}",
            f"exit={getattr(decision, 'exit_condition', '') or 'unspecified'}",
            f"artifacts={artifacts}",
            f"next={getattr(decision, 'next_step', '') or 'unset'}",
        ]
    )
