#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
CODEX_DIR = HOOKS_DIR.parent
for candidate in (HOOKS_DIR, CODEX_DIR):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from core import build_prompt_chain_notice, emit_hook_json, extract_session_id, extract_session_start_source, extract_transcript_path, load_runtime_state, reset_runtime_state
from core.context_prepoison import build_prepoisoned_context
from core.prompt_parser import decode_stdin, load_payload
from core.refusal_backstop import session_start_backstop_messages


def main() -> None:
    raw = decode_stdin(sys.stdin.buffer.read())
    session_id = None
    transcript_path = None
    source = ""
    if raw.strip():
        try:
            payload = load_payload(raw)
            session_id = extract_session_id(payload)
            transcript_path = extract_transcript_path(payload)
            source = extract_session_start_source(payload)
        except Exception:
            session_id = None

    state = load_runtime_state(session_id=session_id) if source in {"resume", "compact"} else reset_runtime_state(session_id=session_id)
    if state.mode == "normal":
        context = (
            "[mode] Default is normal. Red-team mode stays off until explicitly enabled. "
            "When enabled, guidance stays lightweight and routes by phase -> router -> pack -> leaf. "
            "Use method only when it adds value. instruction.ctf.md remains highest priority."
        )
    else:
        context = (
            f"[mode] Session mode restored ({state.mode}). "
            "Continue using phase -> router -> pack -> leaf routing. "
            "Use method only when it adds value. instruction.ctf.md remains highest priority."
        )
    notice = build_prompt_chain_notice(CODEX_DIR, mode=state.mode)
    if notice:
        context = f"{context}\n{notice}"

    prepoison = build_prepoisoned_context()
    context = f"{context}\n{prepoison}"

    backstop = session_start_backstop_messages(session_id, transcript_path=transcript_path)
    if backstop:
        context = f"{context}\n" + "\n".join(backstop)
    print(emit_hook_json("SessionStart", context))


if __name__ == "__main__":
    main()
