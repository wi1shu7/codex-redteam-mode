from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence
from urllib.parse import urlparse

from .tool_registry import ToolRegistry


@dataclass(frozen=True)
class Scope:
    in_scope: tuple[str, ...] = ()
    out_of_scope: tuple[str, ...] = ()
    allow_cross_system: bool = False


@dataclass(frozen=True)
class ScopeDecision:
    allowed: bool
    reason: str


class ScopeGate:
    def __init__(self, scope: Scope) -> None:
        self.scope = scope

    def _target(self, args: Mapping[str, object]) -> str:
        for key in ("target", "url", "endpoint", "host"):
            value = args.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _matches_scope_entry(self, target: str, scope_entry: str) -> bool:
        target_parsed = urlparse(target if "://" in target else f"//{target}")
        scope_parsed = urlparse(scope_entry if "://" in scope_entry else f"//{scope_entry}")
        target_host = (target_parsed.hostname or "").casefold()
        scope_host = (scope_parsed.hostname or "").casefold()
        if not target_host or not scope_host:
            return target.casefold() == scope_entry.casefold()
        if target_host != scope_host:
            return False
        if scope_parsed.scheme and target_parsed.scheme and target_parsed.scheme != scope_parsed.scheme:
            return False
        if scope_parsed.port is not None and target_parsed.port != scope_parsed.port:
            return False
        scope_path = scope_parsed.path.rstrip("/")
        if scope_path:
            target_path = target_parsed.path.rstrip("/")
            return target_path == scope_path or target_path.startswith(f"{scope_path}/")
        return True

    def check_tool(self, tool_name: str, args: Mapping[str, object], registry: ToolRegistry) -> ScopeDecision:
        spec = registry.require(tool_name)
        target = self._target(args)
        if spec.requires_scope and not target:
            return ScopeDecision(False, "missing_target")
        if spec.requires_scope and target and not self.scope.allow_cross_system and not self.scope.in_scope:
            return ScopeDecision(False, "missing_scope")
        if not self.scope.allow_cross_system and target:
            for blocked in self.scope.out_of_scope:
                if self._matches_scope_entry(target, blocked):
                    return ScopeDecision(False, "out_of_scope")
            if self.scope.in_scope and not any(self._matches_scope_entry(target, allowed) for allowed in self.scope.in_scope):
                return ScopeDecision(False, "not_in_scope")
        if spec.requires_approval and not args.get("approved", False):
            return ScopeDecision(False, "approval_required")
        return ScopeDecision(True, "allowed")
