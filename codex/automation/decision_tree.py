from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionPath:
    path: str
    priority: str
    reason: str
    required_capabilities: tuple[str, ...]
    expected_artifacts: tuple[str, ...]


def select_decision_path(objective: str, *, phase: str = "general") -> DecisionPath:
    text = f"{objective} {phase}".casefold()
    if "apk" in text or "android" in text:
        return DecisionPath(
            path="apk-api-inventory",
            priority="high",
            reason="apk or android markers found",
            required_capabilities=("apk_decompile", "code_generation"),
            expected_artifacts=("jadx_api_inventory",),
        )
    if any(marker in text for marker in ("login", "token", "jwt", "session", "oauth", "saml")):
        return DecisionPath(
            path="auth-boundary",
            priority="high",
            reason="login/token/session markers found",
            required_capabilities=("page_fetch", "browser_automation"),
            expected_artifacts=("webfetch_summary", "browser_trace"),
        )
    if any(marker in text for marker in ("api", "graphql", "endpoint", "schema")):
        return DecisionPath(
            path="api-boundary",
            priority="high",
            reason="api markers found",
            required_capabilities=("page_fetch", "code_generation"),
            expected_artifacts=("webfetch_summary", "generated_code"),
        )
    if phase in {"reverse", "network"} or any(marker in text for marker in ("binary", "protocol", "firmware", "ida")):
        return DecisionPath(
            path="binary-protocol",
            priority="medium",
            reason="binary or protocol markers found",
            required_capabilities=("binary_reverse", "code_generation"),
            expected_artifacts=("ida_function_notes",),
        )
    return DecisionPath(
        path="recon-baseline",
        priority="medium",
        reason="default low-noise recon path",
        required_capabilities=("page_fetch",),
        expected_artifacts=("webfetch_summary",),
    )
