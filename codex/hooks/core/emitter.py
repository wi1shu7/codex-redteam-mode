from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


def emit_hook_json(
    event: str,
    context: str,
    *,
    role_phase: str = "",
    inject_role_overlay: bool = False,
    inject_prepoison: bool = False,
) -> str:
    """Emit a hook JSON payload for the Codex CLI interface.

    Args:
        event: Context hook event name ("SessionStart" or "UserPromptSubmit").
        context: Additional context text injected into the hook output.
        role_phase: Current red-team phase used only to build the role overlay.
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
            logger.debug("context_prepoison module not available")

    if inject_role_overlay:
        try:
            from .supplemental_prompts import build_role_overlay
            role = build_role_overlay(role_phase)
            if role:
                augmented_context = f"{role}\n\n---\n\n{augmented_context}"
        except ImportError:
            logger.debug("supplemental_prompts module not available")

    payload: dict = {
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": augmented_context,
        }
    }

    return json.dumps(payload, ensure_ascii=True)
