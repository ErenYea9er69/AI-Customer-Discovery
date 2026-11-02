# Voice cloning from the owner's old comments

The goal: replies that read like the owner wrote them on a normal day. The method copies habits that a reader notices. It never copies sentences or claims.

## Where the samples come from

1. The owner links an existing account (Reddit, X or another platform). The app reads the account's public comment history and imports samples. Public history needs no password.
2. The owner pastes 3 to 15 comments.
3. Both. Linked history gives volume, pasted comments give the best examples.

Use real comments from the same kind of community as the target. A voice from a hobby community does not fit a business community.

## Sample rules

| Rule | Value |
| --- | --- |
| Minimum samples | 3 comments of 12 words or more |
| Good set | 8 to 15 comments |
| Skip | Removed or deleted comments, one-word replies, quotes of other users, comments that are mostly links, comments in another language |
| Weight | The newest 5 samples count double |
| Mixed registers | Group by community type and measure each group. Use the group that matches the target. |

## What the code measures

| Feature | Meaning | How the reply uses it |
| --- | --- | --- |
| avg_words_per_reply | Mean length of a sample | Target length is 0.6 to 1.5 times this number |
| avg_sentence_words | Mean sentence length | The reply stays within 40 percent of it |
| sentence_len_stdev | Spread of sentence length | The reply keeps a similar spread |
| lowercase_start_ratio | Share of sentences starting in lowercase | The reply copies the habit |
| contraction_rate | Contractions per 100 words | The reply matches within one step |
| no_apostrophe_ratio | Share of "dont", "im", "cant" forms | Copied only if above 0.3 |
| question_rate | Share of sentences that ask | Matched |
| exclamation_rate | Share of sentences with ! | Matched. Zero means none. |
| ellipsis_rate | Share of sentences with ... | Matched |
| emoji_rate | Emoji per 100 words | Zero means none |
| paren_rate | Parentheses per 100 words | Matched |
| comma_per_sentence | Commas per sentence | Within one step |
| first_person_rate | "I" and "my" per 100 words | Matched |
| top_openers | Most common first words of a reply | Offered as opener options |
| top_closers | Most common last phrases | Offered as closer options |
| hedge_words | imo, tbh, fwiw and so on | Used at the sample rate |
| paragraph_count_avg | Paragraphs per reply | Matched |

The prompt shows the owner's measured card and 3 verbatim samples as examples of style. The model must not copy a sample sentence.

## Honesty limits

- Copy style, never content. Do not reuse a story, a number or a claim from a sample.
- Do not claim an experience the owner did not have. If the owner never used a competitor, the reply does not say "I used X for a year".
- Do not mimic another person's account. The voice belongs to the account that posts the reply.
- Keep the affiliation sentence. A matching voice does not remove the duty to say you work on the product.

## Checking the clone

The linter compares each draft to the card:

| Check | Pass |
| --- | --- |
| Length | Between 0.5 and 1.7 times the sample average, and within max_words |
| Lowercase style | If lowercase_start_ratio is above 0.6, most sentences start in lowercase |
| Emoji | None when emoji_rate is 0 |
| Exclamation | None when exclamation_rate is 0 |
| Contractions | At least one when contraction_rate is above 1 per 100 words |

The result is a voice score from 0 to 100. A score under 60 shows a warning. A person decides.

## Few-shot prompt layout

1. The measured card in six lines.
2. Three samples from the same community type, quoted and labeled "style only, do not copy".
3. The thread, then the target text.
4. The rules.
