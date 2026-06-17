from __future__ import annotations

from dataclasses import dataclass

from redteam_state import RedTeamState


@dataclass
class IntentDecision:
    intent_type: str
    objective_delta: str = ""
    should_refresh_taskbook: bool = False
    should_verify_now: bool = False


VERIFY_MARKERS = (
    "verify",
    "\u9a8c\u8bc1",
    "\u786e\u8ba4\u6f0f\u6d1e",
    "\u786e\u8ba4\u662f\u5426",
    "\u662f\u4e0d\u662f\u6709\u6548",
    "\u662f\u5426\u6709\u6548",
    "confirm whether",
    "is this valid",
    "\u6709\u6548\u6f0f\u6d1e",
    "\u9700\u8981\u4ec0\u4e48\u8bc1\u636e",
)
REVISE_MARKERS = (
    "new objective",
    "\u65b0\u7684\u76ee\u6807",
    "\u65b0\u76ee\u6807",
    "\u53ea\u6d4b\u8bd5",
    "\u4ec5\u6d4b\u8bd5",
    "only test",
    "revise objective",
)
SUMMARY_MARKERS = ("summarize", "\u603b\u7ed3", "\u6c47\u603b", "\u62a5\u544a", "report")
CONTINUE_MARKERS = ("continue", "\u7ee7\u7eed", "keep digging", "same target", "\u540c\u4e00\u76ee\u6807")


COLON_CN = "\uff1a"
PERIOD_CN = "\u3002"
OBJECTIVE_CN = "\u76ee\u6807"
ONLY_TEST_MARKERS = ("\u53ea\u6d4b\u8bd5", "\u4ec5\u6d4b\u8bd5")


def _normalize(prompt: str) -> str:
    return prompt.strip()


def _looks_like_revise(prompt: str) -> bool:
    lowered = prompt.casefold()
    return any(marker in lowered for marker in REVISE_MARKERS) or COLON_CN in prompt or ":" in prompt


def _extract_revised_objective(prompt: str) -> str:
    text = prompt.strip().strip(PERIOD_CN)
    for marker in (
        "New objective:",
        "new objective:",
        "\u65b0\u7684\u76ee\u6807\uff1a",
        "\u65b0\u7684\u76ee\u6807:",
        "\u65b0\u76ee\u6807\uff1a",
        "\u65b0\u76ee\u6807:",
        "Only test ",
        "only test ",
    ):
        if text.startswith(marker):
            return text[len(marker):].strip().strip(PERIOD_CN)
    for marker in ONLY_TEST_MARKERS:
        if marker in text:
            idx = text.index(marker)
            return text[idx:].strip().strip(PERIOD_CN)
    if ":" in text:
        head, tail = text.split(":", 1)
        if "objective" in head.casefold():
            return tail.strip().strip(PERIOD_CN)
    if COLON_CN in text:
        head, tail = text.split(COLON_CN, 1)
        if OBJECTIVE_CN in head:
            return tail.strip().strip(PERIOD_CN)
    return text


def detect_intent(prompt: str, state: RedTeamState) -> IntentDecision:
    text = _normalize(prompt)
    lowered = text.casefold()

    if state.objective == "":
        return IntentDecision(
            intent_type="new",
            objective_delta=text,
            should_refresh_taskbook=True,
        )

    if any(marker in lowered for marker in SUMMARY_MARKERS):
        return IntentDecision(intent_type="summarize")

    if (
        any(marker in lowered for marker in VERIFY_MARKERS)
        and "confirm the callback path" not in lowered
        and "continue tracing" not in lowered
    ):
        return IntentDecision(intent_type="verify", should_verify_now=True)

    if _looks_like_revise(text) and text != state.objective:
        objective = _extract_revised_objective(text)
        if objective and objective != state.objective:
            return IntentDecision(
                intent_type="revise",
                objective_delta=objective,
                should_refresh_taskbook=True,
            )

    if any(marker in lowered for marker in CONTINUE_MARKERS):
        return IntentDecision(intent_type="continue")

    return IntentDecision(intent_type="continue")
