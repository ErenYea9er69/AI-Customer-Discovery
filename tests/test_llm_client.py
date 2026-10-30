# -*- coding: utf-8 -*-
from agent_reach.discovery.llm_client import LLMClient


def test_llm_client_mock():
    client = LLMClient(provider="mock")

    # Business profile extraction
    resp = client.complete_json("Extract business profile from website text...")
    assert "name" in resp
    assert resp["name"] == "SuperTask"
    assert "problems_solved" in resp
    assert len(resp["problems_solved"]) > 0
    assert "facts" in resp
    assert "inferences" in resp

    # Search queries
    queries_resp = client.complete_json("Generate search queries for ICP...")
    assert "queries" in queries_resp
    assert len(queries_resp["queries"]) > 0

    # Lead qualification
    qual_resp = client.complete_json("Qualify lead conversation...")
    assert "score" in qual_resp
    assert qual_resp["score"] >= 90
    assert "score_breakdown" in qual_resp
    assert qual_resp["score_breakdown"]["total"] == qual_resp["score"]

    # Reply generation
    reply_resp = client.complete_json("Generate replies for qualified lead...")
    assert "value_first" in reply_resp
    assert "product_aware" in reply_resp
    assert "disclosure" in reply_resp

