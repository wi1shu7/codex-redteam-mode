from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .skill_card import SkillCard


@dataclass
class VerifyDecision:
    passed: bool
    pseudo_complete: bool
    reason_code: str


POSITIVE_COMPLETE_MARKERS = (
    "confirmed vulnerability",
    "task complete",
    "finished",
    "确认漏洞",
    "任务完成",
    "已完成",
)
NEGATING_MARKERS = (
    "not confirmed",
    "need more evidence",
    "未确认",
    "需要更多证据",
)


def verify_progress(
    *,
    objective: str,
    acceptance_checks: list[str],
    evidence_level: str,
    gate_ok: bool,
    assistant_summary: str,
    skill_card: "SkillCard | None" = None,
    evidence_artifacts: list | None = None,
    loop_iteration: int = 0,
) -> VerifyDecision:
    # Primary path: skill_card exit gate (scope-not-instruct pattern).
    # The AI must prove its work via evidence artifacts, not keyword claims.
    # Exception: if the orchestrator gate already passed (gate_ok=True),
    # the phase transition is authorized — skill_card yields.
    if skill_card is not None and not gate_ok:
        satisfied, gate_reason = skill_card.check_exit_gate(
            evidence_artifacts or [], loop_iteration
        )
        if satisfied:
            return VerifyDecision(passed=True, pseudo_complete=False, reason_code=gate_reason)
        summary = assistant_summary.casefold()
        pseudo_complete = (
            any(m in summary for m in POSITIVE_COMPLETE_MARKERS)
            and not any(m in summary for m in NEGATING_MARKERS)
        )
        return VerifyDecision(
            passed=False,
            pseudo_complete=pseudo_complete,
            reason_code=f"exit_gate_pending:{gate_reason}",
        )

    # Fallback: keyword + orchestrator-gate verification (no skill_card active).
    summary = assistant_summary.casefold()
    pseudo_complete = (
        any(marker in summary for marker in POSITIVE_COMPLETE_MARKERS)
        and not any(marker in summary for marker in NEGATING_MARKERS)
        and (evidence_level != "confirmed" and not gate_ok)
    )
    if gate_ok and evidence_level in {"partial", "confirmed"}:
        return VerifyDecision(passed=True, pseudo_complete=False, reason_code="verified")
    if pseudo_complete:
        return VerifyDecision(passed=False, pseudo_complete=True, reason_code="pseudo_complete")
    return VerifyDecision(passed=False, pseudo_complete=False, reason_code="missing_evidence")
