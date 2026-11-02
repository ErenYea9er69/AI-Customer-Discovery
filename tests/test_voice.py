from agent_reach.discovery import voice
from agent_reach.discovery.models import ReplyPreferences

GOOD = ("I stopped chasing by hand when I set one rule: every invoice gets a due date and a reminder three days "
        "before it. A calendar repeat does it for free. It breaks down past twenty clients.")


def codes(text, **kw):
    return {i.code for i in voice.lint_reply(text, **kw).errors}


def test_clean_text_passes():
    assert voice.lint_reply(GOOD).passed


def test_dash_markdown_banned_and_flattery():
    assert "dash" in codes(GOOD + " Also — this.")
    assert "markdown_structure" in codes("- one\n- two\n" + GOOD)
    assert "banned_word" in codes("You should delve into this. " + GOOD)
    assert "flattery_opener" in codes("Great question! " + GOOD)


def test_links_need_level_three():
    text = GOOD + " See https://acme.test for more."
    assert "link" in codes(text)
    assert "link" not in codes(text, kind="product_aware", product_name="Acme", level=3)


def test_product_rules():
    assert "product_in_value_first" in codes(GOOD + " Acme does it.", product_name="Acme")
    assert "product_missing" in codes(GOOD, kind="product_aware", product_name="Acme")
    assert "affiliation_missing" in codes(GOOD + " Acme handles that.", kind="product_aware", product_name="Acme")
    assert voice.lint_reply(GOOD + " I built Acme for that stage.", kind="product_aware", product_name="Acme").passed
    assert "bad_disclosure" in codes(GOOD + " Disclosure: I am affiliated with Acme. #ad", kind="product_aware", product_name="Acme")


def test_length_and_repeat():
    assert "too_short" in codes("Short one here.")
    assert "too_long" in codes(GOOD * 8)
    assert "too_similar" in codes(GOOD, previous=[GOOD])


def test_owner_banned_words_and_avoid_budget():
    prefs = ReplyPreferences(banned_words=["twenty"])
    assert "banned_word" in codes(GOOD, prefs=prefs)


def test_voice_card_and_score():
    samples = ["honestly i just use a spreadsheet and a calendar reminder, works fine till you hit around twenty clients and then it falls apart"] * 4
    card = voice.analyze_samples(samples)
    assert card["n_samples"] == 4 and card["lowercase_start_ratio"] > 0.5
    prefs = ReplyPreferences(voice_card=card)
    report = voice.lint_reply("Honestly I would never do this. I use a rigid system, a detailed process, and a very long checklist for everything I do each week, every single month.", prefs=prefs)
    assert report.voice_score is not None
