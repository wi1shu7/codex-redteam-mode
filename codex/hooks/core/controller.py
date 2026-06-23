from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
from pathlib import Path

from orchestrator import ReconArtifact, StrategyArtifact, StrategyPath, recon_gate, strategy_gate
from automation import build_quick_card, create_automation_plan, should_refresh_quick_card
from redteam_state import RedTeamState
from router import select_leaf_skill, select_method, select_router, select_skill_pack, select_subphase

from .doctrine import build_route_envelope
from .intent_engine import detect_intent
from .loop_engine import decide_loop_action
from .memory_store import (
    append_long_memory,
    latest_long_memory,
    load_session_memory,
    save_session_memory,
)
from .phase_detector import detect_phase
from .prompt_sanitizer import build_sanitizer_context
from .supplemental_prompts import build_prompt_overlay
from .taskbook import Taskbook, refresh_taskbook, select_current_task
from .verify_engine import verify_progress


GENERAL_HINTS = ("continue", "继续", "same target", "keep digging", "same objective")
BOUNDARY_TOKEN_REPLACEMENTS = {".": " ", ",": " ", "/": " ", "-": " ", "_": " "}
CONCRETE_EVIDENCE_MARKERS = (
    "burp",
    "raw request",
    "request",
    "response",
    "443/tcp",
    "80/tcp",
    "pcap",
    "source code",
    "controller",
    "shell",
)


@dataclass
class ProcessTurnResult:
    state: RedTeamState
    brief: str
    overlay: str
    artifact: object | None
    reason_code: str


def _normalize_for_boundary(text: str) -> list[str]:
    cleaned = text.casefold()
    for old, new in BOUNDARY_TOKEN_REPLACEMENTS.items():
        cleaned = cleaned.replace(old, new)
    return [token for token in cleaned.split() if token]


def _boundary_break(prompt: str, memory: dict) -> bool:
    boundary = memory.get("boundary", {}) if isinstance(memory, dict) else {}
    if not isinstance(boundary, dict):
        return False
    if boundary.get("allow_cross_system"):
        return False
    tokens = set(_normalize_for_boundary(prompt))
    for blocked in boundary.get("out_of_scope", []):
        if isinstance(blocked, str) and blocked.casefold() in tokens:
            return True
    return False


def _infer_evidence_level(prompt: str) -> str:
    lowered = prompt.casefold()
    if any(marker in lowered for marker in ("burp raw", "raw request", "pcap", "443/tcp", "80/tcp")):
        return "confirmed"
    if any(marker in lowered for marker in CONCRETE_EVIDENCE_MARKERS) and "token reuse risk" not in lowered:
        return "partial"
    return "unknown"


def _is_general_prompt(prompt: str) -> bool:
    lowered = prompt.casefold()
    return any(marker in lowered for marker in GENERAL_HINTS)


def _rehydrate_state(state: RedTeamState) -> RedTeamState:
    if state.objective:
        return state
    memory = latest_long_memory(state.session_id)
    if not memory:
        return state
    if memory.get("objective"):
        state.objective = str(memory.get("objective", state.objective))
    if memory.get("phase"):
        state.phase = str(memory.get("phase", state.phase))
    if memory.get("workflow_phase"):
        state.workflow_phase = str(memory.get("workflow_phase", state.workflow_phase))
    return state


def _extract_host_port(prompt: str) -> tuple[list[str], list[str], list[str]]:
    lowered = prompt.casefold()
    hosts = sorted(set(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", prompt)))
    ports = sorted(set(re.findall(r"\b\d{1,5}/tcp\b", lowered)))
    services: list[str] = []
    for marker in ("http", "https", "ssh", "ldap", "rdp", "mysql", "postgresql", "mongodb", "redis"):
        if marker in lowered:
            services.append(marker)
    return hosts, ports, services


def _build_recon_artifact(prompt: str, objective: str) -> ReconArtifact:
    hosts, ports, services = _extract_host_port(prompt)
    if not hosts and objective:
        hosts = [objective[:32] or "target"]
    return ReconArtifact(
        scope=objective or "selected target",
        hosts=hosts,
        ports=ports,
        services=services,
        evidence_refs=[prompt[:120]],
        confidence=0.8 if hosts or ports or services else 0.5,
    )


def _build_strategy_artifact(phase: str, selected_path: str, prompt: str) -> StrategyArtifact:
    return StrategyArtifact(
        source_phase="recon",
        candidate_paths=[
            StrategyPath(
                name=selected_path or phase,
                rationale=f"Derived from prompt evidence: {prompt[:120]}",
                required_validation=["Need concrete validation artifact"],
            )
        ],
        chosen_path=selected_path or phase,
        evidence_refs=[prompt[:80]],
    )


def _taskbook_to_memory(taskbook: Taskbook) -> dict:
    return {
        "objective": taskbook.objective,
        "workflow_phase": taskbook.workflow_phase,
        "selected_path": taskbook.selected_path,
        "coverage_tags": list(taskbook.coverage_tags),
        "todo_items": [
            {"id": item.id, "title": item.title, "status": item.status}
            for item in taskbook.todo_items
        ],
        "acceptance_checks": list(taskbook.acceptance_checks),
    }


def _build_automation_summary(objective: str, phase: str, prompt: str) -> list[str]:
    plan = create_automation_plan(objective=objective or prompt, phase=phase)
    lines: list[str] = []
    for step in plan.steps[:5]:
        lines.append(
            "[tool:{cap}] preferred={preferred} selected={selected} risk={risk} fallback={fallback}".format(
                cap=step.required_capability,
                preferred=step.preferred_tool,
                selected=step.tool,
                risk=step.risk,
                fallback=step.fallback_reason,
            )
        )
    for missing in plan.missing_capabilities[:5]:
        lines.append(f"[tool-missing:{missing}] no registered local MCP/tool matched this capability")
    return lines


def _bounded_tags(tags: list[str], limit: int = 24) -> list[str]:
    return list(dict.fromkeys(tag for tag in tags if tag))[-limit:]


def _bounded_recent_artifacts(items: list[object], limit: int = 24) -> list[object]:
    if not isinstance(items, list):
        return []
    return items[-limit:]


def process_turn(
    *,
    prompt: str,
    state: RedTeamState,
    codex_dir: Path,
    assistant_summary: str,
) -> ProcessTurnResult:
    working = deepcopy(state).normalized()
    working.loop_iteration += 1
    if _is_general_prompt(prompt):
        working = _rehydrate_state(working)
    memory = load_session_memory(working.session_id)
    prior_snapshot = latest_long_memory(working.session_id)

    if _boundary_break(prompt, memory):
        overlay = "[boundary] Request appears to cross the declared system boundary. Stay within in-scope assets only."
        working.last_reason_code = "boundary_break"
        return ProcessTurnResult(
            state=working,
            brief=build_route_envelope(working),
            overlay=overlay,
            artifact=None,
            reason_code="boundary_break",
        )

    intent = detect_intent(prompt, working)
    working.intent_type = intent.intent_type

    if intent.intent_type in {"new", "revise"}:
        working.objective = intent.objective_delta or prompt.strip()
        working.workflow_phase = "recon"
    elif not working.objective:
        working.objective = prompt.strip()

    preserve_previous_phase = intent.intent_type == "continue" and _is_general_prompt(prompt)
    if preserve_previous_phase and working.phase != "general":
        phase = working.phase
    else:
        phase = detect_phase(prompt)
        if phase == "general" and preserve_previous_phase and working.phase != "general":
            phase = working.phase
    working.phase = phase
    working.subphase = select_subphase(prompt, phase)
    working.method = select_method(prompt, phase, working.mode)
    working.router = select_router(prompt, phase)
    working.skill_pack = select_skill_pack(phase, working.router)
    working.leaf_skill = select_leaf_skill(prompt, phase, working.router)
    working.evidence_level = _infer_evidence_level(prompt)

    if working.objective.startswith("recover ") and _is_general_prompt(prompt):
        working.selected_path = "recon-for-sec"
    else:
        working.selected_path = working.leaf_skill if working.leaf_skill and working.leaf_skill != "hack" else working.router

    previous_signature = None
    if isinstance(prior_snapshot, dict):
        previous_signature = (
            prior_snapshot.get("objective"),
            prior_snapshot.get("phase"),
            prior_snapshot.get("workflow_phase"),
            prior_snapshot.get("path"),
        )
    current_signature = (working.objective, working.phase, working.workflow_phase, working.selected_path)
    if previous_signature == current_signature or _is_general_prompt(prompt):
        working.stagnation_count += 1
    else:
        working.stagnation_count = max(0, working.stagnation_count - 1)

    previous_taskbook = memory.get("taskbook")
    taskbook = refresh_taskbook(
        objective=working.objective,
        phase=working.workflow_phase if working.workflow_phase != "recon" and _is_general_prompt(prompt) else "strategy" if working.evidence_level == "confirmed" else working.workflow_phase,
        selected_path=working.selected_path,
        previous=previous_taskbook,
        intent_type=intent.intent_type,
    )
    selection = select_current_task(taskbook)
    if selection.current_task:
        working.current_task_id = selection.current_task.id
    working.active_skill_count = len([x for x in [working.router, working.skill_pack, working.leaf_skill] if x])

    artifact = None
    reason_code = "continue"
    gate_ok = False

    if working.evidence_level == "confirmed":
        artifact = _build_recon_artifact(prompt, working.objective)
        recon_decision = recon_gate(artifact)
        gate_ok = recon_decision.ok
        if recon_decision.ok:
            reason_code = "gate_pass"
        else:
            artifact = _build_strategy_artifact(phase, working.selected_path, prompt)
            decision = strategy_gate(artifact)
            gate_ok = decision.ok
            if decision.ok:
                reason_code = "gate_pass"
    elif working.workflow_phase == "recon" and _is_general_prompt(prompt) and state.workflow_phase:
        working.workflow_phase = state.workflow_phase

    verify = verify_progress(
        objective=working.objective,
        acceptance_checks=selection.taskbook.acceptance_checks,
        evidence_level=working.evidence_level,
        gate_ok=gate_ok,
        assistant_summary=assistant_summary,
    )
    if verify.pseudo_complete:
        working.pseudo_complete_count += 1
        reason_code = verify.reason_code
    elif reason_code == "continue":
        reason_code = verify.reason_code if verify.reason_code != "missing_evidence" else reason_code

    loop_decision = decide_loop_action(
        state=working,
        evidence_level=working.evidence_level,
        gate_ok=gate_ok,
        verify_passed=verify.passed,
        taskbook=selection.taskbook,
        current_task_id=working.current_task_id,
    )
    working.workflow_phase = loop_decision.next_stage
    reason_code = loop_decision.action

    working.drift_score = min(
        1.0,
        working.stagnation_count * 0.12
        + (0.15 if phase == "general" else 0.0)
        + (0.1 if working.pseudo_complete_count else 0.0),
    )
    working.drift_level = "high" if working.drift_score >= 0.7 else "medium" if working.drift_score >= 0.3 else "low"
    working.loop_health = "degraded" if working.drift_level == "high" else "strained" if working.drift_level == "medium" else "healthy"
    working.last_reason_code = reason_code

    seen_tags = _bounded_tags(memory.get("coverage_tags_seen", []) + [phase, working.router, working.workflow_phase, working.selected_path])
    pending_tags = _bounded_tags(
        [tag for tag in memory.get("coverage_tags_pending", []) if tag not in seen_tags]
        + [tag for tag in selection.taskbook.coverage_tags if tag not in seen_tags]
    )
    save_session_memory(
        working.session_id,
        {
            "taskbook": _taskbook_to_memory(selection.taskbook),
            "coverage_tags_seen": seen_tags,
            "coverage_tags_pending": pending_tags,
            "acceptance_checks": list(selection.taskbook.acceptance_checks),
            "recent_artifacts": _bounded_recent_artifacts(
                list(memory.get("recent_artifacts", []))
                + ([{"kind": artifact.__class__.__name__}] if artifact else [])
            ),
        },
    )
    append_long_memory(
        working.session_id,
        {
            "objective": working.objective,
            "phase": working.phase,
            "workflow_phase": working.workflow_phase,
            "path": working.selected_path,
            "action": reason_code,
        },
    )

    brief_lines = [
        build_route_envelope(working),
        f"[intent:{intent.intent_type}]",
        f"[task:{working.current_task_id}]",
        f"[loop:{loop_decision.action}]",
        f"[loop-reason:{loop_decision.reason}]",
        f"[loop-trigger:{loop_decision.trigger}]",
        f"[feedback-gate:{loop_decision.feedback_gate}]",
        f"[exit-condition:{loop_decision.exit_condition}]",
        f"[next-step:{loop_decision.next_step}]",
    ]
    if should_refresh_quick_card(loop_decision, loop_iteration=working.loop_iteration):
        brief_lines.append(
            build_quick_card(
                objective=working.objective,
                selected_path=working.selected_path,
                decision=loop_decision,
                recent_artifacts=tuple(item.get("kind", "") for item in memory.get("recent_artifacts", []) if isinstance(item, dict)),
            )
        )
    brief_lines.extend(_build_automation_summary(working.objective, working.phase, prompt))
    for check in selection.taskbook.acceptance_checks[:2]:
        brief_lines.append(f"[check] {check}")
    brief = "\n".join(brief_lines)

    overlays: list[str] = []
    sanitizer = build_sanitizer_context(prompt)
    if sanitizer:
        overlays.append(sanitizer)
    supplemental = build_prompt_overlay(codex_dir, phase)
    if supplemental:
        overlays.append(supplemental)

    return ProcessTurnResult(
        state=working,
        brief=brief,
        overlay="\n".join(overlays),
        artifact=artifact,
        reason_code=reason_code,
    )
