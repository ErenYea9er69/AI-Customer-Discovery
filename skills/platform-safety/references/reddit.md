# Reddit

Source labels: [official] means Reddit's published policy. [practice] means community practice. [vendor] means a vendor article. Rules change. Check the live pages before you rely on a line.

## Site-wide rules

- [official] The Content Policy asks for authentic participation. It bans spam, vote manipulation, ban evasion and fake engagement. Using several accounts to promote a product counts as serious abuse.
- [official] Reddiquette: it is fine to be a redditor with a website, not fine to be a website with a Reddit account.
- [practice] The 9 to 1 rule (about 90 percent of activity is not self-promotion) is advice from reddiquette-style guidance and marketing guides. It is not an official number. Some communities enforce a stricter ratio.
- [practice] Say so when you have a connection to a product you mention.

## Community rules

Every community sets its own self-promotion rule. Patterns reported by vendor guides in 2026 (re-check each one):

| Pattern | Example | Effect |
| --- | --- | --- |
| Promotion only in designated threads | r/startups | Level 0 or 1 outside the thread |
| Founder content allowed with conditions | r/SaaS | Level 2 with affiliation, no link |
| Tool pitches effectively banned | r/freelance, r/SEO | Level 0 only |
| Minimum karma or age | Many | Check account health |
| AI-written content banned | Many tech and hobby communities | The owner rewrites each reply |

### Rule check procedure

1. Open the community's sidebar or About page. Read every rule.
2. Open pinned posts and the wiki. Search "self promotion" and "AI".
3. Check the post flair rules and any weekly promotion thread.
4. Look at the last 10 removed or flagged posts if visible in the mod log or in comments about removals.
5. Record: self-promotion allowed (yes, thread only, no), links allowed in comments (yes, no), AI content allowed (yes, no), minimum karma or age.
6. The owner confirms the record. The app stores it as the rule acknowledgement and refuses to prepare a post for a community without one when the setting is on.

## API and posting

- [official] Reddit ended self-service API keys in November 2025. New OAuth credentials need approval under the Responsible Builder Policy. Reports say small commercial tools are usually rejected. Older credentials keep working while they follow the rules.
- [practice] Public JSON reading is limited to about 10 requests per minute without credentials.
- Result: the app reads with polite limits and posts manually by default. Automatic posting needs credentials the owner already holds, and it stays behind every gate.
- Browser automation can post, but it risks account bans and breaks often. The app does not use it.

## Detection signals

[vendor] heuristics from 2026 articles. Reddit publishes no thresholds.

- Young account with high volume.
- Karma mismatch: much karma elsewhere, little in the community.
- The same link posted in several communities.
- Replies at fixed intervals or in bursts.
- Uniform, polite, LinkedIn-like tone.
- Em dashes, bullets and a fixed structure.
- Shared phrasing across accounts.
- Several accounts from one device or network.
- Votes arriving in bursts after a post.

The app lowers these risks with real account history, one account, varied and short replies, jittered timing, caps and the mention ratio. No setting makes a spam pattern safe.

## Moderation changes

- [official] In August 2026 Reddit said it is building stronger built-in abuse prevention. It expects karma and account age to matter less over time. It expanded Rules Hub, an AI tool that applies a community's written rules to posts and comments.
- Result: a reply that follows the written rules gets removed less often. A reply that breaks a rule gets caught faster.

## After a removal or warning

Stop in that community. Do not repost. Read the rule. Lower the level for that community to 0. If a moderator asks a question, answer once and politely. Do not use another account.
