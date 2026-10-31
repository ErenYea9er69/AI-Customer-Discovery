# -*- coding: utf-8 -*-
"""Tests for MCP helpers: reports, file exports, settings, and dashboard process management."""

import json
import socket
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent_reach.discovery.models import (
    BusinessProfile,
    LeadClassification,
    LeadQualification,
    ScoreBreakdown,
)
from agent_reach.discovery.storage import DiscoveryStorage
from agent_reach.mcp.helpers import (
    ensure_dashboard_running,
    export_results_files,
    generate_markdown_report,
    get_or_init_mcp_settings,
    is_port_in_use,
    update_mcp_settings,
)


@pytest.fixture
def temp_storage(tmp_path: Path) -> DiscoveryStorage:
    db_file = tmp_path / "test_discovery.db"
    return DiscoveryStorage(db_file)


@pytest.fixture
def sample_lead() -> LeadQualification:
    return LeadQualification(
        id="lead-test-1",
        discovered_item_id="item-test-1",
        url="https://reddit.com/r/SaaS/comments/xyz123",
        platform="reddit",
        community="r/SaaS",
        title="Looking for alternative to ExpensiveTool for customer outreach",
        customer_problem="Current tooling is overpriced and lacks automated outreach",
        pain_point_category="high_cost",
        purchase_intent="High",
        urgency="High",
        score=85,
        classification="high_potential",
        confidence=0.9,
        published_at="2026-10-30T10:00:00Z",
        excerpt="We need to switch this month because pricing doubled.",
        profile_match="Matches B2B founder ICP looking for cost effective outreach",
        product_fit_explanation="Product offers automated outreach at fixed flat price",
        score_breakdown=ScoreBreakdown(
            icp_match=25,
            problem_fit=25,
            buying_intent=18,
            urgency=10,
            recency=7,
            total=85,
            explanation="Strong intent and clear problem fit",
        ),
        author="saas_builder",
        evidence="We need to switch this month because pricing doubled.",
        recommended_action="Engage with value-first advice and mention migration tool",
    )


def test_generate_markdown_report(sample_lead):
    profile = BusinessProfile(
        id="prof-1",
        name="ReachOut Pro",
        description="AI Customer Discovery",
        main_product_or_service="Automated lead discovery engine",
        icp="B2B Founders and Marketers",
        problems_solved=["Slow lead generation", "High outreach tool cost"],
    )
    md = generate_markdown_report([sample_lead], profile)
    assert "# 🎯 Agent Reach — Customer Discovery Report" in md
    assert "ReachOut Pro" in md
    assert "Looking for alternative to ExpensiveTool" in md
    assert "85/100" in md
    assert "reddit" in md
    assert "https://reddit.com/r/SaaS/comments/xyz123" in md


def test_generate_markdown_report_formula_escape(sample_lead):
    sample_lead.title = "=cmd|' /C calc'!A0"
    md = generate_markdown_report([sample_lead], None)
    # Ensure formula injection is safely escaped
    assert "'=cmd|" in md or "\\=cmd|" in md or "`=cmd|" in md


def test_export_results_files(temp_storage, sample_lead, tmp_path):
    temp_storage.save_lead(sample_lead)

    # Test "both"
    result = export_results_files(
        storage=temp_storage,
        output_dir=tmp_path / "out",
        formats="both",
        min_score=50,
    )
    assert "markdown" in result
    assert "json" in result
    assert Path(result["markdown"]).exists()
    assert Path(result["json"]).exists()

    # Validate JSON content
    with open(result["json"], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["id"] == "lead-test-1"
        assert data[0]["score"] == 85


def test_get_or_init_mcp_settings_defaults(temp_storage):
    settings = get_or_init_mcp_settings(temp_storage)
    assert settings["discovery_mode"] in ("host_driven", "built_in_auto")
    assert settings["default_output_format"] in ("markdown", "json", "both")
    assert settings["default_min_score"] == 70
    assert settings["emergency_stop"] is False


def test_update_mcp_settings(temp_storage):
    updated = update_mcp_settings(
        temp_storage,
        {"discovery_mode": "built_in_auto", "default_output_format": "markdown", "default_min_score": 80},
    )
    assert updated["discovery_mode"] == "built_in_auto"
    assert updated["default_output_format"] == "markdown"
    assert updated["default_min_score"] == 80

    re_read = get_or_init_mcp_settings(temp_storage)
    assert re_read["discovery_mode"] == "built_in_auto"
    assert re_read["default_output_format"] == "markdown"
    assert re_read["default_min_score"] == 80


def test_is_port_in_use():
    with socket.socket(socket.AF_IPv2 if hasattr(socket, "AF_IPv2") else socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
        assert is_port_in_use(port, "127.0.0.1") is True

    # Port released
    assert is_port_in_use(port, "127.0.0.1") is False


@patch("agent_reach.mcp.helpers.is_port_in_use")
@patch("webbrowser.open")
def test_ensure_dashboard_running_already_active(mock_open, mock_port_in_use):
    mock_port_in_use.return_value = True
    info = ensure_dashboard_running(port=8000, host="127.0.0.1", open_browser=True)
    assert info["status"] == "already_running"
    assert info["url"] == "http://127.0.0.1:8000"
    mock_open.assert_called_once_with("http://127.0.0.1:8000")
