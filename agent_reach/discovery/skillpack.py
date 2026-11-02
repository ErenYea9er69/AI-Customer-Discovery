# -*- coding: utf-8 -*-
"""Skill pack loader. One set of skills feeds the pipeline prompts and the MCP server.

Skills live in folders: skills/<name>/SKILL.md plus skills/<name>/references/.
Each SKILL.md holds YAML frontmatter, a compact block between the markers
<!-- prompt:start --> and <!-- prompt:end -->, and longer notes after the block.
The pipeline injects only the compact block. The MCP server serves the whole file.
"""

from __future__ import annotations

import functools
import hashlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

PROMPT_START = "<!-- prompt:start -->"
PROMPT_END = "<!-- prompt:end -->"
STAGE_ORDER = ["router", "profile", "search", "qualify", "engage", "write", "safety"]
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,60}$")


class SkillError(RuntimeError):
    """The skill pack is missing or malformed."""


@dataclass
class Skill:
    name: str
    description: str
    version: str
    stage: str
    used_by: List[str]
    references: List[str]
    body: str
    prompt_block: str
    path: Path
    raw: str = field(default="", repr=False)

    def to_dict(self, with_body: bool = False) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "stage": self.stage,
            "used_by": self.used_by,
            "references": self.references,
            "prompt_words": len(self.prompt_block.split()),
        }
        if with_body:
            data["content"] = self.raw
        return data


@dataclass
class BannedTerms:
    hard: List[str]
    avoid: List[str]


@dataclass
class Example:
    title: str
    intent: str
    level: int
    thread: str
    good: str
    why_good: str
    bad: str
    why_bad: str


def skills_dir() -> Path:
    """Find the skills folder: env override, installed package data, then a source checkout."""
    override = os.getenv("AGENT_REACH_SKILLS_DIR")
    if override:
        return Path(override)
    here = Path(__file__).resolve()
    candidates = [
        here.parents[1] / "skillpack",   # inside the wheel (force-included)
        here.parents[2] / "skills",      # source checkout: repo/skills
    ]
    for cand in candidates:
        if cand.is_dir():
            return cand
    raise SkillError("Skill pack not found. Set AGENT_REACH_SKILLS_DIR or reinstall the package.")


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    text = text.lstrip("﻿")
    if not text.startswith("---"):
        raise SkillError("SKILL.md must start with frontmatter.")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise SkillError("Frontmatter is not closed.")
    meta = yaml.safe_load(parts[1]) or {}
    if not isinstance(meta, dict):
        raise SkillError("Frontmatter must be a mapping.")
    return meta, parts[2].lstrip("\n")


def extract_prompt_block(body: str) -> str:
    start = body.find(PROMPT_START)
    end = body.find(PROMPT_END)
    if start == -1 or end == -1 or end < start:
        return body.strip()
    return body[start + len(PROMPT_START):end].strip()


def _load_skill(folder: Path) -> Skill:
    path = folder / "SKILL.md"
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    name = str(meta.get("name") or "")
    if name != folder.name or not _NAME_RE.match(name):
        raise SkillError(f"Skill name '{name}' must equal its folder '{folder.name}'.")
    return Skill(
        name=name,
        description=str(meta.get("description") or ""),
        version=str(meta.get("version") or "0.0.0"),
        stage=str(meta.get("stage") or ""),
        used_by=[str(x) for x in (meta.get("used_by") or [])],
        references=[str(x) for x in (meta.get("references") or [])],
        body=body,
        prompt_block=extract_prompt_block(body),
        path=path,
        raw=raw,
    )


@functools.lru_cache(maxsize=4)
def _load_all(root: str) -> Dict[str, Skill]:
    base = Path(root)
    found: Dict[str, Skill] = {}
    for folder in sorted(p for p in base.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()):
        skill = _load_skill(folder)
        found[skill.name] = skill
    if not found:
        raise SkillError(f"No skills found in {base}.")
    return found


def reload() -> None:
    """Clear caches. Call after editing skill files in a running process."""
    _load_all.cache_clear()
    banned_terms.cache_clear()
    disclosure_phrases.cache_clear()
    examples.cache_clear()


def list_skills() -> List[Skill]:
    skills = list(_load_all(str(skills_dir())).values())
    order = {s: i for i, s in enumerate(STAGE_ORDER)}
    return sorted(skills, key=lambda s: (order.get(s.stage, 99), s.name))


def get_skill(name: str) -> Skill:
    skills = _load_all(str(skills_dir()))
    if name not in skills:
        raise KeyError(f"Unknown skill '{name}'. Known: {', '.join(sorted(skills))}")
    return skills[name]


def read_reference(name: str, reference: str) -> str:
    """Return one reference file. The path must stay inside the skill's references folder."""
    skill = get_skill(name)
    ref_dir = (skill.path.parent / "references").resolve()
    clean = reference.strip().replace("\\", "/")
    if clean.startswith("references/"):
        clean = clean[len("references/"):]
    target = (ref_dir / clean).resolve()
    if ref_dir not in target.parents or not target.is_file():
        raise KeyError(f"Unknown reference '{reference}' for skill '{name}'.")
    return target.read_text(encoding="utf-8")


def prompt(*names: str) -> str:
    """Join the compact blocks of the named skills for a system prompt."""
    chunks = []
    for name in names:
        skill = get_skill(name)
        chunks.append(f"## Skill: {skill.name}\n{skill.prompt_block}")
    return "\n\n".join(chunks)


# ── Reference parsers ─────────────────────────────────────────────────────────

def _copywriting_ref(filename: str) -> str:
    return read_reference("community-copywriting", filename)


def _parse_banned(text: str) -> Tuple[List[str], List[str]]:
    hard: List[str] = []
    avoid: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        tier, _, term = line.partition("|")
        term = term.strip().lower().replace("’", "'")
        if not term:
            continue
        if tier.strip() == "hard":
            hard.append(term)
        elif tier.strip() == "avoid":
            avoid.append(term)
    return hard, avoid


@functools.lru_cache(maxsize=4)
def banned_terms(include_user: bool = True) -> BannedTerms:
    hard, avoid = _parse_banned(_copywriting_ref("banned-ai-tells.txt"))
    if include_user:
        uh, ua = _parse_banned(_copywriting_ref("banned-user-list.txt"))
        hard += uh
        avoid += ua
    hard_set = list(dict.fromkeys(hard))
    avoid_set = [a for a in dict.fromkeys(avoid) if a not in hard_set]
    return BannedTerms(hard=hard_set, avoid=avoid_set)


@functools.lru_cache(maxsize=1)
def disclosure_phrases() -> List[str]:
    text = _copywriting_ref("disclosure-patterns.md")
    section = re.search(r"## Approved phrases\s*\n(.*?)(?:\n## |\Z)", text, re.S)
    if not section:
        raise SkillError("disclosure-patterns.md has no 'Approved phrases' section.")
    phrases = [m.group(1).strip() for m in re.finditer(r"^- (.+)$", section.group(1), re.M)]
    phrases = [p for p in phrases if "{product}" in p]
    if not phrases:
        raise SkillError("No approved disclosure phrases found.")
    return phrases


_EXAMPLE_HEAD = re.compile(r"^## Example \d+:\s*(.+)$", re.M)
_LABELS = ("Intent:", "Level:", "Thread:", "Good reply:", "Why it works:", "Bad reply:", "Why it fails:")


@functools.lru_cache(maxsize=1)
def examples() -> List[Example]:
    text = _copywriting_ref("examples.md")
    heads = list(_EXAMPLE_HEAD.finditer(text))
    out: List[Example] = []
    for i, head in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        block = text[head.end():end]
        fields: Dict[str, str] = {}
        current: Optional[str] = None
        buf: List[str] = []
        for line in block.splitlines():
            label = next((lb for lb in _LABELS if line.startswith(lb)), None)
            if label:
                if current is not None:
                    fields[current] = "\n".join(buf).strip()
                current = label
                buf = [line[len(label):].strip()]
            elif current is not None:
                buf.append(line)
        if current is not None:
            fields[current] = "\n".join(buf).strip()
        try:
            out.append(Example(
                title=head.group(1).strip(),
                intent=fields["Intent:"],
                level=int(fields["Level:"]),
                thread=fields["Thread:"],
                good=fields["Good reply:"],
                why_good=fields["Why it works:"],
                bad=fields["Bad reply:"],
                why_bad=fields["Why it fails:"],
            ))
        except (KeyError, ValueError) as exc:
            raise SkillError(f"examples.md: example '{head.group(1)}' is malformed: {exc}") from exc
    if not out:
        raise SkillError("examples.md has no examples.")
    return out


def few_shot(level: int, intent: Optional[str] = None, limit: int = 2) -> List[Example]:
    """Pick good examples near the wanted pitch level."""
    pool = examples()
    ranked = sorted(
        pool,
        key=lambda e: (abs(e.level - level), 0 if (intent and e.intent == intent) else 1),
    )
    return ranked[:limit]


def manifest() -> Dict[str, Any]:
    """Describe the pack: names, versions and a content hash per skill."""
    items = []
    total = hashlib.sha256()
    for skill in list_skills():
        folder = skill.path.parent
        digest = hashlib.sha256()
        for file in sorted(folder.rglob("*")):
            if file.is_file():
                digest.update(file.relative_to(folder).as_posix().encode())
                digest.update(file.read_bytes())
        total.update(digest.digest())
        items.append({**skill.to_dict(), "sha256": digest.hexdigest()})
    return {"pack_version": "1.0.0", "sha256": total.hexdigest(), "skills": items}
