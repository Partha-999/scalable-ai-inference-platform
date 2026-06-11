from __future__ import annotations

from functools import lru_cache


def detect_gpu_available() -> bool:
    try:
        import tensorflow as tf

        return bool(tf.config.list_physical_devices("GPU"))
    except Exception:
        return False


@lru_cache(maxsize=1)
def get_compute_device() -> str:
    return "gpu" if detect_gpu_available() else "cpu"
