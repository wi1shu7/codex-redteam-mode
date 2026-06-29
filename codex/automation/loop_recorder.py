from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path


class LoopRecorder:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "decision-log.jsonl"

    def record_decision(self, *, run_id: str, iteration: int, decision: object) -> Path:
        payload = {
            "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "run_id": run_id,
            "iteration": iteration,
            "decision": asdict(decision) if is_dataclass(decision) else dict(decision),
        }
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        return self.path
