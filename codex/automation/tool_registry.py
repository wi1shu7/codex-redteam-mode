from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolSpec:
    name: str
    capability: str
    preferred_tool: str
    risk: str
    fallback_reason: str = ""
    capability_match: str = ""
    requires_scope: bool = False
    requires_approval: bool = False


class ToolRegistry:
    def __init__(self) -> None:
        self._by_name: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._by_name[spec.name] = spec

    def register_selected(
        self,
        *,
        capability: str,
        preferred_tool: str,
        selected_tool: str,
        risk: str,
        fallback_reason: str,
        capability_match: str = "",
    ) -> ToolSpec:
        spec = ToolSpec(
            name=selected_tool,
            capability=capability,
            preferred_tool=preferred_tool,
            risk=risk,
            fallback_reason=fallback_reason,
            capability_match=capability_match or capability,
            requires_scope=risk in {"passive", "active_low", "active_medium", "restricted", "unknown"},
            requires_approval=risk not in {"safe", "passive", "active_low"},
        )
        self.register(spec)
        return spec

    def require(self, name: str) -> ToolSpec:
        if name not in self._by_name:
            raise KeyError(f"Tool is not registered: {name}")
        return self._by_name[name]

    def names(self) -> tuple[str, ...]:
        return tuple(self._by_name)
