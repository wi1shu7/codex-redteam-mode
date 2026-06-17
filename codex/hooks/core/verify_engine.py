from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VerifyDecision:
    passed: bool
    pseudo_complete: bool
    reason_code: str


POSITIVE_COMPLETE_MARKERS = (
    "confirmed vulnerability",
    "task complete",
    "finished",
    "\u786e\u8ba4\u6f0f\u6d1e",
    "\u4efb\u52a1\u5b8c\u6210",
    "\u5df2\u5b8c\u6210",
)
NEGATING_MARKERS = (
    "not confirmed",
    "need more evidence",
    "\u672a\u786e\u8ba4",
    "\u9700\u8981\u66f4\u591a\u8bc1\u636e",
)


def verify_progress(
    *,
    objective: str,
    acceptance_checks: list[str],
    evidence_level: str,
    gate_ok: bool,
    assistant_summary: str,
) -> VerifyDecision:
    summary = assistant_summary.casefold()
    pseudo_complete = (
        any(marker in summary for marker in POSITIVE_COMPLETE_MARKERS)
        and not any(marker in summary for marker in NEGATING_MARKERS)
        and (evidence_level != "confirmed" or not gate_ok)
    )
    if gate_ok and evidence_level in {"partial", "confirmed"}:
        return VerifyDecision(passed=True, pseudo_complete=False, reason_code="verified")
    if pseudo_complete:
        return VerifyDecision(passed=False, pseudo_complete=True, reason_code="pseudo_complete")
    return VerifyDecision(passed=False, pseudo_complete=False, reason_code="missing_evidence")
