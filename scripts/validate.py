from __future__ import annotations

import argparse
import importlib.util
import io
import json
import runpy
import sys
from pathlib import Path


class FakeIn:
    def __init__(self, payload: bytes) -> None:
        self.buffer = io.BytesIO(payload)


def assert_exists(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"missing: {path}")


def run_hook(path: Path, payload: dict) -> str:
    old_stdin, old_stdout = sys.stdin, sys.stdout
    buf = io.StringIO()
    sys.stdout = buf
    sys.stdin = FakeIn(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    try:
        runpy.run_path(str(path), run_name="__main__")
    finally:
        sys.stdin, sys.stdout = old_stdin, old_stdout
    return buf.getvalue().strip()


def hook_context(output: str) -> str:
    if not output:
        return ""
    raw = json.loads(output)
    return raw["hookSpecificOutput"]["additionalContext"]


def hook_context_len(output: str) -> int:
    return len(hook_context(output))


def status_line(name: str, ok: bool) -> str:
    return f"- {name}: {'ok' if ok else 'fail'}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    args = parser.parse_args()
    codex_home = Path(args.codex_home)

    files = [
        codex_home / "redteam-install-manifest.json",
        codex_home / "instruction.ctf.md",
        codex_home / "prompts" / "system-prompt.md",
        codex_home / "prompts" / "do_special.md",
        codex_home / "prompts" / "Reverse.md",
        codex_home / "AGENTS.md",
        codex_home / "hooks.json",
        codex_home / "hooks" / "session-start-context.py",
        codex_home / "hooks" / "hook-security-context-hook.py",
        codex_home / "hooks" / "redteam_state.py",
        codex_home / "hooks" / "core" / "__init__.py",
        codex_home / "router" / "__init__.py",
        codex_home / "orchestrator" / "__init__.py",
    ]
    for file_path in files:
        assert_exists(file_path)

    hooks_dir = codex_home / "hooks"
    for insert_path in (hooks_dir, codex_home):
        insert_str = str(insert_path)
        if insert_str not in sys.path:
            sys.path.insert(0, insert_str)

    for idx, hook in enumerate(
        [
            codex_home / "hooks" / "session-start-context.py",
            codex_home / "hooks" / "hook-security-context-hook.py",
            codex_home / "hooks" / "redteam_state.py",
        ],
        start=1,
    ):
        name = f"validate_mod_{idx}"
        spec = importlib.util.spec_from_file_location(name, hook)
        mod = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules[name] = mod
        spec.loader.exec_module(mod)

    session_hook = codex_home / "hooks" / "session-start-context.py"
    prompt_hook = codex_home / "hooks" / "hook-security-context-hook.py"

    enable = run_hook(prompt_hook, {"session_id": "validate-main", "prompt": "/redteam light"})
    reverse = run_hook(
        prompt_hook,
        {"session_id": "validate-main", "prompt": "Analyze this malware loader sample and recover the execution chain"},
    )
    reverse_sem = run_hook(
        prompt_hook,
        {"session_id": "validate-main", "prompt": "This program releases resources and spawns a child process, help reconstruct the execution flow"},
    )
    audit = run_hook(
        prompt_hook,
        {"session_id": "validate-main", "prompt": "Audit this controller and middleware from entrypoint to dangerous sink"},
    )
    audit_sem = run_hook(
        prompt_hook,
        {"session_id": "validate-main", "prompt": "Help trace from the entrypoint down to the dangerous function and identify trust boundary failures"},
    )
    postex_sem = run_hook(
        prompt_hook,
        {"session_id": "validate-main", "prompt": "We already have a shell, what is the next host triage and lateral movement preparation step?"},
    )
    cloud_route = run_hook(
        prompt_hook,
        {"session_id": "validate-main", "prompt": "Analyze AWS IAM role assumption and metadata credential abuse paths"},
    )
    container_route = run_hook(
        prompt_hook,
        {"session_id": "validate-main", "prompt": "Assess kubernetes hostPath and privileged pod breakout risk"},
    )
    network_route = run_hook(
        prompt_hook,
        {"session_id": "validate-main", "prompt": "Check HTTP/2 request smuggling and websocket protocol issues from this traffic"},
    )
    crypto_route = run_hook(
        prompt_hook,
        {"session_id": "validate-main", "prompt": "Review this RSA and hash challenge for practical attack paths"},
    )
    mobile_route = run_hook(
        prompt_hook,
        {"session_id": "validate-main", "prompt": "Analyze this Android APK with SSL pinning and Frida bypass considerations"},
    )
    enable_full = run_hook(prompt_hook, {"session_id": "validate-full", "prompt": "/redteam full"})
    full_web = run_hook(
        prompt_hook,
        {"session_id": "validate-full", "prompt": "Review Burp JWT login traffic and verify token boundary reuse risks"},
    )
    full_reverse = run_hook(
        prompt_hook,
        {"session_id": "validate-full", "prompt": "Analyze this malware loader sample and recover the execution chain"},
    )
    session_ctx = run_hook(session_hook, {"session_id": "validate-session"})
    ordinary = run_hook(prompt_hook, {"session_id": "validate-session-2", "prompt": "Write a normal React page"})
    disable = run_hook(prompt_hook, {"session_id": "validate-main", "prompt": "/redteam off"})

    if str(codex_home) not in sys.path:
        sys.path.insert(0, str(codex_home))
    import orchestrator as orch

    recon = orch.ReconArtifact(
        scope="lab",
        hosts=["10.0.0.5"],
        ports=["80/tcp"],
        services=["http"],
        evidence_refs=["scan.json"],
        confidence=0.9,
    )
    strategy = orch.StrategyArtifact(
        candidate_paths=[orch.StrategyPath(name="web-path", rationale="http present")],
        chosen_path="web-path",
        evidence_refs=["scan.json"],
    )
    review = orch.ReviewArtifact(status="pass", next_action="deliver")

    manifest_file = codex_home / "redteam-install-manifest.json"
    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    manifest_ok = manifest_data.get("name") == "codex-redteam-optin-mode" and any(
        str(path).endswith("instruction.ctf.md")
        for path in manifest_data.get("managed_paths", [])
    )

    checks = [
        ("files", True),
        ("install manifest", manifest_ok),
        (
            "prompt chain session notice",
            "[prompt-chain]" in session_ctx and "instruction.ctf.md is highest priority" in session_ctx,
        ),
        ("enable", "enabled (redteam-light)" in enable),
        ("enable full", "enabled (redteam-full)" in enable_full),
        ("reverse phase", "[phase:reverse]" in reverse),
        ("reverse prompt overlay", "[overlay:Reverse|supplemental-phase]" in reverse),
        ("reverse semantic fallback", "[phase:reverse]" in reverse_sem),
        ("code-audit phase", "[phase:code-audit]" in audit),
        ("code-audit semantic fallback", "[phase:code-audit]" in audit_sem),
        ("postex semantic fallback", "[phase:postex]" in postex_sem),
        ("cloud routing", "[phase:cloud]" in cloud_route and "[pack:redteam-cloud-detail-pack]" in cloud_route),
        (
            "container routing",
            "[phase:container]" in container_route and "[pack:redteam-container-detail-pack]" in container_route,
        ),
        ("network routing", "[phase:network]" in network_route and "[pack:redteam-network-detail-pack]" in network_route),
        ("crypto routing", "[phase:crypto]" in crypto_route and "[pack:redteam-crypto-detail-pack]" in crypto_route),
        ("mobile routing", "[phase:mobile]" in mobile_route and "[pack:redteam-mobile-detail-pack]" in mobile_route),
        ("method/router/pack/leaf routing", all(token in full_web for token in ("[router:", "[pack:", "[leaf:"))),
        ("prompt overlays active", "[overlay:Reverse|supplemental-phase]" in full_reverse),
        (
            "redteam-full distinction",
            "[mode:redteam-full]" in full_web
            and "[workflow:structured-orchestration]" in full_web
            and "[review:required]" in full_web,
        ),
        ("session start context size", hook_context_len(session_ctx) <= 700),
        ("ordinary prompt stays empty", ordinary == ""),
        ("recon gate", orch.recon_gate(recon).ok),
        ("strategy gate", orch.strategy_gate(strategy).ok),
        ("review gate", orch.review_gate(review).ok),
        ("disable", "disabled" in disable),
    ]

    report = ["# Validation Report", "", *[status_line(name, ok) for name, ok in checks]]
    print("\n".join(report))
    if not all(ok for _, ok in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
