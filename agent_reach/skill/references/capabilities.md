# Capability Scope

Read this reference when the user asks what can be fetched or how complete a result is. These are declared capabilities, not guaranteed results across all networks, accounts, and content.

## Three Tiers of Access

- **Public Attempt:** The agent's existing web tools, native tools, or public APIs may already satisfy the task; no browser installation or login required. Answer based on actual evidence obtained.
- **Reach Supplement:** Declared actions in the current release, see `agent-reach channels`. When configuration is needed, reuse saved sessions in the dedicated browser first; the user only logs in themselves when the chosen path strictly requires authentication.
- **Locally Verified:** Lists specific actions recently verified on this machine; installation, saved sessions, and network reachability do not equate to operational verification.

## Channel Capabilities

| Channel | Public Route to Try First | Reach Supplement & Boundaries |
|---|---|---|
| Reddit | Search, post body, top comments; public JSON endpoints include thread IDs | Community discovery, problem search, posts and comments extraction; full comment trees and user complaint analysis |
| X/Twitter | Public single posts from search; direct tweet status parsing (`x.com/<user>/status/<id>`) | Search, profile, tweet status, threads, and customer complaint extraction |
| Web | Agent's built-in web search and reader, Quora, Medium, blogs | Web search fallback (DuckDuckGo, Jina Reader), multi-engine scraping, Quora and forum complaint parsing |
| GitHub | Public repositories, READMEs, Issues/PRs | Repository search, issue/discussion reading with developer complaints and bug reports |
| YouTube | Search, titles, descriptions; native tools may fetch comments and subtitles | Search, video descriptions, subtitles, and tutorial workflow discussions |

When describing capabilities, deliver available public evidence as is. Authenticated browser sessions are used only when specifically needed.
