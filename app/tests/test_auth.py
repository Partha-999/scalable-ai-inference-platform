from __future__ import annotations


def test_token_and_me(client):
    token = client.post(
        "/api/v1/auth/token",
        json={"subject": "user-1", "tenant_id": "tenant-a", "scopes": ["inference"]},
    ).json()["access_token"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": "tenant-a"},
    )
    assert response.status_code == 200
    assert response.json()["subject"] == "user-1"


def test_me_rejects_tenant_mismatch_with_explicit_reason(client):
    token = client.post(
        "/api/v1/auth/token",
        json={"subject": "user-1", "tenant_id": "tenant-a", "scopes": ["inference"]},
    ).json()["access_token"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": "tenant-b"},
    )
    assert response.status_code == 401
    assert "Tenant mismatch" in response.json()["detail"]
