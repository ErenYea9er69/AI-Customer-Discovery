# Capability Scope

Read this reference when the user asks what can be fetched or how complete a result is. These are declared capabilities, not guaranteed results across all networks, accounts, and content.

## Three Tiers of Access

- **Public Attempt:** The agent's existing web tools, native tools, or public APIs may already satisfy the task; no browser installation or login required. Answer based on actual evidence obtained.
- **Reach Supplement:** Declared actions in the current release, see `agent-reach channels`. When configuration is needed, reuse saved sessions in the dedicated browser first; the user only logs in themselves when the chosen path strictly requires authentication.
- **Locally Verified:** Lists specific actions recently verified on this machine; installation, saved sessions, and network reachability do not equate to operational verification.

## Channel Capabilities

| Channel | Public Route to Try First | Reach Supplement & Boundaries |
|---|---|---|
| GitHub | Public repositories, READMEs, Issues/PRs | Repository search, repo/issue/PR reading with comments; private permissions determined separately |
| YouTube | Search, titles, descriptions; native tools may fetch some comments and subtitles | search/read/subtitle/transcribe; no unified comments action; track lists are not subtitle bodies; audio transcription depends on corresponding tools |
| Bilibili | Search, video descriptions; some public endpoints return comments and thread IDs | search/read/hot/subtitle; no unified comments action; subtitles vary by video and access route |
| Reddit | Search, post body, top comments; public JSON endpoints include thread IDs | Browser search/read/subreddit; login depends on chosen path; full comment tree not guaranteed; posting comments not supported in reach |
| X/Twitter | Public single posts from search; official embeds return full text | search/profile/tweets/thread; readable single posts do not guarantee readable reply streams; full comment tree not guaranteed |
| Xiaohongshu | Public lists/indexes may have note IDs, authors, titles; do not guess empty fields | search/read/comments; text descriptions, top-level comments, and loaded replies; never claim to understand images/videos |
| Instagram | Shallow profile and index information; HTML app shells are not post content | search (users), profile, posts (user post descriptions); no unified comments action; never claim to understand images/videos |
| Facebook | Search indexes or HTML snippets; snippets may be truncated | search/profile; no unified post detail or comment action; do not treat snippets as full text |
| LinkedIn | Public job searches, public JD reading | jobs/read tries public web first; specify opencli to use site tools directly; readable job descriptions not guaranteed for all jobs |
| Boss Zhipin | Job summaries in search indexes | search/read job listings and JDs; never guess salary digits from encoded strings; detail fallback per channel declaration |
| V2EX | Topics, post bodies, and public replies | hot/node/read/user; scope determined by API response; hidden or deleted replies not guaranteed |
| Xueqiu | Public stock quotes and index data | quote/search/hot_posts/hot_stocks; quote and community routes verified separately |
| Web | Agent's built-in web search and reader | Reach web search/read as anonymous fallback; snippets, shells, and captcha verification pages must not be treated as full text |
| Xiaoyuzhou | Podcast episode titles, show notes | transcribe full episode to text; requires user-provided Groq Key (`agent-reach configure groq-key`) |

When describing capabilities after login, say "can enable/attempt the above browser actions", never "supports all comments after login". When the user skips login, deliver available public evidence as is.
