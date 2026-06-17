from __future__ import annotations

from dataclasses import dataclass, field

from .taskbook import Taskbook


@dataclass
class ActivationPlan:
    objective: str
    phase: str
    selected_path: str
    router: str
    leaf_skill: str
    coverage_gaps: list[str] = field(default_factory=list)


def plan_activation(
    *,
    objective: str,
    phase: str,
    selected_path: str,
    router: str,
    leaf_skill: str,
    taskbook: Taskbook,
    coverage_pending: list[str],
    coverage_seen: list[str],
) -> ActivationPlan:
    del coverage_seen, taskbook
    return ActivationPlan(
        objective=objective,
        phase=phase,
        selected_path=selected_path,
        router=router,
        leaf_skill=leaf_skill,
        coverage_gaps=list(coverage_pending),
    )
