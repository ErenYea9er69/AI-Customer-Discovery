# AI tells and how to fix them

These patterns make a reply read as machine written. Sources: Wikipedia's "Signs of AI writing" guide, moderator and vendor write-ups on Reddit bot detection (2026). They are heuristics, not proof. A human can write any of them. A reader who sees three in one reply stops trusting it.

## Vocabulary

| Tell | Fix |
| --- | --- |
| delve, tapestry, testament, multifaceted, landscape, realm, navigate, leverage, robust, seamless, streamline, elevate, foster, underscore, showcase | Use the plain verb: look at, use, make easier, show |
| moreover, furthermore, additionally, however, thus, hence | Start a new sentence, or use "but" and "so" |
| crucial, vital, pivotal, essential, key | Say why it matters in a fact: "it costs a week of work" |
| "it's worth noting", "it is important to note" | Delete the phrase. State the point. |
| "in today's fast-paced world", "ever-evolving" | Delete. Start with the point. |

The full lists sit in banned-ai-tells.txt and banned-user-list.txt. The linter reads those files.

## Punctuation

| Tell | Fix |
| --- | --- |
| Em dashes and en dashes | Use a comma, a period, a colon or parentheses |
| Curly quotes mixed with straight quotes | Use straight quotes and apostrophes only |
| Emoji before a line or a list item | Remove, unless the owner's samples use emoji |
| Exclamation marks in every second sentence | At most one per reply, only if the samples use them |

## Structure

| Tell | Fix |
| --- | --- |
| Rule of three: three adjectives, three benefits, three steps | Give one or two items. Odd counts come from habit, not from the topic. |
| "Not just X, but Y" and "not X, but Y" | State Y alone |
| A closing sentence that sums up the reply | Delete it. End on the last real point. |
| Sentences all 15 to 25 words long | Mix 4-word, 20-word and 9-word sentences |
| Paragraph breaks every two sentences, evenly | One paragraph, or break where the idea changes |
| Opening that restates the question | Answer in the first sentence |
| "Here are some tips" followed by a list | Give the best tip in a sentence |

## Formatting

| Tell | Fix |
| --- | --- |
| Headers, bullets, numbered lists, bold labels | Plain paragraphs |
| A bold lead-in followed by a colon | Plain sentence |
| Code fences for non-code | Plain text |
| A table in a comment | Plain sentence |

## Tone

| Tell | Fix |
| --- | --- |
| Flattery opener: "Great question!" | Delete |
| Offer of more help: "Let me know if you need more" | Delete |
| Hedging every claim | Hedge once, where you are unsure |
| Promotional adjectives: powerful, innovative, exciting | A number or a fact |
| Balanced "on one hand, on the other hand" | Pick the option you would use and say why |
| Vague authority: "experts say", "studies show" | Name the source or drop the claim |
| Perfect politeness in every sentence | Allow a flat, direct sentence |

## Reddit-specific tells

| Tell | Fix |
| --- | --- |
| The reply answers the post and ignores the comment above it | Answer the parent comment |
| Expert detail in many unrelated communities within a day | Reply only where the owner has real knowledge |
| The same phrasing in many replies | Vary the structure, not only the words |
| No personal detail anywhere | Add the owner's real role or real context only if true |
| Every reply has the same length | Match the thread: short under short comments |
| Perfect grammar and no contraction | Use contractions the samples use |

## How the linter uses this file

The linter checks vocabulary, dashes, formatting marks, flattery and sign-offs, sentence-length spread, length and voice match. It cannot judge truth or tone. A person must read every reply before it posts.
