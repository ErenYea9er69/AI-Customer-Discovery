# Pitch ladder

The ladder sets how much product appears in a reply. Higher levels need more trust from the community and from the account's history. The settings hold a maximum level per account and per community. The reply never exceeds the maximum.

| Level | What the reply contains | Link | Affiliation sentence |
| --- | --- | --- | --- |
| 0 | Help only. No product, no category. | No | Not needed |
| 1 | The approach or the kind of tool, no brand. | No | Not needed |
| 2 | The brand once, as one option, with the limit of the product. | No | Required |
| 3 | The brand once plus a link. | Yes | Required |

## Level 0: help only

Use when the post is a rant, a discussion, a community that bans tool mentions, a young account, or a thread where the product is a weak fit.
Example: "Batch the reminders on one weekday with a template. The first hour feels wasteful, after that it takes ten minutes."

## Level 1: describe the kind of tool

Use when the person asks for a tool but the community bans brand names, or when the account is still building history.
Example: "Look for a reminder tool that reads your invoice list and emails on a schedule, not a full accounting suite. At your volume the suite costs more than the problem."

## Level 2: brand once, with affiliation

Use when the person asks for a tool or an alternative, the product fits the constraint, and the community allows tool mentions from members with a connection.
Example: "I built Tidewatch for this. It only sends reminders and lists what is overdue. It does not create invoices."

State what the product does not do. A named limit makes the mention believable.

## Level 3: brand and link

Use only when all three hold: the thread asks for a link or a name ("link?", "what is it called?"), the community allows links in comments, and the account has history in that community.
Example: "It is at tidewatch.app. I'm the founder, so keep my bias in mind."

## Decision table

| Situation | Level |
| --- | --- |
| Rant or discussion post | 0 |
| Problem-aware question, community bans brands | 0 or 1 |
| Tool request, community allows brands with affiliation | 2 |
| Switching request | 2 |
| Author or commenter asks for the link | 3 if links are allowed, else 2 |
| Account under 30 days old or under 100 comment karma | 0 |
| Account with fewer than 10 comments in the community | 0 or 1 |
| The last 10 published replies already hold 1 product mention | One level lower than the table says |
| The thread is a showcase or launch thread | Do not reply |

## Pacing

At most 1 reply in 10 may name the product. The other 9 are help only. The posting gate counts this from the history in the database and blocks the reply when the ratio is over the cap.
