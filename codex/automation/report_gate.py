from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ReportDecision:
    passed: bool
    missing: tuple[str, ...]


class ReportGate:
    def check(self, artifact_types: Sequence[str]) -> ReportDecision:
        available = set(artifact_types)
        missing: list[str] = []
        if not ({"webfetch_summary", "browser_trace", "jadx_api_inventory", "ida_function_notes"} & available):
            missing.append("core_evidence")
        if not ({"reproduction_artifact", "generated_code", "local_harness"} & available):
            missing.append("reproduction_artifact")
        return ReportDecision(passed=not missing, missing=missing)
