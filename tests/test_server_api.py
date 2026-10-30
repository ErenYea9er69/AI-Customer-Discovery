# -*- coding: utf-8 -*-
from fastapi.testclient import TestClient

from agent_reach.server.app import app

client = TestClient(app)


def test_server_api_flow():
    # 1. Profile extraction
    resp = client.post(
        "/api/profile/extract-manual",
        json={
            "name": "SuperTask",
            "description": "SuperTask is an AI developer tool that automates GitHub issue triage and backlog deduplication.",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["profile"]["name"] == "SuperTask"

    # Confirm profile
    confirm_resp = client.post("/api/profile/confirm")
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["profile"]["confirmed"] is True

    # 2. Launch campaign
    camp_resp = client.post(
        "/api/campaigns/launch",
        json={"name": "Test API Campaign", "platforms": ["reddit"], "max_leads": 5},
    )
    assert camp_resp.status_code == 200
    camp_id = camp_resp.json()["campaign_id"]
    assert camp_id is not None

    # Check campaigns list
    list_camp = client.get("/api/campaigns")
    assert list_camp.status_code == 200
    assert len(list_camp.json()["campaigns"]) > 0

    # 3. List leads
    leads_resp = client.get("/api/leads")
    assert leads_resp.status_code == 200
    leads = leads_resp.json()["leads"]
    assert len(leads) > 0
    first_lead = leads[0]
    lead_id = first_lead["id"]

    # Lead details
    detail_resp = client.get(f"/api/leads/{lead_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["lead"]["id"] == lead_id

    # 4. Reply workflow
    reply_resp = client.get(f"/api/replies/{lead_id}")
    assert reply_resp.status_code == 200
    reply = reply_resp.json()["reply"]
    assert reply["value_first"] != ""
    assert reply["product_aware"] != ""

    # Approve reply
    approve_resp = client.post(
        f"/api/replies/{lead_id}/approve",
        json={"edited_reply": "Reviewed and customized answer.", "selected_version": "custom"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["reply"]["status"] == "approved"

    # Configure posting settings to whitelist the lead's community
    client.post(
        "/api/settings",
        json={
            "posting_settings": {
                "mode": "manual",
                "daily_limit": 10,
                "allowed_communities": [first_lead["community"], "r/programming", "r/startups"],
                "emergency_stop": False,
            }
        },
    )

    # Publish reply (copy fallback)
    publish_resp = client.post(f"/api/replies/{lead_id}/publish")
    assert publish_resp.status_code == 200
    assert publish_resp.json()["success"] is True

    # 5. Analytics
    analytics_resp = client.get("/api/analytics")
    assert analytics_resp.status_code == 200
    assert "common_complaints" in analytics_resp.json()

    # 6. Export (JSON & CSV)
    exp_json = client.get("/api/export?format=json")
    assert exp_json.status_code == 200
    assert "application/json" in exp_json.headers["content-type"]

    exp_csv = client.get("/api/export?format=csv")
    assert exp_csv.status_code == 200
    assert "text/csv" in exp_csv.headers["content-type"]

    # 7. Settings
    settings_resp = client.get("/api/settings")
    assert settings_resp.status_code == 200
    assert "posting_settings" in settings_resp.json()

    update_set = client.post(
        "/api/settings",
        json={"posting_settings": {"mode": "manual", "daily_limit": 10, "emergency_stop": False}},
    )
    assert update_set.status_code == 200


def test_static_dashboard_mounted():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "<title>" in resp.text
