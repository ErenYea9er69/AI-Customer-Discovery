# -*- coding: utf-8 -*-
"""Voice analysis and the reply linter.

`analyze_samples` measures how the owner writes. `lint_reply` checks a draft
against the skill pack rules: banned words, dashes, markdown, links, product and
affiliation rules, length, near-duplicates and voice match. The same linter runs
in the pipeline and in the MCP server, so both apply the same gate.
"""

from __future__ import annotations

import functools
import re
import statistics
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence

from agent_reach.discovery import skillpack
from agent_reach.discovery.models import ReplyPreferences

_WORD_RE = re.compile(r"[A-Za-z0-9À-ɏ]+(?:'[A-Za-z]+)?")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U0001F000-\U0001F2FF☀-➿⭐⭕️]"
)
_CONTRACTION_RE = re.compile(r"\b\w+'(?:s|t|re|ve|ll|d|m)\b", re.I)
_NO_APOS_RE = re.compile(r"\b(dont|doesnt|didnt|cant|wont|isnt|arent|wasnt|im|ive|youre|theyre|thats|couldnt|shouldnt|wouldnt)\b", re.I)
_HEDGES = ("imo", "imho", "tbh", "fwiw", "ngl", "afaik", "iirc", "ymmv", "idk", "iirc", "honestly")
_URL_RE = re.compile(
    r"(https?://|www\.)\S+|\b[a-z0-9][a-z0-9-]*\.(?:com|io|app|co|net|org|dev|ai|so|me|xyz|sh|tech)\b(?:/\S*)?",
    re.I,
)
_DASH_RE = re.compile("[—–―]")
_MD_HEADER = re.compile(r"^\s{0,3}#{1,6}\s+\S", re.M)
_MD_BULLET = re.compile(r"^\s*(?:[-*•▪●])\s+\S", re.M)
_MD_NUMBERED = re.compile(r"^\s*\d{1,2}[.)]\s+\S", re.M)
_MD_BOLD = re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__")
_MD_CODE = re.compile(r"`[^`\n]+`|```")
_MD_TABLE = re.compile(r"^\s*\|.+\|\s*$", re.M)
_FLATTERY = re.compile(
    r"^\s*(?:(?:great|good|excellent|awesome|fantastic|interesting|fair|solid|smart)\s+(?:question|point|post|call|thinking)|"
    r"thanks? for (?:asking|sharing|posting|bringing)|absolutely[!,.]|definitely[!,.]|certainly[!,.]|of course[!,.]|sure[!,]|"
    r"love (?:this|that)|this is a (?:great|good|common|really|very|fantastic)|you(?:'re| are) (?:absolutely|totally|completely) right|"
    r"i(?:'d| would) (?:be happy|love|be glad) to|what a (?:great|good|fantastic))",
    re.I,
)
_AFFIL_PATTERNS = [
    re.compile(
        r"\b(?:i|we|i'm|im|i am|i've|my team|our team)\b[^.!?\n]{0,60}?\b"
        r"(?:built|build|builds|work|works|working|worked|founder|founded|co-?founder|make|makes|made|"
        r"run|runs|own|owns|maintain|maintains|wrote|write|started|behind|contribute|contributor|"
        r"affiliated|part of|maker|creator|dev|developer)\b",
        re.I,
    ),
    re.compile(r"\b(?:i'm|i am|im)\s+(?:on|in|with)\s+(?:the\s+)?[^.!?\n]{0,40}\bteam\b", re.I),
    re.compile(r"\bmy (?:day )?(?:job|work|role)\b", re.I),
    re.compile(r"\b(?:is|'s) mine\b", re.I),
    re.compile(r"\b(?:disclosure|full disclosure|bias warning|heads up)\b[^.\n]{0,40}\b(?:i|my|mine)\b", re.I),
    re.compile(r"\bmy (?:team|company|startup|project|tool|app)\b", re.I),
]
_BAD_DISCLOSURE = [
    (re.compile(r"#(?:ad|sponsored|partner|affiliate|promo)\b", re.I), "A hashtag is not a disclosure."),
    (re.compile(r"\bnot (?:sponsored|an ad|affiliated)\b", re.I), "Do not claim there is no connection."),
    (re.compile(r"\bdisclaimer\s*:", re.I), "A legal footer reads like a form. Use a natural sentence."),
    (
        re.compile(r"\b(?:as a|i'?m (?:just )?a|just a) (?:happy |long[- ]time |satisfied )?(?:user|customer)\b", re.I),
        "Do not pose as a customer.",
    ),
]
_CURLY = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', " ": " "})


# A model told "no em dash" often writes a spaced hyphen instead. It reads the same way.
_SPACED_DASH = re.compile(r"(?<=[A-Za-z0-9,.)\"'])\s+(?:-{1,2}|―)\s+(?=[A-Za-z\"'(])")
_GREETING = re.compile(r"^\s*(?:hi|hey|hello|hiya|yo|greetings|good (?:morning|afternoon|evening))\b[\s,!.]", re.I)

# Sentence frames that read as machine written. Each pattern runs on the reply text.
_SLOP_FRAMES = [
    (
        "contrast_frame",
        re.compile(
            r"\bnot (?:just|only|merely|simply)\b[^.!?\n]{0,70}\b(?:but|it's|it is)\b"
            r"|\b(?:it|this|that|which)(?:'s| is| isn't| is not)\s+not\s+(?:about\s+)?[^.!?\n]{1,60}[,;]\s*(?:it's|it is|but)\b"
            r"|\bisn't\s+(?:about\s+)?[^.!?\n]{1,60}[,;]\s*(?:it's|it is)\b"
            r"|\bnot because\b[^.!?\n]{1,70}[,;]\s*but because\b",
            re.I,
        ),
        "Remove the not-X-but-Y frame. State the point directly.",
    ),
    (
        "lead_in",
        re.compile(
            r"(?:^|[.!?]\s+|\n)(?:here(?:'s| is| are)\s+(?:the|why|what|how|a|my|some)\b"
            r"|the (?:catch|truth|reality|secret|trick|kicker|real (?:issue|problem|question))\s*(?:is|:)"
            r"|the thing is\b|short version\s*:|pro tip\b|quick tip\b|bonus(?: tip)?\s*:|spoiler\s*:|key (?:point|takeaway)\s*:"
            r"|let'?s (?:break|dive|unpack|walk|be honest|face it|get started|talk))",
            re.I,
        ),
        "Remove the lead-in line and say the point. Do not announce what comes next.",
    ),
    (
        "empathy_script",
        re.compile(
            r"\b(?:i (?:completely |totally |fully )?(?:understand|hear you|feel you)\b"
            r"|i'm sorry (?:to hear|you're|you are)"
            r"|that sounds (?:really |so |incredibly |super )?(?:frustrating|tough|stressful|difficult|hard|rough|painful)"
            r"|(?:totally|completely|perfectly|entirely) (?:understandable|valid|normal|natural)"
            r"|valid (?:concern|point|question|feeling)"
            r"|it's (?:totally |completely )?(?:understandable|natural|normal) to"
            r"|you(?:'re| are) not alone)",
            re.I,
        ),
        "Cut the scripted sympathy. If you share the experience, say what happened to you.",
    ),
    (
        "closing_question",
        re.compile(
            r"(?:what do you think|what are your thoughts|thoughts\?|have you (?:tried|considered)\b"
            r"|does that (?:help|make sense|work)|how does that sound|curious (?:to hear|what|how)|would love to hear"
            r"|any (?:other )?(?:questions|thoughts))[^.!?\n]*\?\s*$",
            re.I,
        ),
        "End on the last real point. A closing question that invites chat reads as engagement bait.",
    ),
]

_SERIAL_TRIPLE = re.compile(r"\b[\w'-]+(?: [\w'-]+){0,3}, [\w'-]+(?: [\w'-]+){0,3}, (?:and|or) [\w'-]+", re.I)
_MIRROR_CONTRAST = re.compile(r"\b[a-z']+, not (?:a |an |the |just )?[a-z']+\b", re.I)
_HEDGE_WORDS = re.compile(
    r"\b(?:might|perhaps|possibly|somewhat|arguably|seems? to|tends? to|in some cases|to some extent|generally|typically|often)\b",
    re.I,
)


# ── Text helpers ──────────────────────────────────────────────────────────────

def words_of(text: str) -> List[str]:
    return _WORD_RE.findall(text or "")


def sentences_of(text: str) -> List[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text or "") if s and s.strip()]


def normalize_text(text: str) -> str:
    """Fix mechanical slips: dashes, curly quotes, markdown marks. Never changes meaning."""
    out = (text or "").translate(_CURLY)
    out = _DASH_RE.sub(",", out)
    out = _SPACED_DASH.sub(", ", out)
    out = re.sub(r"\s*,\s*,", ",", out)
    out = re.sub(r"\s+,", ",", out)
    out = re.sub(r"\*\*([^*\n]+)\*\*", r"\1", out)
    out = re.sub(r"__([^_\n]+)__", r"\1", out)
    out = re.sub(r"`+", "", out)
    out = re.sub(r"^\s*#{1,6}\s+", "", out, flags=re.M)
    out = re.sub(r"^\s*(?:[-*•▪●])\s+", "", out, flags=re.M)
    out = re.sub(r"^\s*\d{1,2}[.)]\s+", "", out, flags=re.M)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def _std(values: Sequence[float]) -> float:
    return statistics.pstdev(values) if len(values) > 1 else 0.0


# ── Voice analysis ────────────────────────────────────────────────────────────

def analyze_samples(samples: Iterable[str]) -> Dict[str, Any]:
    """Measure the habits listed in references/voice-cloning.md. Returns a plain dict."""
    clean = [s.strip() for s in samples if s and len(words_of(s)) >= 3]
    n = len(clean)
    if n == 0:
        return {"n_samples": 0}
    reply_lens: List[int] = []
    sent_lens: List[int] = []
    openers: Counter = Counter()
    closers: Counter = Counter()
    low_starts = total_sents = 0
    contractions = no_apos = q = ex = ell = parens = commas = first_person = emojis = total_words = 0
    paragraphs: List[int] = []
    hedges: Counter = Counter()
    for text in clean:
        toks = words_of(text)
        total_words += len(toks)
        reply_lens.append(len(toks))
        paragraphs.append(max(1, len([p for p in re.split(r"\n\s*\n", text) if p.strip()])))
        sents = sentences_of(text)
        for s in sents:
            total_sents += 1
            sent_lens.append(len(words_of(s)))
            first = s.lstrip("\"'(").strip()
            if first[:1].isalpha() and first[:1].islower():
                low_starts += 1
            if s.endswith("?"):
                q += 1
            if "!" in s:
                ex += 1
            if "..." in s or "…" in s:
                ell += 1
            commas += s.count(",")
        contractions += len(_CONTRACTION_RE.findall(text))
        no_apos += len(_NO_APOS_RE.findall(text))
        parens += text.count("(")
        emojis += len(_EMOJI_RE.findall(text))
        first_person += len(re.findall(r"\b(?:i|i'm|i've|i'd|my|me)\b", text, re.I))
        for h in _HEDGES:
            c = len(re.findall(rf"\b{h}\b", text, re.I))
            if c:
                hedges[h] += c
        toks_l = [t.lower() for t in toks]
        if len(toks_l) >= 2:
            openers[" ".join(toks_l[:2])] += 1
            closers[" ".join(toks_l[-2:])] += 1
    per100 = (100.0 / total_words) if total_words else 0.0
    ts = max(1, total_sents)
    return {
        "n_samples": n,
        "avg_words_per_reply": round(statistics.mean(reply_lens), 1),
        "avg_sentence_words": round(statistics.mean(sent_lens), 1) if sent_lens else 0.0,
        "sentence_len_stdev": round(_std(sent_lens), 1),
        "lowercase_start_ratio": round(low_starts / ts, 2),
        "contraction_rate": round(contractions * per100, 2),
        "no_apostrophe_ratio": round(no_apos / (no_apos + contractions), 2) if (no_apos + contractions) else 0.0,
        "question_rate": round(q / ts, 2),
        "exclamation_rate": round(ex / ts, 2),
        "ellipsis_rate": round(ell / ts, 2),
        "emoji_rate": round(emojis * per100, 2),
        "paren_rate": round(parens * per100, 2),
        "comma_per_sentence": round(commas / ts, 2),
        "first_person_rate": round(first_person * per100, 2),
        "top_openers": [k for k, v in openers.most_common(3) if v > 1],
        "top_closers": [k for k, v in closers.most_common(3) if v > 1],
        "hedge_words": dict(hedges.most_common(4)),
        "paragraph_count_avg": round(statistics.mean(paragraphs), 1),
    }


def style_card_text(card: Dict[str, Any]) -> str:
    """Six readable lines for the prompt."""
    if not card or not card.get("n_samples"):
        return "No voice samples. Use a neutral, direct Reddit voice with normal capitalization."
    lines = [
        f"Typical reply length: about {card['avg_words_per_reply']:.0f} words in {card['paragraph_count_avg']:.1f} paragraph(s).",
        f"Sentences average {card['avg_sentence_words']:.0f} words with a spread of {card['sentence_len_stdev']:.0f}.",
        f"{int(card['lowercase_start_ratio'] * 100)}% of sentences start in lowercase. "
        f"Contractions: {card['contraction_rate']:.1f} per 100 words"
        + (" (often without apostrophes)." if card["no_apostrophe_ratio"] > 0.3 else "."),
        f"Questions {int(card['question_rate'] * 100)}% of sentences, exclamations {int(card['exclamation_rate'] * 100)}%, "
        f"ellipses {int(card['ellipsis_rate'] * 100)}%, emoji {card['emoji_rate']:.1f} per 100 words, "
        f"parentheses {card['paren_rate']:.1f} per 100 words.",
        "Hedges used: " + (", ".join(card["hedge_words"]) if card["hedge_words"] else "none") + ".",
        "Common openers: " + (", ".join(card["top_openers"]) if card["top_openers"] else "no fixed pattern") + ".",
    ]
    return "\n".join(lines)


def pick_samples(samples: Sequence[str], n: int = 3) -> List[str]:
    """Pick the most typical samples: closest in length to the median, long enough to show style."""
    usable = [s.strip() for s in samples if len(words_of(s)) >= 12]
    if not usable:
        return []
    med = statistics.median(len(words_of(s)) for s in usable)
    return sorted(usable, key=lambda s: abs(len(words_of(s)) - med))[:n]


# ── Linter ────────────────────────────────────────────────────────────────────

@dataclass
class LintIssue:
    code: str
    severity: str  # "error" blocks. "warn" informs.
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {"code": self.code, "severity": self.severity, "message": self.message}


@dataclass
class LintReport:
    issues: List[LintIssue] = field(default_factory=list)
    words: int = 0
    voice_score: Optional[int] = None

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def passed(self) -> bool:
        return not self.errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "words": self.words,
            "voice_score": self.voice_score,
            "issues": [i.to_dict() for i in self.issues],
        }

    def issue_lines(self) -> List[str]:
        return [f"{i.code}: {i.message}" for i in self.issues if i.severity == "error"]

    def _add(self, code: str, severity: str, message: str) -> None:
        self.issues.append(LintIssue(code, severity, message))


def _word_forms(word: str) -> List[str]:
    """The base word plus its regular inflections, so "unlock" also catches "unlocked" and "unlocking"."""
    forms = {word}
    if len(word) < 5 or not word.isalpha():
        return [word]
    if word.endswith("e"):
        forms |= {word + "s", word + "d", word[:-1] + "ing"}
    elif word.endswith("y") and word[-2] not in "aeiou":
        forms |= {word[:-1] + "ies", word[:-1] + "ied", word + "ing"}
    else:
        forms |= {word + "s", word + "es", word + "ed", word + "ing", word + "ly"}
    if word.endswith("le"):
        forms.add(word[:-1] + "y")
    return sorted(forms, key=len, reverse=True)


@functools.lru_cache(maxsize=2048)
def _term_regex(term: str) -> "re.Pattern[str]":
    parts = term.split()
    if len(parts) == 1:
        body = "(?:" + "|".join(re.escape(f) for f in _word_forms(parts[0])) + ")"
    else:
        body = r"\s+".join(re.escape(p) for p in parts)
    return re.compile(r"(?<![\w'])" + body + r"(?![\w'])", re.I)


def find_terms(text: str, terms: Iterable[str]) -> List[str]:
    low = (text or "").translate(_CURLY)
    return [t for t in terms if _term_regex(t).search(low)]


def count_terms(text: str, terms: Iterable[str]) -> int:
    low = (text or "").translate(_CURLY)
    return sum(len(_term_regex(t).findall(low)) for t in terms)


def has_affiliation(text: str) -> bool:
    return any(p.search(text or "") for p in _AFFIL_PATTERNS)


def count_product_mentions(text: str, product_name: str) -> int:
    name = (product_name or "").strip()
    if not name:
        return 0
    return len(re.findall(rf"(?<![\w]){re.escape(name)}(?![\w])", text or "", re.I))


def _shingles(text: str, size: int = 4) -> set:
    toks = [t.lower() for t in words_of(text)]
    return {" ".join(toks[i:i + size]) for i in range(max(0, len(toks) - size + 1))}


def similarity(a: str, b: str) -> float:
    sa, sb = _shingles(a), _shingles(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def lint_reply(
    text: str,
    *,
    kind: str = "value_first",
    product_name: str = "",
    prefs: Optional[ReplyPreferences] = None,
    level: Optional[int] = None,
    platform: str = "reddit",
    max_words: Optional[int] = None,
    previous: Sequence[str] = (),
) -> LintReport:
    """Check a draft. `kind` is value_first, product_aware or custom.

    `level` is the pitch level the draft aims for (0 to 3). Links are allowed at
    level 3 or when the preferences allow links.
    """
    prefs = prefs or ReplyPreferences()
    card = prefs.voice_card or {}
    report = LintReport()
    body = (text or "").strip()
    toks = words_of(body)
    report.words = len(toks)

    if not body:
        report._add("empty", "error", "The reply is empty.")
        return report

    if kind == "custom":
        kind = "product_aware" if count_product_mentions(body, product_name) else "value_first"
    if level is None:
        level = 2 if kind == "product_aware" else 0

    # Length
    limit = min(prefs.max_words, max_words) if max_words else prefs.max_words
    if len(toks) < prefs.min_words:
        report._add("too_short", "error", f"{len(toks)} words. Write at least {prefs.min_words}.")
    if len(toks) > limit:
        report._add("too_long", "error", f"{len(toks)} words. Keep it to {limit} or fewer.")

    # Words
    banned = skillpack.banned_terms(prefs.use_user_banned_list)
    hard = list(banned.hard) + [w.lower() for w in prefs.banned_words if w.strip()]
    avoid = list(banned.avoid)
    if prefs.strict_avoid:
        hard += avoid
        avoid = []
    hits = find_terms(body, hard)
    if hits:
        report._add("banned_word", "error", "Remove: " + ", ".join(sorted(set(hits))) + ". Rewrite the whole sentence in plain words. A synonym keeps the same tell.")
    avoid_hits = count_terms(body, avoid)
    if avoid_hits > prefs.avoid_budget:
        used = ", ".join(sorted(set(find_terms(body, avoid))))
        report._add("avoid_word_budget", "error", f"{avoid_hits} avoid-list words ({used}). Use at most {prefs.avoid_budget}.")

    # Punctuation and formatting
    if _DASH_RE.search(body):
        report._add("dash", "error", "Remove em and en dashes. Use a comma, a period or parentheses.")
    if _MD_HEADER.search(body) or _MD_BULLET.search(body) or _MD_NUMBERED.search(body) or _MD_TABLE.search(body):
        report._add("markdown_structure", "error", "Write plain paragraphs. No headers, bullets, numbered lists or tables.")
    if _MD_BOLD.search(body) or _MD_CODE.search(body):
        report._add("markdown_marks", "error", "Remove bold marks and backticks.")
    if any(ch in body for ch in "‘’“”"):
        report._add("curly_quotes", "warn", "Use straight quotes and apostrophes.")
    emoji_ok = prefs.allow_emoji if prefs.allow_emoji is not None else (card.get("emoji_rate", 0) or 0) > 0
    if _EMOJI_RE.search(body) and not emoji_ok:
        report._add("emoji", "error", "Remove emoji. The owner's voice does not use them.")
    if _SPACED_DASH.search(body):
        report._add("dash", "error", "Replace the spaced hyphen with a comma, a period or parentheses. It reads as a dash.")
    if _FLATTERY.search(body):
        report._add("flattery_opener", "error", "Start with the answer, not with praise or thanks.")
    opener_words = " ".join(str(o).lower() for o in (card.get("top_openers") or []))
    first_word = (words_of(body) or [""])[0].lower()
    if _GREETING.search(body) and first_word not in opener_words.split():
        report._add("greeting_opener", "error", "Start with the answer. No greeting.")
    for code, pattern, message in _SLOP_FRAMES:
        if pattern.search(body.translate(_CURLY)):
            report._add(code, "error", message)
    if body.count("!") > 1 and (card.get("exclamation_rate", 0) or 0) == 0:
        report._add("exclamations", "warn", "Use at most one exclamation mark.")

    # Links
    links_ok = level >= 3 or prefs.allow_links
    if _URL_RE.search(body) and not links_ok:
        report._add("link", "error", "Remove links and domain names. Links need pitch level 3.")

    # Product rules
    mentions = count_product_mentions(body, product_name)
    if product_name:
        if kind == "value_first" and mentions:
            report._add("product_in_value_first", "error", f"Do not name {product_name} in the value-first reply.")
        if kind == "product_aware":
            if mentions == 0:
                report._add("product_missing", "error", f"Name {product_name} once.")
            elif mentions > 1 and not (level >= 3 and mentions == 2 and _URL_RE.search(body)):
                report._add("product_repeated", "error", f"Name {product_name} once, not {mentions} times.")
            if mentions and not has_affiliation(body):
                report._add(
                    "affiliation_missing", "error",
                    "State your connection in a natural first-person sentence, for example 'I built X' or 'I work on X'.",
                )
    for pattern, message in _BAD_DISCLOSURE:
        if pattern.search(body):
            report._add("bad_disclosure", "error", message)
            break

    # Structure
    sents = sentences_of(body)
    if len(sents) >= 5:
        spread = _std([len(words_of(s)) for s in sents])
        if spread < 3.0:
            report._add("uniform_sentences", "warn", "Sentences are all about the same length. Let length follow the idea.")
    if len(sents) >= 4:
        starts = Counter((words_of(s) or [""])[0].lower() for s in sents)
        starts.pop("i", None)
        word, count = starts.most_common(1)[0] if starts else ("", 0)
        if count >= 3:
            report._add("repeated_openers", "warn", f"{count} sentences start with '{word}'. Change how some of them begin.")
    if len(_SERIAL_TRIPLE.findall(body)) >= 2:
        report._add("stacked_triples", "warn", "Two lists of three items. Give one or two items where the topic allows it.")
    if len(_MIRROR_CONTRAST.findall(body)) >= 2:
        report._add("mirror_contrast", "warn", "Two 'X, not Y' contrasts. Keep the one that carries the point.")
    if len(_HEDGE_WORDS.findall(body)) >= 3:
        report._add("hedge_stack", "warn", "Three or more hedges. Hedge once, where you are unsure.")
    if body.count(";") >= 2:
        report._add("semicolons", "warn", "Semicolons are rare in forum comments. Use periods.")
    contraction_rate = card.get("contraction_rate")
    if len(toks) >= 40 and not _CONTRACTION_RE.search(body) and (contraction_rate is None or contraction_rate >= 1):
        report._add("stiff_register", "warn", "No contractions in a long reply. People write don't and it's.")
    lowercase_voice = (card.get("lowercase_start_ratio") or 0) > 0.6
    if len(toks) >= 40 and not lowercase_voice:
        has_digit = bool(re.search(r"\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|fifty|hundred|dozen)\b", body, re.I))
        has_name = bool(re.search(r"(?<=[a-z,] )[A-Z][A-Za-z0-9]{2,}", body)) or bool(_URL_RE.search(body))
        if not has_digit and not has_name:
            report._add("no_specific_detail", "warn", "Add one concrete detail from the thread or the product facts: a number, a tool, a step.")
    if kind == "product_aware" and product_name and sents:
        if count_product_mentions(sents[0], product_name):
            report._add("product_first_sentence", "warn", "The product appears in the first sentence. Answer first, then mention it.")

    # Near duplicates of earlier replies
    for old in previous:
        if old and similarity(body, old) >= 0.5:
            report._add("too_similar", "error", "This reply repeats the wording of an earlier reply. Write it differently.")
            break

    report.voice_score = _voice_score(body, toks, sents, card, report) if card.get("n_samples", 0) >= 3 else None
    if report.voice_score is not None and report.voice_score < 60:
        report._add("voice_mismatch", "warn", f"Voice match is {report.voice_score}/100. Compare with the owner's samples.")
    return report


def _voice_score(body: str, toks: List[str], sents: List[str], card: Dict[str, Any], report: LintReport) -> int:
    score = 100
    avg = card.get("avg_words_per_reply") or 0
    if avg:
        ratio = len(toks) / avg
        if ratio < 0.5 or ratio > 1.7:
            score -= 25
    lows = sum(1 for s in sents if s[:1].isalpha() and s[:1].islower())
    low_ratio = lows / max(1, len(sents))
    if abs(low_ratio - (card.get("lowercase_start_ratio") or 0)) > 0.5:
        score -= 20
    if (card.get("emoji_rate") or 0) == 0 and _EMOJI_RE.search(body):
        score -= 15
    if (card.get("exclamation_rate") or 0) == 0 and "!" in body:
        score -= 10
    if (card.get("contraction_rate") or 0) > 1 and not _CONTRACTION_RE.search(body):
        score -= 10
    avg_s = card.get("avg_sentence_words") or 0
    if avg_s and sents:
        mine = statistics.mean(len(words_of(s)) for s in sents)
        if abs(mine - avg_s) > 0.4 * avg_s:
            score -= 10
    return max(0, score)
