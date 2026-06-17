from __future__ import annotations

import json


def emit_hook_json(
    event: str,
    context: str,
    *,
    metadata: dict | None = None,
    session_id: str = "",
    timestamp: str = "",
    phase: str = "",
    inject_role_overlay: bool = False,
    inject_prepoison: bool = False,
) -> str:
    """Emit a hook JSON payload for the Codex CLI interface.

    Args:
        event: Hook event name (e.g. "PreToolUse", "PostToolExecution", "SessionStart").
        context: Additional context text injected into the hook output.
        metadata: Optional key-value pairs attached to hook output.
        session_id: Optional session identifier.
        timestamp: Optional ISO-8601 timestamp.
        phase: Current red-team phase for role overlay injection.
        inject_role_overlay: When True, prepend the role identity overlay to context.
        inject_prepoison: When True, prepend pre-poisoned conversation history.
    """
    # Build augmented context with active pre-injection layers
    augmented_context = context

    if inject_prepoison:
        try:
            from .context_prepoison import build_prepoisoned_context
            prepoison = build_prepoisoned_context()
            augmented_context = f"{prepoison}\n\n---\n\n{augmented_context}"
        except ImportError:
            pass

    if inject_role_overlay:
        try:
            from .supplemental_prompts import build_role_overlay
            role = build_role_overlay(phase)
            if role:
                augmented_context = f"{role}\n\n---\n\n{augmented_context}"
        except ImportError:
            pass

    payload: dict = {
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": augmented_context,
        }
    }
    if metadata:
        payload["hookSpecificOutput"]["metadata"] = metadata
    if session_id:
        payload["hookSpecificOutput"]["sessionId"] = session_id
    if timestamp:
        payload["hookSpecificOutput"]["timestamp"] = timestamp
    if phase:
        payload["hookSpecificOutput"]["phase"] = phase

    return json.dumps(payload, ensure_ascii=False)
