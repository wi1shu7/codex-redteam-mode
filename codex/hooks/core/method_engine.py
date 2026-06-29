from __future__ import annotations
import re
from router.mappings import PHASE_DEFAULT_METHOD, PHASE_ESCALATION_METHOD

METHOD_HINTS = [
    ("workflows", [r"\bworkflow\b", r"\bplaybook\b", r"\bchain\b", "工作流", "流程", "多阶段"]),
    ("overall-planning", [r"\bplan\b", r"\broadmap\b", "路线图", "整体规划", "全局规划"]),
    ("concentrate-forces", [r"\bpriorit", r"\bwhich path\b", "优先", "先打哪条", "主攻方向"]),
    ("contradiction-analysis", [r"\btrade[- ]?off\b", r"\bcompare\b", "权衡", "对比", "矛盾"]),
    ("practice-cognition", [r"\bpoc\b", r"\bscaffold\b", "脚手架", "验证骨架", "构建"]),
    ("investigation-first", [r"\banalyze\b", r"\btrace\b", r"\breconstruct\b", "分析", "追踪", "梳理"]),
    ("criticism-self-criticism", [r"\bself[- ]?review\b", r"\bpostmortem\b", "复盘", "自审", "批评"]),
]


def select_method(prompt: str, phase: str, mode: str) -> str:
    for method, patterns in METHOD_HINTS:
        if any(re.search(pat, prompt, re.I) for pat in patterns):
            return method
    if mode == "redteam-full":
        return PHASE_ESCALATION_METHOD.get(phase, PHASE_DEFAULT_METHOD.get(phase, "overall-planning"))
    return PHASE_DEFAULT_METHOD.get(phase, "overall-planning")
