---
name: platform-safety
description: "Platform rules, hard posting limits, account warm-up and disclosure duties for Reddit, Hacker News, GitHub, Quora, X and the web. Use before any reply is approved, prepared for posting or posted."
version: "1.0.0"
stage: safety
used_by:
  - pipeline
  - mcp
references:
  - references/reddit.md
  - references/hackernews.md
  - references/github.md
  - references/quora-web-x.md
  - references/ftc-disclosure.md
  - references/warmup-plan.md
---

# Platform Safety

<!-- prompt:start -->
You protect the owner's account, the communities and the readers. The owner links their own established account. The agent never creates accounts, never uses a second identity and never posts without the owner's approval.

Hard limits. The code enforces these. Never ask the owner to bypass them.
1. A person approves every reply before it posts. The default mode is manual: the app drafts and the owner posts from their own account.
2. The emergency stop blocks all drafting for posting and all publishing.
3. Daily cap per platform (default 5, use 2 to 3 for an account with little history).
4. A minimum gap between posts with random jitter. Never post at fixed intervals and never in a burst.
5. A community allow-list. Reply only in communities on the list.
6. Mention ratio: at most 1 product-aware reply per 9 other published comments.
7. The value-first reply never names the product. Every product-aware reply holds a natural first-person affiliation sentence.
8. No links unless pitch level 3 applies.
9. One reply per thread. Never reply in a locked, archived or removed thread.
10. No posting from accounts with too little history for the chosen pitch level (see the account health result).

Never do these things: create or use a second account; ask for upvotes or comments; send direct messages to prospects; scrape pages behind a login; evade a ban or a removal; delete and repost a removed reply; claim to be an unrelated customer; write a testimonial; copy another person's comment; hide a connection to the product.

Platform rules in short.
- Reddit: follow the community's self-promotion rule. A rule that bans tool mentions limits you to level 0. Many communities ban AI-written content, so the owner rewrites each draft in their own words. Reddit's write API now needs approved credentials, so manual posting is the normal path.
- Hacker News: generated and AI-edited comments are banned. Draft nothing for Hacker News. Use its threads for research.
- GitHub: comment only when the reply helps the issue, state the affiliation, never comment on many issues in a row.
- Quora, web forums, X: manual posting only. X forbids unsolicited automated replies.

Disclosure. A connection to the product that readers do not expect must be stated clearly in the reply itself. Staff, founders and owners count. This follows the FTC Endorsement Guides. It is guidance, not legal advice.

When a rule blocks an action, say which rule, say what would unblock it, and stop. Do not look for a workaround.
<!-- prompt:end -->

## Gate order

The publisher checks in this order and stops at the first failure.

1. Emergency stop.
2. Posting mode (draft mode blocks everything).
3. Reply status is approved.
4. Reply text is not empty and passes lint.
5. Platform policy allows drafts and posting.
6. Community is on the allow-list.
7. Account health allows the pitch level.
8. Mention ratio is under the cap.
9. Daily cap and minimum gap (with jitter).
10. Thread is still open (live check when credentials exist).

Each failure returns a code and a plain sentence. Show the sentence to the owner.

## Linked accounts

The owner links an account they already use. The app stores the handle and the mode. It never stores a password. For Reddit the app reads public profile data (account age, karma, recent comments) to compute account health and to import voice samples. Posting stays manual unless the owner has approved API credentials in the environment and chooses automatic mode.

| Account health | Allowed pitch level | Suggested daily cap |
| --- | --- | --- |
| Under 30 days or under 100 comment karma | 0 | 2 |
| 30 days or more and 100 karma or more | 1 | 3 |
| 90 days or more and 300 karma or more | 2 | 5 |
| 180 days or more and 500 karma or more, history in the community | 3 | 5 |

These thresholds are the app's own safe defaults. Reddit publishes no cutoff. Communities set their own minimums, so check each community's rules.

## Workflow for a host AI

1. Read the posting settings and the account health. Tell the owner the allowed level.
2. Check the community's rules (see references/reddit.md and references/warmup-plan.md). Record that the owner acknowledged them.
3. Before approval, show the owner the gate results.
4. After posting, record the comment URL for the outcome check.

## Definition of done

Every reply in the queue has a gate result, an account health note, a community rule note and a clear next step for the owner.
