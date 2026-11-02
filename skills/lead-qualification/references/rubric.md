# Rubric

The rubric adds to 100. The code stores the fifth part in the field named `recency`. The field holds the reply opportunity score. It looks at age, crowding and whether the thread accepts comments.

| Part | Max | What it measures |
| --- | --- | --- |
| problem_fit | 30 | How closely the post's problem matches a problem the product solves |
| icp_match | 25 | How closely the author matches the ideal customer |
| buying_intent | 20 | How close the author is to choosing a tool |
| urgency | 15 | How much the problem hurts now |
| reply_opportunity | 10 | Whether a reply would still be read and allowed |

## Anchors by part

### problem_fit (30)

| Score | Looks like |
| --- | --- |
| 0 | Different topic. Shares a word with the problem list and nothing else. |
| 10 | Same field, different problem. |
| 20 | Describes one problem the product solves, in different words. |
| 25 | Describes one problem the product solves, in the words of pain_vocabulary. |
| 30 | Describes the exact problem and the main outcome of the product answers it directly. |

### icp_match (25)

| Score | Looks like |
| --- | --- |
| 0 | Matches a not_for entry. |
| 5 | Role unknown, size unknown, topic fits. |
| 10 | Role matches, size unknown. |
| 18 | Near fit: right role, size one step off. |
| 25 | Role, size and situation match the ICP sentence. |

### buying_intent (20)

| Score | Looks like |
| --- | --- |
| 0 | Venting, sharing a story, asking for sympathy. |
| 5 | Asks how others cope. No tool in mind. |
| 8 | Open to ideas. Says "I need something". |
| 14 | Asks for a tool, a recommendation or an alternative. |
| 20 | Names a budget, a deadline, a trial in progress or a switch date. |

### urgency (15)

| Score | Looks like |
| --- | --- |
| 0 | Casual thought. |
| 6 | Recurring annoyance. |
| 10 | Costs time or money each week, stated. |
| 15 | Blocks work now. A deadline or a client is waiting. |

### reply_opportunity (10)

| Condition | Points |
| --- | --- |
| Age 7 days or less | 10 |
| Age 8 to 30 days | 8 |
| Age 31 to 90 days | 6 |
| Age 91 to 150 days | 4 |
| Older, or unknown age | 2 to 3 |
| 80 or more comments | minus 3 |
| Comment state not verified | minus 1 |
| Locked, archived, removed | The thread is dropped before scoring |

## Class table

| Class | Condition |
| --- | --- |
| competitor_intel | Competitor named, buying_intent below 8, problem_fit below 15 |
| high_potential | Total 75 or more, buying_intent 8 or more, commentable, judged by a model or host AI |
| relevant_potential | Total 50 or more |
| customer_insight | Total 30 or more, problem_fit above 0 |
| reject | Everything else |

A thread scored only by keyword rules can never be high_potential. Keywords cannot prove intent.

## Evidence rule

Copy the quote from the post text. Use at most 200 characters. Do not fix typos. Do not join two sentences with an ellipsis. The system compares the quote to the stored post after it collapses whitespace and lowercases both. A quote that does not match lowers confidence.

## Author types to reject or downgrade

| Author | Action |
| --- | --- |
| Seller announcing a product | Reject (seller_promo) |
| Consultant or agency offering services | Reject |
| Student with homework | Reject, or insight at most |
| Bot or account with copied text | Reject |
| Journalist collecting quotes | Reject |
| Competitor employee | competitor_intel at most |
| Person who solved it in the same post | Insight at most |
