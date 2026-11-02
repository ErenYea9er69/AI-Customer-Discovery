# Target selection

## Reading a comment tree

Reddit returns comments as a tree. The code flattens it with depth, score, author and age. Read these fields:

| Field | Use |
| --- | --- |
| depth | 0 is a top-level comment. Replies at depth 3 or more are rarely read. |
| score | A negative score means the community rejects the comment. Do not reply under it. |
| author | The post author is marked as OP. A comment from OP carries the real constraints. |
| age | Under 24 hours is fresh. Over 3 days is buried. |
| text | The question or claim you reply to. |

## Candidate types

### OP follow-up

OP writes "thanks, does it handle Stripe invoices?" or "I tried X and it failed because Y". The author is present and reads the replies. Reply under the follow-up. Answer the exact question first.

### Tool request in the comments

A commenter writes "what do you use for this?" or "also looking, any names?". Reply under it with a short answer. Several people read these threads for the answers.

### Incomplete answer

The top comment says "use a spreadsheet and set calendar reminders". It works for 3 clients and fails at 12. Add the missing piece: "that works until about 10 clients, then the reminders get lost, so I switched to..." Keep the tone friendly. Never call the other comment wrong.

### Post-level answer

No comment fits. Reply to the post with a direct answer.

## Filters

Skip the candidate when:

- its score is below 0,
- its author is a deleted account,
- the text is shorter than 8 words and has no question,
- the text contains a link and a pitch,
- the author is a moderator and the comment is a rule notice,
- someone already replied with the same suggestion.

## How to write target_text

Copy the parent text word for word, up to 300 characters. If the parent is longer, copy the sentence that holds the question. The reply must answer that sentence.

## One reply per thread

If you reply under a comment, you do not also reply to the post. Pick one place. The best place is where the person who needs the answer will read it.
