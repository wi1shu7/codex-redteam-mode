from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field


@dataclass
class TaskItem:
    id: str
    title: str
    status: str = "pending"


@dataclass
class Taskbook:
    objective: str
    workflow_phase: str = "recon"
    selected_path: str = ""
    coverage_tags: list[str] = field(default_factory=list)
    todo_items: list[TaskItem] = field(default_factory=list)
    acceptance_checks: list[str] = field(default_factory=list)


@dataclass
class TaskSelection:
    taskbook: Taskbook
    current_task: TaskItem | None


def _default_todos(objective: str, phase: str, selected_path: str) -> list[TaskItem]:
    title_root = selected_path or phase or "path"
    return [
        TaskItem(id="task-1", title=f"Scope and trace {objective or title_root}"),
        TaskItem(id="task-2", title=f"Validate evidence for {title_root}"),
        TaskItem(id="task-3", title="Decide next gate or revision"),
    ]


def _default_checks(selected_path: str) -> list[str]:
    label = selected_path or "selected path"
    return [
        f"Need concrete evidence for {label}",
        "Need a clear next-step decision",
    ]


def _coerce_taskbook(previous: Taskbook | dict | None) -> Taskbook | None:
    if previous is None:
        return None
    if isinstance(previous, Taskbook):
        return deepcopy(previous)
    if isinstance(previous, dict):
        todo_items = [
            TaskItem(
                id=str(item.get("id", f"task-{idx+1}")),
                title=str(item.get("title", "")),
                status=str(item.get("status", "pending")),
            )
            for idx, item in enumerate(previous.get("todo_items", []))
            if isinstance(item, dict)
        ]
        return Taskbook(
            objective=str(previous.get("objective", "")),
            workflow_phase=str(previous.get("workflow_phase", "recon")),
            selected_path=str(previous.get("selected_path", "")),
            coverage_tags=list(previous.get("coverage_tags", [])),
            todo_items=todo_items,
            acceptance_checks=list(previous.get("acceptance_checks", [])),
        )
    return None


def refresh_taskbook(
    *,
    objective: str,
    phase: str,
    selected_path: str,
    previous: Taskbook | dict | None,
    intent_type: str,
) -> Taskbook:
    prior = _coerce_taskbook(previous)
    if prior and intent_type not in {"new", "revise"} and prior.objective == objective:
        if not prior.todo_items:
            prior.todo_items = _default_todos(objective, phase, selected_path)
        if not prior.acceptance_checks:
            prior.acceptance_checks = _default_checks(selected_path)
        prior.workflow_phase = phase or prior.workflow_phase
        prior.selected_path = selected_path or prior.selected_path
        prior.coverage_tags = list(dict.fromkeys(prior.coverage_tags or [selected_path, phase]))
        return prior

    coverage_tags = [tag for tag in [selected_path, phase] if tag]
    return Taskbook(
        objective=objective,
        workflow_phase=phase or "recon",
        selected_path=selected_path,
        coverage_tags=list(dict.fromkeys(coverage_tags)),
        todo_items=_default_todos(objective, phase, selected_path),
        acceptance_checks=_default_checks(selected_path),
    )


def select_current_task(taskbook: Taskbook) -> TaskSelection:
    cloned = deepcopy(taskbook)
    current: TaskItem | None = None
    for item in cloned.todo_items:
        if item.status in {"pending", "running"}:
            item.status = "running"
            current = deepcopy(item)
            break
    return TaskSelection(taskbook=cloned, current_task=current)
