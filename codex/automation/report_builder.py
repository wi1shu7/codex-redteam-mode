"""Dead code - retained for backward compatibility with external test suites.

TODO: Remove in next major version if no consumers surface.
"""
from __future__ import annotations

from typing import Sequence


def build_loop_report_lines(
    *,
    objective: str,
    selected_path: str,
    gate_names: Sequence[str],
    next_step: str,
) -> tuple[str, ...]:
    return (
        f"[report-objective:{objective or 'unset'}]",
        f"[report-path:{selected_path or 'unset'}]",
        f"[report-gates:{','.join(gate_names) or 'none'}]",
        f"[report-next:{next_step or 'unset'}]",
    )
