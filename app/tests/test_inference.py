from __future__ import annotations

import base64


def test_text_inference(client):
    token = client.post(
        "/api/v1/auth/token", json={"subject": "user-1", "tenant_id": "tenant-a"}
    ).json()["access_token"]
    response = client.post(
        "/api/v1/inference/text",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": "tenant-a"},
        json={"text": "I love this product", "use_ab_test": False},
    )
    assert response.status_code == 200
    assert response.json()["label"] == "positive"


def test_qa_inference(client):
    token = client.post(
        "/api/v1/auth/token", json={"subject": "user-1", "tenant_id": "tenant-a"}
    ).json()["access_token"]
    response = client.post(
        "/api/v1/inference/text",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": "tenant-a"},
        json={
            "question": "What is the capital of France?",
            "context": "Paris is the capital and most populous city of France.",
            "model_id": "text-qa-v1",
        },
    )
    assert response.status_code == 200
    assert response.json()["label"] == "Paris"


def test_vision_inference_upload(client):
    token = client.post(
        "/api/v1/auth/token", json={"subject": "user-1", "tenant_id": "tenant-a"}
    ).json()["access_token"]
    image_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO3X3b0AAAAASUVORK5CYII="
    )
    response = client.post(
        "/api/v1/inference/vision/upload",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": "tenant-a"},
        files={"file": ("sample.png", image_bytes, "image/png")},
    )
    assert response.status_code == 200
