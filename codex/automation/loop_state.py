from __future__ import annotations

from dataclasses import dataclass, field

from .gate_engine import GateResult


@dataclass
class LoopRuntimeState:
    run_id: str
    session_id: str
    objective: str
    mode: str = "normal"
    automation_mode: str = "plan-only"
    phase: str = "general"
    router: str = ""
    leaf_skill: str = ""
    workflow_stage: str = "recon"
    loop_iteration: int = 0
    current_loop_type: str = ""
    current_task_id: str = ""
    selected_path: str = ""
    required_capabilities: tuple[str, ...] = ()
    selected_tools: tuple[str, ...] = ()
    missing_capabilities: tuple[str, ...] = ()
    recent_artifacts: tuple[str, ...] = ()
    evidence_level: str = "unknown"
    gate_results: tuple[GateResult, ...] = ()
    drift_score: float = 0.0
    rhythm_state: str = "healthy"
    stagnation_count: int = 0
    tool_failure_count: int = 0
    pseudo_complete_count: int = 0
    last_action: str = ""
    last_reason: str = ""
    next_step: str = ""
    notes: dict[str, str] = field(default_factory=dict)
