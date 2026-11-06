# AI tells and how to fix them

These patterns make a reply read as machine written. Sources: Wikipedia's "Signs of AI writing" guide, moderator and vendor write-ups on Reddit bot detection (2026). They are heuristics, not proof. A human writes any of them now and then. A reader who sees three in one reply stops trusting it.

## Vocabulary

| Tell | Fix |
| --- | --- |
| delve, tapestry, testament, multifaceted, landscape, realm, navigate, leverage, robust, seamless, streamline, elevate, foster, underscore, showcase, resonate, tailored | Use the plain verb: look at, use, make easier, show |
| moreover, furthermore, additionally, however, thus, hence | Start a new sentence, or use "but" and "so" |
| crucial, vital, pivotal, essential, key | Say why it matters in a fact: "it costs a week of work" |
| pain points, value proposition, solution, platform, ecosystem | Say what the person does: "chasing late invoices" |
| "it's worth noting", "it is important to note" | Delete the phrase. State the point. |
| "in today's fast-paced world", "ever-evolving" | Delete. Start with the point. |
| Other forms of a banned word (unlocked, discovering, utilizes) | The linter matches them too. Rewrite the sentence. |

A synonym does not fix a vocabulary tell. "Leverage" becomes "harness" and the reply still reads the same. Change the sentence, not the word.

The full lists sit in banned-ai-tells.txt and banned-user-list.txt. The linter reads those files.

## Punctuation

| Tell | Fix |
| --- | --- |
| Em dashes and en dashes | Use a comma, a period, a colon or parentheses |
| A hyphen with spaces around it used as a dash | Same fix. It reads as an em dash. |
| Curly quotes mixed with straight quotes | Use straight quotes and apostrophes only |
| Emoji before a line or a list item | Remove, unless the owner's samples use emoji |
| Exclamation marks in every second sentence | At most one per reply, only if the samples use them |
| Semicolons and several colons in a short comment | Use periods |

## Structure

| Tell | Fix |
| --- | --- |
| "Not just X, but Y", "it's not X, it's Y", "this isn't about X" | State Y alone |
| "X, not Y" twice in one reply | Keep the one that carries the point |
| Rule of three: three adjectives, three benefits, three steps | List what is true. That is often one or two items. |
| A closing sentence that sums up the reply | Delete it. End on the last real point. |
| A closing question: "What do you think?", "Have you tried X?" | Delete it. A real follow-up question is rare. |
| A lead-in line: "Here's why", "The catch:", "The thing is", "Pro tip" | Say the point |
| Sentences all 15 to 25 words long | Let length follow the idea. Some sentences have 3 words. |
| Paragraph breaks every two sentences, evenly | One paragraph, or break where the idea changes |
| Opening that restates the question | Answer in the first sentence |
| "Here are some tips" followed by a list | Give the best tip in a sentence |
| Three sentences that start with the same word | Change how two of them begin |

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
| Flattery or agreement opener: "Great question!", "You're absolutely right" | Delete |
| Greeting: "Hi!", "Hey there" | Delete, unless the owner's samples open that way |
| Offer of more help: "Let me know if you need more" | Delete |
| Wish of luck: "Good luck!", "Hang in there" | Delete |
| Scripted sympathy: "I understand how frustrating this is" | Say what happened to you, or say nothing |
| Hedging every claim | Hedge once, where you are unsure |
| Promotional adjectives: powerful, innovative, exciting | A number or a fact |
| Balanced "on one hand, on the other hand" | Pick the option you would use and say why |
| Vague authority: "experts say", "studies show" | Name the source or drop the claim |
| Perfect politeness in every sentence | Allow a flat, direct sentence |
| An apology for bias in every product reply | Say the connection once. Skip the apology most of the time. |

## Slop thinking

These patterns come from how a model reasons, not from word choice. A linter finds few of them. Check them yourself.

| Pattern | What it looks like | Fix |
| --- | --- | --- |
| Generic advice | The reply fits under any post on the topic | React to the one detail the author gave: a number, a tool, a constraint |
| Both sides | "It depends on your needs" followed by two even options | Pick what you would do. Give one reason. |
| Survey of options | Four tools in one reply | Name one, or none |
| Invented specifics | "I tracked 40 clients for 3 years" with no source in the facts | Use only numbers the thread, the facts or the owner supplied |
| Fake vulnerability | A made-up failure story used as a hook | Tell only what the owner lived. Otherwise skip the story. |
| Template arc | Problem, advice, caveat, product, every time | Let the thread set the order. Some replies have no caveat. |
| Tidy ending | The last sentence wraps up the whole reply | End on the last real point |
| Symmetry | Every sentence has the same weight and shape | Let one sentence be a plain fact and another a short opinion |
| Answering the topic | The reply covers the subject, not the question | Answer the exact question first |
| Reply written for the post | The author asked in a comment, the reply addresses the post | Answer the comment |

## Reddit-specific tells

| Tell | Fix |
| --- | --- |
| The reply answers the post and ignores the comment above it | Answer the parent comment |
| Expert detail in many unrelated communities within a day | Reply only where the owner has real knowledge |
| The same phrasing in many replies | Vary the structure, not only the words |
| The same opening and ending in many replies | Change the first and last sentence shape |
| No personal detail anywhere | Add the owner's real role or real context only if true |
| Every reply has the same length | Match the thread: short under short comments |
| Perfect grammar and no contraction | Use contractions the samples use |

## How the linter uses this file

The linter checks vocabulary in all forms, dashes (including the spaced hyphen), formatting marks, flattery, greetings, sign-offs, the contrast frame, lead-in lines, scripted sympathy, closing questions, sentence-length spread, repeated openers, stacked lists of three, hedge stacks, missing contractions, missing concrete detail, length and voice match. Most structure checks are warnings. The linter cannot judge truth, relevance or tone. A person must read every reply before it posts.
