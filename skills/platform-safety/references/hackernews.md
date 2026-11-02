# Hacker News

## Rule

[official] The Hacker News guidelines were updated in March 2026. They state that people must not post generated or AI-edited comments, because Hacker News is for conversation between humans. They also ask people not to post shilling or astroturf and not to use the site mainly for promotion. Check news.ycombinator.com/newsguidelines.html for the live text.

## What the app does

- The harvester reads Ask HN posts and stories through the public Algolia search API. It filters Show HN posts and link-only stories.
- The qualifier scores the threads. Leads from Hacker News stay in the lead list as research.
- The reply generator does not draft anything for Hacker News. A lead on Hacker News carries the policy flag human_only.
- The publisher refuses to prepare a post for Hacker News.

## How to use Hacker News leads

1. Read the thread to learn the words people use for the problem.
2. Add those words to pain_vocabulary.
3. Note the tools and alternatives people name. Add them to competitors_and_alternatives.
4. If the owner wants to join the conversation, the owner writes the comment alone, in their own words, with no draft from the app.

## Thread facts

- Threads close to new comments after a period set by the site. The app drops Ask HN threads older than 14 days as a safe default.
- A comment that mentions your own product is normal when it answers the question and states the connection. Bare promotion gets flagged.
