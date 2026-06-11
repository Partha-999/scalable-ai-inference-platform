from __future__ import annotations


def test_models_endpoint(client):
    token = client.post(
        "/api/v1/auth/token", json={"subject": "user-1", "tenant_id": "tenant-a"}
    ).json()["access_token"]
    response = client.get(
        "/api/v1/inference/models",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": "tenant-a"},
    )
    assert response.status_code == 200
    assert len(response.json()["models"]) >= 2
