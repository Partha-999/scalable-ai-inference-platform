from __future__ import annotations


def test_live_and_ready(client):
    assert client.get("/api/v1/health/live").status_code == 200
    assert (
        client.get(
            "/api/v1/health/ready", headers={"X-Tenant-ID": "tenant-a"}
        ).status_code
        == 200
    )
