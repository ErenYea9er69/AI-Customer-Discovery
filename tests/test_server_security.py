# -*- coding: utf-8 -*-
import os
from fastapi.testclient import TestClient

from agent_reach.server.app import app
from agent_reach.discovery.storage import DiscoveryStorage
from agent_reach.discovery.orchestrator import DiscoveryOrchestrator
from agent_reach.discovery.models import PostingSettings


def test_settings_secret_masking(tmp_path):
    from agent_reach.server import app as server_mod

    test_storage = DiscoveryStorage(tmp_path / "test_sec.db")
    server_mod.storage = test_storage
    server_mod.orchestrator = DiscoveryOrchestrator(test_storage)
    client = TestClient(app)

    # 1. Save sensitive credentials
    save_resp = client.post(
        "/api/settings",
        json={
            "posting_settings": {
                "reddit_username": "marketing_bot",
                "reddit_password": "super_secret_password_123",
                "reddit_client_id": "client_id_abc",
                "reddit_client_secret": "secret_oauth_xyz",
                "github_token": "ghp_RealSecretToken12345",
            },
            "llm_settings": {
                "provider": "openai",
                "api_key": "sk-real-secret-key-12345",
            },
        },
    )
    assert save_resp.status_code == 200

    # 2. Query settings - must NOT return plaintext secrets
    get_resp = client.get("/api/settings")
    assert get_resp.status_code == 200
    data = get_resp.json()

    posting = data["posting_settings"]
    assert posting["reddit_password"] == "***"
    assert posting["reddit_client_secret"] == "***"
    assert posting["github_token"] == "***"
    assert posting["has_reddit_password"] is True
    assert posting["has_reddit_client_secret"] is True
    assert posting["has_github_token"] is True
    assert "super_secret_password_123" not in get_resp.text
    assert "secret_oauth_xyz" not in get_resp.text
    assert "ghp_RealSecretToken12345" not in get_resp.text

    llm = data["llm_settings"]
    assert llm["api_key"] == "***"
    assert llm["has_api_key"] is True
    assert "sk-real-secret-key-12345" not in get_resp.text

    # 3. Update with masked secrets without losing real stored values
    update_resp = client.post(
        "/api/settings",
        json={
            "posting_settings": {
                "daily_limit": 20,
                "reddit_password": "***",
                "github_token": "***",
            }
        },
    )
    assert update_resp.status_code == 200

    # Verify underlying storage preserved the real secret values
    stored_posting = test_storage.get_setting("posting_settings")
    assert stored_posting["reddit_password"] == "super_secret_password_123"
    assert stored_posting["github_token"] == "ghp_RealSecretToken12345"
    assert stored_posting["daily_limit"] == 20


def test_campaign_input_validation(tmp_path):
    client = TestClient(app)

    # Reject max_leads > 100
    resp_huge = client.post(
        "/api/campaigns/launch",
        json={"name": "Attack", "max_leads": 1000000},
    )
    assert resp_huge.status_code == 422

    # Reject max_leads < 1
    resp_zero = client.post(
        "/api/campaigns/launch",
        json={"name": "Attack", "max_leads": 0},
    )
    assert resp_zero.status_code == 422


def test_api_key_authentication(monkeypatch, tmp_path):
    from agent_reach.server import app as server_mod

    test_storage = DiscoveryStorage(tmp_path / "test_auth.db")
    server_mod.storage = test_storage
    server_mod.orchestrator = DiscoveryOrchestrator(test_storage)

    client = TestClient(app)

    monkeypatch.setenv("AGENT_REACH_API_KEY", "prod-secret-token-999")

    # Unauthenticated request must fail with 401
    unauth_resp = client.get("/api/settings")
    assert unauth_resp.status_code == 401

    # Request with invalid API key must fail with 401
    bad_key_resp = client.get("/api/settings", headers={"X-API-Key": "wrong-token"})
    assert bad_key_resp.status_code == 401

    # Request with valid X-API-Key must succeed
    auth_resp = client.get("/api/settings", headers={"X-API-Key": "prod-secret-token-999"})
    assert auth_resp.status_code == 200

    # Request with valid Authorization: Bearer must succeed
    bearer_resp = client.get("/api/settings", headers={"Authorization": "Bearer prod-secret-token-999"})
    assert bearer_resp.status_code == 200



def test_global_api_protection(monkeypatch, tmp_path):
    from agent_reach.server import app as server_mod

    test_storage = DiscoveryStorage(tmp_path / "test_global_auth.db")
    server_mod.storage = test_storage
    server_mod.orchestrator = DiscoveryOrchestrator(test_storage)
    client = TestClient(app)

    monkeypatch.setenv("AGENT_REACH_API_KEY", "secure-api-key-456")

    # All /api/ routes require auth
    assert client.get("/api/profile").status_code == 401
    assert client.get("/api/campaigns").status_code == 401
    assert client.get("/api/leads").status_code == 401
    assert client.get("/api/export").status_code == 401

    # With key, they work
    auth_headers = {"X-API-Key": "secure-api-key-456"}
    assert client.get("/api/profile", headers=auth_headers).status_code == 200
    assert client.get("/api/campaigns", headers=auth_headers).status_code == 200
    assert client.get("/api/leads", headers=auth_headers).status_code == 200


def test_rate_limiting_enforcement(tmp_path):
    from agent_reach.server import app as server_mod
    from agent_reach.server.app import rate_limiter

    test_storage = DiscoveryStorage(tmp_path / "test_rl.db")
    server_mod.storage = test_storage
    server_mod.orchestrator = DiscoveryOrchestrator(test_storage)
    client = TestClient(app)

    # Exhaust rate limit for extract-url
    for _ in range(15):
        rate_limiter.check("extract_url:testclient", max_requests=15)

    # Next request should be rejected with 429
    resp = client.post("/api/profile/extract-url", json={"url": "https://example.com"})
    assert resp.status_code == 429
    assert "Rate limit exceeded" in resp.json()["detail"]


def test_loopback_cross_site_protection(tmp_path):
    from agent_reach.server import app as server_mod
    test_storage = DiscoveryStorage(tmp_path / "test_cs.db")
    server_mod.storage = test_storage
    server_mod.orchestrator = DiscoveryOrchestrator(test_storage)
    client = TestClient(app)

    # 1. Untrusted cross-origin header should be rejected with 403
    evil_resp = client.get("/api/profile", headers={"Origin": "https://attacker-site.com"})
    assert evil_resp.status_code == 403
    assert "Cross-origin request" in evil_resp.json()["detail"]

    # 2. Sec-Fetch-Site: cross-site should be rejected with 403
    cross_site_resp = client.get("/api/profile", headers={"Sec-Fetch-Site": "cross-site"})
    assert cross_site_resp.status_code == 403
    assert "Cross-site requests" in cross_site_resp.json()["detail"]

    # 3. Trusted local origin should succeed
    local_resp = client.get("/api/profile", headers={"Origin": "http://localhost:5173"})
    assert local_resp.status_code == 200
