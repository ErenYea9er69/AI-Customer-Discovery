# -*- coding: utf-8 -*-
import time

from agent_reach.discovery.harvester import CommunityHarvester
from agent_reach.discovery.models import BusinessProfile
from agent_reach.discovery.orchestrator import DiscoveryOrchestrator, validate_platforms
from agent_reach.discovery.storage import DiscoveryStorage


class Meta:
    last_error = None

    def fetch(self, ids):
        now = time.time()
        return {i: {"id": i, "created_utc": now - 3 * 86400, "num_comments": 2, "is_self": True, "subreddit": "smallbusiness",
                    "title": "How do you chase unpaid invoices?", "selftext": "Customers ignore my reminders", "author": "bob"}
                for i in ids if i != "archived1"} | (
                {"archived1": {"id": "archived1", "created_utc": now - 200 * 86400, "archived": True, "is_self": True}}
                if "archived1" in ids else {})


class Verdict:
    provider, model, is_mock, is_configured = "stub", "x", False, True

    def complete_json(self, prompt, system_prompt=None):
        if "value_first" in prompt:
            return {"value_first": "Send a reminder on day 3.", "product_aware": "Try reminders. We built PlumbBooks."}
        if "sales lead" in prompt:
            return {"author_is_potential_customer": True, "post_type": "asking_for_help", "problem_fit": 28, "icp_match": 20,
                    "buying_intent": 16, "urgency": 10, "customer_problem": "Chasing unpaid invoices",
                    "evidence_quote": "Customers ignore my reminders", "reason": "Owner with the exact problem"}
        return {"queries": [], "subreddits": []}


def test_full_campaign_offline(tmp_path):
    storage = DiscoveryStorage(tmp_path / "e2e.db")
    profile = BusinessProfile(
        name="PlumbBooks", problems_solved=["Chasing unpaid customer invoices takes hours"],
        icp="Small plumbing business owners", competitors_and_alternatives=["QuickBooks"], confirmed=True)
    storage.save_business_profile(profile)

    orch = DiscoveryOrchestrator(storage)
    llm = Verdict()
    orch.llm = llm
    orch.qualifier.llm = llm
    orch.reply_generator.llm = llm
    orch.harvester = CommunityHarvester(storage, reddit_meta=Meta())

    def fake_search(query, limit):
        return [
            {"url": "https://www.reddit.com/r/smallbusiness/comments/live1/x/", "title": "t", "text": "Customers ignore my reminders"},
            {"url": "https://www.reddit.com/r/smallbusiness/comments/archived1/x/", "title": "t", "text": "old"},
        ]
    orch.harvester._search = fake_search
    orch.harvester._reddit_direct = lambda *a, **k: []

    campaign = orch.run_campaign_sync(platforms=["reddit"], max_leads=3)

    assert campaign.status == "completed"
    assert campaign.total_qualified == 1                      # one thread, deduped across queries
    assert campaign.diagnostics["rejected:archived"] >= 1     # archived thread was dropped and counted
    lead = storage.list_leads()[0]
    assert lead.judged_by == "llm" and lead.thread_health["num_comments"] == 2
    reply = storage.get_reply_by_lead_id(lead.id)
    assert reply and "Disclosure" in reply.product_aware


def test_platform_validation():
    assert validate_platforms(["REDDIT", "nope", "reddit"]) == ["reddit"]
    assert validate_platforms([]) == ["reddit", "hackernews", "web"]
