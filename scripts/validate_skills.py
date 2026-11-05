#!/usr/bin/env python3
"""Validate the shared skill pack. CI runs this on every push.

Checks:
  1. every SKILL.md has the required frontmatter and a prompt block
  2. every listed reference file exists, and no file sits unlisted
  3. no em or en dashes in any skill file
  4. every `reach_*` and `ceo_*` tool named in a skill exists in the MCP server
  5. every good example passes the linter and every bad example fails it
  6. skills/manifest.json matches the content (use --write to refresh it)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SKILLS = ROOT / "skills"
STAGES = {"router", "profile", "search", "qualify", "engage", "write", "safety"}
DASHES = ("—", "–")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Rewrite skills/manifest.json")
    ns = parser.parse_args()
    import os

    os.environ["AGENT_REACH_SKILLS_DIR"] = str(SKILLS)
    from agent_reach.discovery import skillpack, voice
    from agent_reach.discovery.models import ReplyPreferences

    errors: list[str] = []
    skills = skillpack.list_skills()
    if len(skills) < 8:
        errors.append(f"Expected at least 8 skills, found {len(skills)}.")

    for skill in skills:
        folder = skill.path.parent
        if skill.stage not in STAGES:
            errors.append(f"{skill.name}: stage '{skill.stage}' is not one of {sorted(STAGES)}.")
        if not skill.prompt_block.strip():
            errors.append(f"{skill.name}: empty prompt block.")
        listed = {str(Path(r)) for r in skill.references}
        for ref in skill.references:
            if not (folder / ref).is_file():
                errors.append(f"{skill.name}: listed reference missing: {ref}")
        on_disk = {str(p.relative_to(folder)) for p in (folder / "references").glob("*") if p.is_file()}
        for extra in sorted(on_disk - listed):
            errors.append(f"{skill.name}: reference not listed in frontmatter: {extra}")

    for path in SKILLS.rglob("*"):
        if path.is_file() and path.suffix in (".md", ".txt", ".json"):
            text = path.read_text(encoding="utf-8")
            if any(d in text for d in DASHES):
                errors.append(f"{path.relative_to(ROOT)}: contains an em or en dash.")

    from agent_reach.mcp import server

    # The validator sees every tool because it never calls create_mcp_server(), which hides specialist tools.
    tool_names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    for path in SKILLS.rglob("*.md"):
        if path.name == "tool-reference.md":
            continue
        for name in set(re.findall(r"\b(?:reach|ceo)_[a-z_]+\b", path.read_text(encoding="utf-8"))):
            if name not in tool_names:
                errors.append(f"{path.relative_to(ROOT)}: names unknown tool {name}.")

    prefs = ReplyPreferences()
    for ex in skillpack.examples():
        kind = "product_aware" if ex.level >= 2 else "value_first"
        good = voice.lint_reply(ex.good, kind=kind, product_name="Tidewatch", prefs=prefs, level=ex.level)
        if not good.passed:
            errors.append(f"Example '{ex.title}': good reply fails lint: {good.issue_lines()}")
        bad_kind = "product_aware" if "Tidewatch" in ex.bad else "value_first"
        bad = voice.lint_reply(ex.bad, kind=bad_kind, product_name="Tidewatch", prefs=prefs, level=ex.level)
        if bad.passed:
            errors.append(f"Example '{ex.title}': bad reply passes lint.")

    manifest = skillpack.manifest()
    mpath = SKILLS / "manifest.json"
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if ns.write:
        mpath.write_bytes(text.encode("utf-8"))
        print(f"wrote {mpath}")
    elif not mpath.exists() or mpath.read_text(encoding="utf-8").replace("\r\n", "\n") != text:
        errors.append("skills/manifest.json is stale. Run: python scripts/validate_skills.py --write")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"ok: {len(skills)} skills, {len(skillpack.examples())} examples, {len(tool_names)} tools")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
