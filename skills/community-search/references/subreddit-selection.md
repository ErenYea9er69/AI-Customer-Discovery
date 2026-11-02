# Community selection

Pick communities by who asks questions there, not by size.

## Three kinds of community

| Kind | What members post | Use |
| --- | --- | --- |
| Help communities | Questions, rants, tool requests | Main search targets |
| Showcase communities | "I built", launches, feedback requests | Skip. Every thread is promotion. |
| General feeds | Mixed content, memes, news | Skip. Low density of buyers. |

Examples of showcase communities to skip: r/SideProject, r/IMadeThis, r/alphaandbetausers. General feeds to skip: r/all, r/popular, r/AskReddit. The code already drops the general feeds in a deny list.

## Selection steps

1. Name the role from the ICP in the words that role uses ("freelancer", "sysadmin", "shopify store owner").
2. Search the web index for "<role> subreddit" and for the pain phrase with "reddit". Note the communities that appear more than once.
3. Open each candidate. Check three things in the last 30 days: how many posts ask a question, how many are promotion, how many moderators remove posts.
4. Keep a community only when at least 3 of the last 10 posts ask for help in the product's field.
5. Read the rules page. Record the self-promotion rule in one line. A community that bans any tool mention is still a source of insight, but the reply must stay at level 0.
6. Keep at most 8 communities per run.

## Starter map the planner uses

| Field | Communities to test |
| --- | --- |
| Developer tools | r/devops, r/webdev, r/softwaredevelopment, r/ExperiencedDevs |
| B2B and SaaS | r/SaaS, r/startups, r/Entrepreneur, r/smallbusiness |
| Marketing and sales | r/marketing, r/digital_marketing, r/sales, r/SEO |
| Design | r/web_design, r/userexperience, r/ProductManagement |
| Productivity | r/productivity, r/notion, r/automation |
| Freelance | r/freelance, r/Freelancers, r/consulting |
| Ecommerce | r/ecommerce, r/shopify, r/dropship |
| Finance and admin | r/Accounting, r/Bookkeeping, r/smallbusiness |
| AI tools | r/ChatGPT, r/LocalLLaMA, r/ClaudeAI |
| Creators | r/NewTubers, r/podcasting, r/videography |

Treat the map as a list of places to test. Rules change, communities close and new ones appear. The planner can also ask the language model for names, and the code accepts only names that match the pattern r/ followed by 3 to 21 letters, digits or underscores.

## Rule patterns seen in practice

These patterns come from vendor guides and community posts. Check each community's current rules before you act.

| Pattern | Example | Effect on a reply |
| --- | --- | --- |
| Promotion in designated threads only | r/startups | Level 0 or 1 outside the thread |
| Founder content allowed with conditions | r/SaaS | Level 2 with affiliation, no link |
| Tool pitches effectively banned | r/freelance, r/SEO | Level 0 only |
| Minimum karma or account age | Many communities | Check the linked account stats first |
| AI-written content banned | Many hobby and tech communities | A person must rewrite the reply in their own words |
