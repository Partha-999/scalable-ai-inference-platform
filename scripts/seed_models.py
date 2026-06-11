from __future__ import annotations

from pathlib import Path

from app.services.model_registry import ModelRegistry

if __name__ == "__main__":
    registry = ModelRegistry.load(
        Path(__file__).resolve().parents[1] / "configs" / "model_registry.json"
    )
    print(
        {
            "model_count": len(registry.list_models()),
            "model_ids": list(registry.model_ids()),
        }
    )
