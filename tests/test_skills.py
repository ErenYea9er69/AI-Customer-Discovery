import subprocess
import sys
from pathlib import Path

from agent_reach.discovery import skillpack, voice
from agent_reach.discovery.models import ReplyPreferences

ROOT = Path(__file__).resolve().parent.parent


def test_validate_skills_script_passes():
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_skills.py")], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr


def test_tool_reference_is_current():
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "gen_tool_reference.py"), "--check"], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr


def test_every_skill_has_prompt_block_and_references():
    skills = skillpack.list_skills()
    assert {s.name for s in skills} >= {
        "customer-discovery", "business-intelligence", "community-search", "lead-qualification",
        "thread-engagement", "community-copywriting", "platform-safety",
    }
    for s in skills:
        assert s.prompt_block.strip()


def test_good_examples_pass_and_bad_examples_fail():
    prefs = ReplyPreferences()
    for ex in skillpack.examples():
        kind = "product_aware" if ex.level >= 2 else "value_first"
        good = voice.lint_reply(ex.good, kind=kind, product_name="Tidewatch", prefs=prefs, level=ex.level)
        assert good.passed, f"good example fails lint: {ex.title}: {good.issue_lines()}"
        bad_kind = "product_aware" if "Tidewatch" in ex.bad else "value_first"
        bad = voice.lint_reply(ex.bad, kind=bad_kind, product_name="Tidewatch", prefs=prefs, level=ex.level)
        assert not bad.passed, f"bad example passes lint: {ex.title}"


def test_banned_lists_load():
    banned = skillpack.banned_terms(True)
    assert len(banned.hard) > 100 and len(banned.avoid) > 10
    assert "delve" in banned.hard
    assert len(skillpack.disclosure_phrases()) >= 10
