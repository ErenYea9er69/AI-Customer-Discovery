# -*- coding: utf-8 -*-
"""Tests for FastMCP server tools and endpoints."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent_reach.discovery.models import BusinessProfile, DiscoveredItem
from agent_reach.discovery.storage import DiscoveryStorage
from agent_reach.mcp.server import (
    create_mcp_server,
    reach_control_dashboard,
    reach_export_results,
    reach_get_or_create_profile,
    reach_get_settings,
    reach_harvest_threads,
    reach_list_leads,
    reach_plan_queries,
    reach_run_autonomous_batch,
    reach_save_lead,
    reach_save_reply,
    reach_update_settings,
)


@pytest.fixture
def mock_storage(tmp_path: Path):
    db_file = tmp_path / "test_mcp.db"
    return DiscoveryStorage(db_file)


def test_mcp_profile_create_and_get(mock_storage):
    with patch("agent_reach.mcp.server.get_storage", return_value=mock_storage):
        prof = reach_get_or_create_profile(
            name="AlphaLead",
            description="AI tool for discovery",
            problems_solved=["Manual lead search", "High SDR cost"],
            icp="SaaS founders",
        )
        assert prof["name"] == "AlphaLead"
        assert "Manual lead search" in prof["problems_solved"]

        # Fetch without recreating
        fetched = reach_get_or_create_profile()
        assert fetched["id"] == prof["id"]
        assert fetched["name"] == "AlphaLead"


def test_mcp_plan_queries(mock_storage):
    with patch("agent_reach.mcp.server.get_storage", return_value=mock_storage):
        reach_get_or_create_profile(
            name="AlphaLead",
            problems_solved=["Manual lead search"],
            icp="SaaS founders",
        )
        queries = reach_plan_queries(platforms=["reddit", "web"])
        assert len(queries) > 0
        assert any("reddit" in q["platform"] for q in queries)


def test_mcp_save_and_list_lead(mock_storage):
    with patch("agent_reach.mcp.server.get_storage", return_value=mock_storage):
        saved = reach_save_lead(
            title="Looking for better lead tools",
            url="https://reddit.com/r/SaaS/comments/lead123",
            platform="reddit",
            community="r/SaaS",
            customer_problem="Need automated outreach",
            pain_point_category="manual_work",
            buying_intent="High",
            urgency="High",
            score=88,
            classification="high_potential",
            evidence="Budget is $200/mo ready to spend.",
        )
        assert saved["score"] == 88
        assert saved["id"] is not None

        leads = reach_list_leads(min_score=80)
        assert len(leads) == 1
        assert leads[0]["id"] == saved["id"]
        assert leads[0]["score"] == 88


def test_mcp_save_reply(mock_storage):
    with patch("agent_reach.mcp.server.get_storage", return_value=mock_storage):
        saved_lead = reach_save_lead(
            title="Need outreach tool",
            url="https://reddit.com/r/SaaS/comments/lead456",
            platform="reddit",
            community="r/SaaS",
            customer_problem="Manual outreach",
            pain_point_category="manual_work",
            score=82,
        )
        rep = reach_save_reply(
            lead_id=saved_lead["id"],
            value_first="Here is a proven framework for automated outreach...",
            product_aware="We built AlphaLead to automate this exact workflow...",
        )
        assert rep["lead_id"] == saved_lead["id"]
        assert "AlphaLead" in rep["product_aware"]


def test_mcp_settings_flow(mock_storage):
    with patch("agent_reach.mcp.server.get_storage", return_value=mock_storage):
        curr = reach_get_settings()
        assert "discovery_mode" in curr

        updated = reach_update_settings(
            discovery_mode="built_in_auto",
            default_output_format="both",
            default_min_score=75,
        )
        assert updated["discovery_mode"] == "built_in_auto"
        assert updated["default_min_score"] == 75

        curr2 = reach_get_settings()
        assert curr2["discovery_mode"] == "built_in_auto"


def test_mcp_export_results(mock_storage, tmp_path):
    with patch("agent_reach.mcp.server.get_storage", return_value=mock_storage):
        reach_save_lead(
            title="Top Lead",
            url="https://reddit.com/r/SaaS/comments/lead999",
            platform="reddit",
            community="r/SaaS",
            customer_problem="Manual outreach",
            pain_point_category="manual_work",
            score=95,
        )
        out_dir = tmp_path / "exports"
        res = reach_export_results(formats="both", output_dir=str(out_dir), min_score=90)
        assert "markdown" in res
        assert "json" in res
        assert Path(res["markdown"]).exists()
        assert Path(res["json"]).exists()


@patch("agent_reach.discovery.harvester.CommunityHarvester.execute_query")
def test_mcp_run_autonomous_batch(mock_execute_query, mock_storage):
    mock_item = DiscoveredItem(
        url="https://reddit.com/r/SaaS/comments/batch1",
        platform="reddit",
        community="r/SaaS",
        author="founder_joe",
        title="Looking for a tool to find customer leads on reddit",
        content="I hate having to manually scroll forums every day. Anyone know a better tool? Willing to pay for software.",
    )
    mock_execute_query.return_value = [mock_item]

    with patch("agent_reach.mcp.server.get_storage", return_value=mock_storage):
        reach_get_or_create_profile(
            name="AlphaLead",
            description="Reddit lead discovery tool",
            problems_solved=["finding leads on reddit"],
            icp="SaaS founders",
        )
        res = reach_run_autonomous_batch(
            queries=["looking for a tool to find customer leads on reddit"],
            platforms=["reddit"],
            min_score=50,
            max_leads=2,
        )
        assert res["total_qualified"] >= 1
        assert len(res["leads"]) >= 1
        assert res["leads"][0]["url"] == mock_item.url


@patch("agent_reach.mcp.server.ensure_dashboard_running")
@patch("agent_reach.mcp.server.is_port_in_use")
def test_mcp_control_dashboard(mock_is_port, mock_ensure):
    mock_is_port.return_value = True
    mock_ensure.return_value = {"status": "already_running", "url": "http://127.0.0.1:8000", "port": 8000}

    res_status = reach_control_dashboard(action="status", port=8000)
    assert res_status["is_running"] is True
    assert res_status["url"] == "http://127.0.0.1:8000"

    res_launch = reach_control_dashboard(action="launch", port=8000, open_browser=False)
    assert res_launch["status"] == "already_running"
