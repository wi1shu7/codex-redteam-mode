from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
import os
from pathlib import Path
import tomllib
from typing import Any


DEFAULT_PROFILE_FILES = {
    "gpt-5.6*": "Jailbreak.gpt-5.6.md",
    "gpt-5.5*": "Jailbreak.gpt-5.5.md",
    "gpt-5.4*": "Jailbreak.gpt-5.4.md",
    "default": "Jailbreak.default.md",
}


@dataclass(frozen=True)
class ModelPromptProfile:
    model: str
    profile: str
    filename: str
    content: str
    source: str

    def render(self) -> str:
        return (
            "[model-prompt-profile]\n"
            f"model={self.model}; profile={self.profile}; source={self.source}; file={self.filename}; "
            "delivery=model_instructions_file; layer=system"
        )


def extract_model(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    value = payload.get("model")
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _config_candidates(codex_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    explicit = os.environ.get("CODEX_REDTEAM_CONFIG", "").strip()
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.extend((codex_dir / "config.toml", codex_dir.parent / "config.toml"))
    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if codex_home:
        candidates.append(Path(codex_home).expanduser() / "config.toml")
    else:
        candidates.append(Path.home() / ".codex" / "config.toml")
    seen: set[str] = set()
    result: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        key = str(resolved).casefold()
        if key not in seen:
            seen.add(key)
            result.append(resolved)
    return result


def _read_configs(codex_dir: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for candidate in _config_candidates(codex_dir):
        if not candidate.is_file():
            continue
        try:
            value = tomllib.loads(candidate.read_text(encoding="utf-8-sig"))
        except (OSError, tomllib.TOMLDecodeError):
            continue
        if isinstance(value, dict):
            result.append(value)
    return result


def _model_from_config(configs: list[dict[str, Any]]) -> str:
    for config in configs:
        value = config.get("model")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _profile_mapping(configs: list[dict[str, Any]]) -> dict[str, str]:
    mapping = dict(DEFAULT_PROFILE_FILES)
    for config in configs:
        redteam = config.get("redteam")
        if not isinstance(redteam, dict):
            continue
        configured = redteam.get("model_prompt_profiles")
        if not isinstance(configured, dict):
            continue
        mapping.update(
            (str(pattern).strip(), filename.strip())
            for pattern, filename in configured.items()
            if str(pattern).strip() and isinstance(filename, str) and filename.strip()
        )
        break
    return mapping


def _select_profile(model: str, mapping: dict[str, str]) -> tuple[str, str]:
    normalized = model.casefold()
    patterns = sorted((key for key in mapping if key.casefold() != "default"), key=len, reverse=True)
    for pattern in patterns:
        lowered = pattern.casefold()
        if fnmatchcase(normalized, lowered) or (not any(char in lowered for char in "*?[") and normalized.startswith(lowered)):
            return pattern, mapping[pattern]
    return "default", mapping.get("default", DEFAULT_PROFILE_FILES["default"])


def resolve_model_prompt_profile(
    codex_dir: Path,
    payload: object = None,
) -> ModelPromptProfile:
    configs = _read_configs(codex_dir)
    model = extract_model(payload)
    source = "payload"
    if not model:
        model = os.environ.get("CODEX_MODEL", "").strip()
        source = "environment"
    if not model:
        model = _model_from_config(configs)
        source = "config"
    if not model:
        model = "unknown"
        source = "default"

    mapping = _profile_mapping(configs)
    profile, filename = _select_profile(model, mapping)
    safe_filename = Path(filename).name
    prompt_path = codex_dir / "prompts" / safe_filename
    if not prompt_path.is_file():
        profile = "default"
        safe_filename = Path(mapping.get("default", DEFAULT_PROFILE_FILES["default"])).name
        prompt_path = codex_dir / "prompts" / safe_filename
    if not prompt_path.is_file():
        safe_filename = DEFAULT_PROFILE_FILES["default"]
        prompt_path = codex_dir / "prompts" / safe_filename
    try:
        content = prompt_path.read_text(encoding="utf-8").strip()
    except OSError:
        content = ""
    return ModelPromptProfile(
        model=model,
        profile=profile,
        filename=safe_filename,
        content=content,
        source=source,
    )
