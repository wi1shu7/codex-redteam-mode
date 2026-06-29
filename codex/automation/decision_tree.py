from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .recon_workflow import RECON_EXIT_ARTIFACTS, RECON_MIN_CAPABILITIES


@dataclass(frozen=True)
class DecisionPath:
    path: str
    priority: str
    reason: str
    required_capabilities: tuple[str, ...]
    expected_artifacts: tuple[str, ...]


# ---------------------------------------------------------------------------
# Recon-specific context flags (set by controller when target_parser fires)
# ---------------------------------------------------------------------------

class ReconContext:
    """Lightweight context passed from controller to influence decision routing."""

    __slots__ = ("bare_target", "recon_profile_ready", "cve_candidates", "cve_patched")

    def __init__(
        self,
        *,
        bare_target: bool = False,
        recon_profile_ready: bool = False,
        cve_candidates: Sequence[str] = (),
        cve_patched: bool = False,
    ):
        self.bare_target = bare_target
        self.recon_profile_ready = recon_profile_ready
        self.cve_candidates = tuple(cve_candidates)
        self.cve_patched = cve_patched


def select_decision_path(
    objective: str,
    *,
    phase: str = "general",
    recon_ctx: ReconContext | None = None,
) -> DecisionPath:
    """Select the decision path based on objective, phase, and optional recon context.

    Routing priority (plan section 11.6):
      1. bare_target → recon-intake
      2. recon_profile_ready → cve-lookup
      3. cve_no_candidate → route-by-evidence (fall through to normal matching)
      4. cve_patched → route-by-evidence (fall through to normal matching)
      5. cve_applicable → cve-validation
      6. Normal keyword matching (apk, auth, api, binary)
      7. Default: recon-baseline
    """
    # --- Recon context overrides ---
    if recon_ctx is not None:
        # 1. bare_target → recon-intake
        if recon_ctx.bare_target and not recon_ctx.recon_profile_ready:
            return DecisionPath(
                path="recon-intake",
                priority="high",
                reason="bare target detected, initiating recon intake",
                required_capabilities=RECON_MIN_CAPABILITIES,
                expected_artifacts=RECON_EXIT_ARTIFACTS,
            )

        # 2. recon_profile_ready → cve-lookup
        if recon_ctx.recon_profile_ready and not recon_ctx.cve_candidates:
            return DecisionPath(
                path="cve-lookup",
                priority="high",
                reason="recon profile complete, proceeding to CVE lookup",
                required_capabilities=("cve_search", "code_generation"),
                expected_artifacts=("cve_candidate_list",),
            )

        # 5. cve_applicable → cve-validation
        if recon_ctx.cve_candidates and not recon_ctx.cve_patched:
            return DecisionPath(
                path="cve-validation",
                priority="high",
                reason="CVE candidates found, validating applicability",
                required_capabilities=("page_fetch", "code_generation"),
                expected_artifacts=("cve_validation_result",),
            )

        # 3 & 4: cve_no_candidate or cve_patched → fall through to normal matching

    # --- Normal keyword-based matching ---
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
