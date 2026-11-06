"""Drive the server over real stdio with the SDK's own client. Runs on SDK 1.x and 2.x."""
import asyncio
import json
import os
import sys
from pathlib import Path

import pytest
from conftest import PRODUCT_AWARE, VALUE_FIRST
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent


def payload(res):
    sc = getattr(res, "structuredContent", None) or getattr(res, "structured_content", None)
    if sc:
        return sc.get("result", sc) if isinstance(sc, dict) and set(sc) == {"result"} else sc
    return json.loads(res.content[0].text)


def attr(obj, *names):
    for n in names:
        v = getattr(obj, n, None)
        if v is not None:
            return v
    raise AttributeError(names)


async def session_flow(db):
    env = {k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")}
    env.update(AGENT_REACH_DISCOVERY_DB=str(db), PYTHONPATH=str(ROOT))
    params = StdioServerParameters(command=sys.executable, args=["-m", "agent_reach.mcp.server"], env=env, cwd=str(ROOT))
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            out = {}
            tools = (await s.list_tools()).tools
            out["tools"] = {t.name: t for t in tools}

            async def call(tool, /, **args):
                return payload(await s.call_tool(tool, args))

            out["status0"] = await call("reach_status")
            out["skill"] = await call("reach_get_skill", name="community-copywriting", reference="pitch-ladder.md")
            out["bad_skill"] = await call("reach_get_skill", name="nope")
            res = await s.read_resource("skill://community-search")
            out["resource"] = res.contents[0].text
            tpl = await s.list_resource_templates()
            out["templates"] = [attr(t, "uriTemplate", "uri_template") for t in attr(tpl, "resourceTemplates", "resource_templates")]
            out["prompts"] = [p.name for p in (await s.list_prompts()).prompts]
            out["profile"] = await call(
                "reach_get_or_create_profile", name="Acme", description="invoice reminders",
                problems_solved=["chasing late invoices"], pain_vocabulary=["clients pay late every month"],
                icp="freelance designers", confirm=True,
            )
            lead = await call(
                "reach_save_lead", title="t", url="https://www.reddit.com/r/freelance/comments/abc/x/", platform="reddit",
                community="r/freelance", customer_problem="p", evidence_quote="not in any stored thread",
                problem_fit=30, icp_match=25, buying_intent=20, urgency=15,
            )
            out["lead"] = lead
            hn = await call(
                "reach_save_lead", title="t", url="https://news.ycombinator.com/item?id=1", platform="hackernews",
                community="hn", customer_problem="p", evidence_quote="q", problem_fit=20, icp_match=15, buying_intent=10, urgency=5,
            )
            out["hn_lead"] = hn
            out["hn_context"] = await call("reach_get_reply_context", lead_id=hn["lead_id"])
            out["bad_save"] = await call("reach_save_reply", lead_id=lead["lead_id"], value_first="Great question — do this.")
            out["save"] = await call("reach_save_reply", lead_id=lead["lead_id"], value_first=VALUE_FIRST, product_aware=PRODUCT_AWARE.replace("Tidewatch", "Acme"))
            out["approve"] = await call("reach_approve_reply", reply_id=out["save"]["reply_id"], selected_version="value_first")
            out["publish_no_rules"] = await call("reach_publish_reply", reply_id=out["save"]["reply_id"])
            await call("reach_set_community_rules", community="r/freelance", self_promo="allowed")
            out["publish"] = await call("reach_publish_reply", reply_id=out["save"]["reply_id"])
            out["confirm"] = await call("reach_confirm_posted", reply_id=out["save"]["reply_id"], comment_url="https://reddit.com/c")
            out["export_bad"] = await call("reach_export_results", output_dir="/etc/agent_reach_test")
            out["settings"] = await call("reach_update_settings", emergency_stop=True)
            out["publish_stopped"] = await call("reach_publish_reply", reply_id=out["save"]["reply_id"])
            return out


@pytest.fixture(scope="module")
def flow(tmp_path_factory):
    return asyncio.run(session_flow(tmp_path_factory.mktemp("mcp") / "m.db"))


def test_surface(flow):
    names = set(flow["tools"])
    assert len(names) >= 30 and {"reach_status", "reach_get_reply_context", "reach_lint_reply", "reach_publish_reply"} <= names
    assert all(t.annotations is not None for t in flow["tools"].values())
    assert "skill://{name}" in flow["templates"]
    assert len(flow["prompts"]) == 0
    assert len(flow["resource"]) > 1000


def test_skills_served(flow):
    assert len(flow["skill"]["content"]) > 500
    assert "error" in flow["bad_skill"] and "available" in flow["bad_skill"]
    assert flow["status0"]["next_steps"][0].startswith("Build the business profile")


def test_server_side_scoring_cannot_be_inflated(flow):
    assert flow["lead"]["saved"] and flow["lead"]["classification"] == "relevant_potential"
    assert flow["lead"]["evidence_verified"] is False
    assert flow["hn_lead"]["reply_policy"] == "human_only"
    assert "error" in flow["hn_context"]


def test_reply_flow_and_gates(flow):
    assert flow["bad_save"]["saved"] is False and flow["bad_save"]["issues"]
    assert flow["save"]["saved"] and flow["approve"]["approved"]
    assert flow["publish_no_rules"]["code"] == "rules_not_read"
    assert flow["publish"]["success"] and flow["publish"]["action"] == "copy_and_open"
    assert flow["confirm"]["confirmed"]
    assert "error" in flow["export_bad"]
    assert flow["settings"]["posting"]["emergency_stop"] is True
    assert "error" in flow["publish_stopped"]
