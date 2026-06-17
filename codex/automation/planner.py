from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .tool_discovery import discover_local_tools, select_tools_for_task
from .tool_registry import ToolRegistry


@dataclass(frozen=True)
class AutomationStep:
    id: str
    tool: str
    required_capability: str
    preferred_tool: str
    risk: str
    fallback_reason: str
    expected_artifact: str
    requires_approval: bool = False


@dataclass(frozen=True)
class AutomationPlan:
    objective: str
    phase: str
    steps: tuple[AutomationStep, ...]
    required_capabilities: tuple[str, ...] = ()
    missing_capabilities: tuple[str, ...] = ()


def infer_required_capabilities(objective: str, phase: str) -> tuple[str, ...]:
    text = f"{objective} {phase}".casefold()
    capabilities: list[str] = []
    if phase in {"web", "recon", "general"} or any(word in text for word in ("页面", "接口", "url", "web", "http")):
        capabilities.append("page_fetch")
    if any(word in text for word in ("交互", "浏览器", "登录", "dom", "browser", "click")):
        capabilities.append("browser_automation")
    if phase == "mobile" or any(word in text for word in ("apk", "android", "安卓")):
        capabilities.append("apk_decompile")
    if phase == "reverse" or any(word in text for word in ("二进制", "协议", "binary", "protocol", "ida")):
        capabilities.append("binary_reverse")
    if any(word in text for word in ("代码", "脚本", "poc", "harness", "报告", "生成")):
        capabilities.append("code_generation")
    return tuple(dict.fromkeys(capabilities or ["page_fetch"]))


def _artifact_for(capability: str) -> str:
    return {
        "page_fetch": "webfetch_summary",
        "browser_automation": "browser_trace",
        "apk_decompile": "jadx_api_inventory",
        "binary_reverse": "ida_function_notes",
        "code_generation": "generated_code",
    }.get(capability, f"{capability}_artifact")


def create_automation_plan(
    *,
    objective: str,
    phase: str,
    tool_config_paths: Sequence[str | Path] | None = None,
    registry: ToolRegistry | None = None,
) -> AutomationPlan:
    inventory = discover_local_tools(tool_config_paths)
    required = infer_required_capabilities(objective, phase)
    selected = select_tools_for_task(required, inventory)
    registry = registry or ToolRegistry()
    steps: list[AutomationStep] = []
    for index, capability in enumerate(required, start=1):
        choice = selected.get(capability)
        if not choice:
            continue
        spec = registry.register_selected(
            capability=choice.capability,
            preferred_tool=choice.preferred_tool,
            selected_tool=choice.selected_tool,
            risk=choice.risk,
            fallback_reason=choice.fallback_reason,
            capability_match=choice.capability_match,
        )
        steps.append(
            AutomationStep(
                id=f"step-{index}",
                tool=spec.name,
                required_capability=capability,
                preferred_tool=spec.preferred_tool,
                risk=spec.risk,
                fallback_reason=spec.fallback_reason,
                expected_artifact=_artifact_for(capability),
                requires_approval=spec.requires_approval,
            )
        )
    planned = {step.required_capability for step in steps}
    missing = tuple(capability for capability in required if capability not in planned)
    return AutomationPlan(
        objective=objective,
        phase=phase,
        steps=tuple(steps),
        required_capabilities=required,
        missing_capabilities=missing,
    )
