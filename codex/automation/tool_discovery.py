from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


PREFERRED_TOOL_BY_CAPABILITY: dict[str, str] = {
    "page_fetch": "WebFetch",
    "content_extract": "WebFetch",
    "browser_automation": "Browser MCP",
    "dom_snapshot": "Browser MCP",
    "screenshot": "Browser MCP",
    "binary_reverse": "IDA MCP",
    "protocol_analysis": "IDA MCP",
    "apk_decompile": "JADX MCP",
    "android_static_analysis": "JADX MCP",
    "code_generation": "Claude code+Codex",
    "ai_coding": "Claude code+Codex",
}

CAPABILITY_ALIASES: dict[str, set[str]] = {
    "page_fetch": {"page_fetch", "content_extract", "web_fetch", "webfetch", "http_fetch"},
    "content_extract": {"content_extract", "page_fetch", "web_fetch", "webfetch"},
    "browser_automation": {"browser_automation", "browser", "dom_snapshot", "screenshot", "playwright"},
    "dom_snapshot": {"dom_snapshot", "browser_automation", "browser"},
    "screenshot": {"screenshot", "browser_automation", "browser"},
    "binary_reverse": {"binary_reverse", "reverse_engineering", "disassemble", "decompile", "protocol_analysis"},
    "protocol_analysis": {"protocol_analysis", "binary_reverse", "pcap_analysis"},
    "apk_decompile": {"apk_decompile", "android_static_analysis", "jadx", "apk_reverse"},
    "android_static_analysis": {"android_static_analysis", "apk_decompile", "manifest_analysis"},
    "code_generation": {"code_generation", "ai_coding", "code_edit", "test_harness", "report_generation"},
    "ai_coding": {"ai_coding", "code_generation", "code_edit"},
}

NAME_CAPABILITY_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("webfetch", ("page_fetch", "content_extract")),
    ("web-fetch", ("page_fetch", "content_extract")),
    ("browser", ("browser_automation", "dom_snapshot", "screenshot")),
    ("playwright", ("browser_automation", "dom_snapshot", "screenshot")),
    ("ida", ("binary_reverse", "protocol_analysis")),
    ("radare", ("binary_reverse", "protocol_analysis")),
    ("r2", ("binary_reverse", "protocol_analysis")),
    ("jadx", ("apk_decompile", "android_static_analysis")),
    ("apk", ("apk_decompile", "android_static_analysis")),
    ("codex", ("code_generation", "ai_coding")),
    ("claude", ("code_generation", "ai_coding")),
)


@dataclass(frozen=True)
class ToolInventoryItem:
    name: str
    capabilities: tuple[str, ...]
    source: str = "local"
    raw: Mapping[str, object] | None = None


@dataclass(frozen=True)
class CapabilitySelection:
    capability: str
    preferred_tool: str
    selected_tool: str
    capability_match: str
    risk: str
    fallback_reason: str


def _normalize_capability(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _risk_for_capability(capability: str) -> str:
    if capability in {"page_fetch", "content_extract"}:
        return "passive"
    if capability in {"browser_automation", "dom_snapshot", "screenshot"}:
        return "active_low"
    if capability in {"binary_reverse", "protocol_analysis", "apk_decompile", "android_static_analysis"}:
        return "safe"
    if capability in {"code_generation", "ai_coding"}:
        return "safe"
    return "unknown"


def _coerce_tool(raw: Mapping[str, object], source: str) -> ToolInventoryItem | None:
    name = str(raw.get("name") or raw.get("id") or raw.get("server") or "").strip()
    if not name:
        return None
    caps_raw = raw.get("capabilities") or raw.get("capability") or raw.get("tools") or []
    if isinstance(caps_raw, str):
        caps = (_normalize_capability(caps_raw),)
    elif isinstance(caps_raw, Iterable):
        caps = tuple(_normalize_capability(item) for item in caps_raw if str(item).strip())
    else:
        caps = ()
    if not caps:
        caps = _infer_capabilities_from_name(name)
    return ToolInventoryItem(name=name, capabilities=caps, source=source, raw=dict(raw))


def _infer_capabilities_from_name(name: str) -> tuple[str, ...]:
    lowered = name.casefold()
    caps: list[str] = []
    for marker, inferred in NAME_CAPABILITY_HINTS:
        if re.search(rf"(^|[^a-z0-9]){re.escape(marker)}([^a-z0-9]|$)", lowered):
            caps.extend(inferred)
    return tuple(dict.fromkeys(caps))


def _entries_from_mcpservers(raw_servers: object, source: str) -> list[ToolInventoryItem]:
    if not isinstance(raw_servers, Mapping):
        return []
    tools: list[ToolInventoryItem] = []
    for name, value in raw_servers.items():
        if isinstance(value, Mapping):
            entry = dict(value)
        else:
            entry = {}
        entry.setdefault("name", str(name))
        item = _coerce_tool(entry, source)
        if item:
            tools.append(item)
    return tools


def discover_tools_from_config(path: str | Path) -> tuple[ToolInventoryItem, ...]:
    """Read a local MCP/tool inventory JSON file.

    Supported shapes:
    - {"mcp_tools": [{"name": "...", "capabilities": [...]}]}
    - {"tools": [...]}
    - {"mcpServers": {"server-name": {"command": "..."}}}
    - [{"name": "...", "capabilities": [...]}]
    """

    cfg_path = Path(path)
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        if isinstance(data.get("mcpServers"), Mapping):
            return tuple(_entries_from_mcpservers(data.get("mcpServers"), str(cfg_path)))
        entries = data.get("mcp_tools") or data.get("tools") or data.get("servers") or []
    else:
        entries = data
    if not isinstance(entries, list):
        return ()
    tools: list[ToolInventoryItem] = []
    for entry in entries:
        if isinstance(entry, Mapping):
            item = _coerce_tool(entry, str(cfg_path))
            if item:
                tools.append(item)
    return tuple(tools)


def discover_local_tools(paths: Sequence[str | Path] | None = None) -> tuple[ToolInventoryItem, ...]:
    """Discover local MCP/tool inventory from explicit paths or env config.

    This intentionally reads local metadata only; it does not execute MCP servers.
    """

    candidates: list[Path] = []
    if paths:
        candidates.extend(Path(p) for p in paths)
    env_paths = os.environ.get("CODEX_REDTEAM_MCP_TOOLS", "")
    for item in env_paths.split(os.pathsep):
        if item.strip():
            candidates.append(Path(item.strip()))

    tools: list[ToolInventoryItem] = []
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            try:
                tools.extend(discover_tools_from_config(candidate))
            except (OSError, json.JSONDecodeError):
                continue
    return tuple(tools)


def _matches(required: str, offered: str) -> bool:
    required_norm = _normalize_capability(required)
    offered_norm = _normalize_capability(offered)
    aliases = CAPABILITY_ALIASES.get(required_norm, {required_norm})
    return offered_norm in aliases


def _tool_supports(tool: ToolInventoryItem, capability: str) -> str:
    for offered in tool.capabilities:
        if _matches(capability, offered):
            return offered
    return ""


def select_tools_for_task(
    required_capabilities: Sequence[str],
    inventory: Sequence[ToolInventoryItem],
) -> dict[str, CapabilitySelection]:
    selections: dict[str, CapabilitySelection] = {}
    for raw_capability in required_capabilities:
        capability = _normalize_capability(raw_capability)
        preferred = PREFERRED_TOOL_BY_CAPABILITY.get(capability, "")
        selected: ToolInventoryItem | None = None
        match = ""

        if preferred:
            for item in inventory:
                item_match = _tool_supports(item, capability)
                if item.name.casefold() == preferred.casefold() and item_match:
                    selected, match = item, item_match
                    break

        if selected is None:
            for item in inventory:
                item_match = _tool_supports(item, capability)
                if item_match:
                    selected, match = item, item_match
                    break

        if selected is None:
            continue

        fallback = "preferred_tool_available" if selected.name.casefold() == preferred.casefold() else "preferred_tool_unavailable"
        selections[capability] = CapabilitySelection(
            capability=capability,
            preferred_tool=preferred,
            selected_tool=selected.name,
            capability_match=match,
            risk=_risk_for_capability(capability),
            fallback_reason=fallback,
        )
    return selections
