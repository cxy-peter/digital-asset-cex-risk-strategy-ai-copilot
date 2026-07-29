from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class Settings(BaseModel):
    project_root: Path
    data_dir: Path
    output_dir: Path
    config_dir: Path
    knowledge_dir: Path
    random_seed: int = 20260728
    use_llm: bool = False
    openai_model: str = "gpt-4.1-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""

    @classmethod
    def load(cls, project_root: str | Path | None = None) -> "Settings":
        root = Path(project_root or Path(__file__).resolve().parents[2]).resolve()
        return cls(
            project_root=root,
            data_dir=(root / os.getenv("RISK_COPILOT_DATA_DIR", "data/demo")).resolve(),
            output_dir=(root / os.getenv("RISK_COPILOT_OUTPUT_DIR", "outputs")).resolve(),
            config_dir=(root / "configs").resolve(),
            knowledge_dir=(root / "data/knowledge").resolve(),
            use_llm=os.getenv("USE_LLM", "false").lower() == "true",
            openai_model=os.getenv("OPENAI_COMPATIBLE_MODEL", "gpt-4.1-mini"),
            openai_base_url=os.getenv("OPENAI_COMPATIBLE_BASE_URL", "https://api.openai.com/v1"),
            openai_api_key=os.getenv("OPENAI_COMPATIBLE_API_KEY", ""),
        )


def load_yaml(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def dump_yaml(value: Any, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(value, fh, allow_unicode=True, sort_keys=False)
