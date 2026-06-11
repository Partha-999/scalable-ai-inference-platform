from __future__ import annotations

import hashlib


def assign_variant(tenant_id: str, model_group: str, variants: list[str]) -> str:
    if not variants:
        raise ValueError("variants must not be empty")
    seed = hashlib.sha256(f"{tenant_id}:{model_group}".encode("utf-8")).hexdigest()
    return variants[int(seed, 16) % len(variants)]
