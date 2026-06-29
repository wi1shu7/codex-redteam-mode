"""Evidence artifact dataclass — structured evidence from redteam operations.

Provides a typed container for evidence artifacts produced during security
testing. Each artifact carries a type tag, content payload, and verifiability
flag used by the ExitGate to decide whether the domain objective is met.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvidenceArtifact:
    """A single piece of evidence produced by a redteam operation.

    Attributes:
        type: Category tag (e.g., "sqli", "xss", "rce", "info_disclosure").
        content: Raw evidence payload (HTTP request/response, screenshot path, etc).
        verifiable: Whether this artifact alone is sufficient proof of exploitation.
        metadata: Additional context (timestamps, tool used, severity, etc).
    """

    type: str = ""
    content: str = ""
    verifiable: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain dict for JSON persistence."""
        result: dict[str, Any] = {
            "type": self.type,
            "content": self.content,
            "verifiable": self.verifiable,
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result


def parse_artifacts(raw_list: Any) -> list[EvidenceArtifact]:
    """Parse a list of raw dicts (or EvidenceArtifact instances) into typed artifacts.

    Tolerant of malformed entries — skips items that cannot be parsed.
    """
    if not isinstance(raw_list, (list, tuple)):
        return []
    results: list[EvidenceArtifact] = []
    for item in raw_list:
        if isinstance(item, EvidenceArtifact):
            results.append(item)
        elif isinstance(item, dict):
            results.append(EvidenceArtifact(
                type=item.get("type", ""),
                content=item.get("content", ""),
                verifiable=bool(item.get("verifiable", False)),
                metadata=item.get("metadata", {}),
            ))
    return results
