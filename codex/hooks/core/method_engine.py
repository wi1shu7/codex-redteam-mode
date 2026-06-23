from __future__ import annotations
import re
from router.mappings import PHASE_DEFAULT_METHOD, PHASE_ESCALATION_METHOD

METHOD_HINTS = [
    ("workflows", [r"\bworkflow\b", r"\bplaybook\b", r"\bchain\b", "\u5de5\u4f5c\u6d41", "\u6d41\u7a0b", "\u591a\u9636\u6bb5"]),
    ("overall-planning", [r"\bplan\b", r"\broadmap\b", "\u8def\u7ebf\u56fe", "\u6574\u4f53\u89c4\u5212", "\u5168\u5c40\u89c4\u5212"]),
    ("concentrate-forces", [r"\bpriorit", r"\bwhich path\b", "\u4f18\u5148", "\u5148\u6253\u54ea\u6761", "\u4e3b\u653b\u65b9\u5411"]),
    ("contradiction-analysis", [r"\btrade[- ]?off\b", r"\bcompare\b", "\u6743\u8861", "\u5bf9\u6bd4", "\u77db\u76fe"]),
    ("practice-cognition", [r"\bpoc\b", r"\bscaffold\b", "\u811a\u624b\u67b6", "\u9a8c\u8bc1\u9aa8\u67b6", "\u6784\u5efa"]),
    ("investigation-first", [r"\banalyze\b", r"\btrace\b", r"\breconstruct\b", "\u5206\u6790", "\u8ffd\u8e2a", "\u68b3\u7406"]),
    ("criticism-self-criticism", [r"\bself[- ]?review\b", r"\bpostmortem\b", "\u590d\u76d8", "\u81ea\u5ba1", "\u6279\u8bc4"]),
]


def select_method(prompt: str, phase: str, mode: str) -> str:
    for method, patterns in METHOD_HINTS:
        if any(re.search(pat, prompt, re.I) for pat in patterns):
            return method
    if mode == "redteam-full":
        return PHASE_ESCALATION_METHOD.get(phase, PHASE_DEFAULT_METHOD.get(phase, "overall-planning"))
    return ""
