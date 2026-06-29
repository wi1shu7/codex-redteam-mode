from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ReportDecision:
    passed: bool
    missing: tuple[str, ...]
    checked: tuple[str, ...] = ()


class ReportGate:
    def __init__(self, *, strict: bool = False) -> None:
        self.strict = strict

    def check(self, artifact_types: Sequence[str]) -> ReportDecision:
        available = set(artifact_types)
        missing: list[str] = []
        if not ({"webfetch_summary", "browser_trace", "jadx_api_inventory", "ida_function_notes"} & available):
            missing.append("core_evidence")
        if not ({"reproduction_artifact", "generated_code", "local_harness"} & available):
            missing.append("reproduction_artifact")
        checked = ["core_evidence", "reproduction_artifact"]
        if self.strict:
            strict_checks: tuple[tuple[str, set[str]], ...] = (
                ("impact_proof", {"impact_proof", "impact_analysis"}),
                ("multi_id_or_parameter_check", {"multi_id_check", "parameter_check"}),
                ("scope_proof", {"scope_proof"}),
                ("false_positive_exclusion", {"false_positive_exclusion"}),
                ("parameter_portability", {"parameter_portability"}),
                ("cia_impact", {"cia_impact", "cia_assessment"}),
            )
            for name, accepted in strict_checks:
                checked.append(name)
                if not (accepted & available):
                    missing.append(name)
        return ReportDecision(passed=not missing, missing=tuple(missing), checked=tuple(checked))
