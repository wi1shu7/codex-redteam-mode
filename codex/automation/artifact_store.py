from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_type: str
    path: str


class ArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._records: list[ArtifactRecord] = self._load_existing()

    def _load_existing(self) -> list[ArtifactRecord]:
        records: list[ArtifactRecord] = []
        for path in sorted(self.root.glob("*.json")):
            name = path.stem
            parts = name.split("-", 1)
            artifact_type = parts[1] if len(parts) == 2 and parts[0].isdigit() else name
            records.append(ArtifactRecord(artifact_type=artifact_type, path=str(path)))
        return records

    def _sanitize_type(self, artifact_type: str) -> str:
        base = str(artifact_type or "artifact").replace("\\", "/").split("/")[-1]
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", base).strip("._-")
        return safe or "artifact"

    def save(self, artifact_type: str, payload: object) -> Path:
        safe_type = self._sanitize_type(artifact_type)
        path = self.root / f"{len(self._records) + 1:03d}-{safe_type}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._records.append(ArtifactRecord(artifact_type=safe_type, path=str(path)))
        return path

    def list_types(self) -> tuple[str, ...]:
        return tuple(record.artifact_type for record in self._records)
