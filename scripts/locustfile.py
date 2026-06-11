from __future__ import annotations

import base64
from locust import HttpUser, task, between

class InferenceUser(HttpUser):
    # Short delay to generate high RPS
    wait_time = between(0.01, 0.05)

    @task(4)
    def infer_text(self):
        headers = {
            "X-API-Key": "dev-api-key",
            "X-Tenant-ID": "tenant-a",
        }
        self.client.post(
            "/api/v1/inference/text",
            headers=headers,
            json={
                "text": "I love this product",
                "model_id": "text-sentiment-v1",
                "use_ab_test": False,
            },
            name="/inference/text"
        )

    @task(1)
    def infer_vision(self):
        headers = {
            "X-API-Key": "dev-api-key",
            "X-Tenant-ID": "tenant-a",
        }
        # Blank 32x32 image base64
        img_b64 = "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAAAKUlEQVR4nO3NMQEAAAjDMMC/52ECvlRA00nqs3m9AwAAAAAAAAAAgMMWx/EDPS4YA2MAAAAASUVORK5CYII="
        self.client.post(
            "/api/v1/inference/vision",
            headers=headers,
            json={
                "image_base64": img_b64,
                "model_id": "vision-vit-v1",
                "use_ab_test": False,
            },
            name="/inference/vision"
        )
