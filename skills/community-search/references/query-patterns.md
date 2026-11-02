# Query patterns

Fill the slots with phrases from pain_vocabulary. X is the problem in the customer's words. Y is a competitor or alternative. Keep each query between 3 and 9 words after filling.

## By buyer stage

### Switching (highest value)

- alternative to Y
- Y too expensive for small teams
- leaving Y for something simpler
- Y does not do X
- what replaced Y for you

### Solution aware

- tool for X
- is there software to X
- what do you use for X
- best way to automate X
- X for freelancers (swap in the real role)

### Problem aware

- how do you deal with X
- struggling with X
- X takes too much time
- anyone else stuck with X
- how do you stop X

### Script or method requests

- what do you say when X
- template for X
- checklist for X

## By platform

| Platform | Query style | Example |
| --- | --- | --- |
| Reddit | Full question, as a title | how do you chase late invoices without sounding rude |
| Hacker News | Short noun phrase | invoice reminders |
| GitHub | Symptom plus tool name in the issue | duplicate issues triage |
| Quora | "How to" question | how to handle clients who pay late |
| Web forums | Question plus the word forum or thread | late paying clients freelancer forum |

## Intent types the code understands

| intent_type | Meaning | Typical template |
| --- | --- | --- |
| frustration | The person vents about X | struggling with X |
| alternative | The person wants an option to Y | alternative to Y |
| recommendation | The person asks what others use | what do you use for X |
| tool_request | The person asks if a tool exists | is there a tool to X |
| cost | The person complains about price | Y too expensive |
| indirect | The person asks how to do X | how do you handle X |

## Rules

1. One idea per query.
2. No product name of the owner. Ever.
3. No marketing words: solution, platform, streamline, optimize, seamless, workflow.
4. No quotation marks. The harvester removes them anyway.
5. Use the singular role the community uses: "freelancer", "founder", "dev", "admin".
6. Add one constraint word in about a third of the queries: free, cheap, self-hosted, simple, small team, solo, Stripe, Shopify. Constraints match the posts that name them.
7. Drop a query after two runs with zero qualified leads.

## Example plan for a freelancer invoice tool (14 queries)

| Stage | Platform | Query |
| --- | --- | --- |
| Switching | Reddit | alternative to FreshBooks for solo freelancers |
| Switching | Reddit | invoicing app too expensive for one person |
| Solution | Reddit | tool that sends payment reminders automatically |
| Solution | Reddit | what do you use to track unpaid invoices |
| Solution | Hacker News | invoice reminders |
| Problem | Reddit | how do you chase late invoices without sounding rude |
| Problem | Reddit | client is 45 days late what now |
| Problem | Reddit | losing track of who owes me money |
| Problem | Quora | how to handle clients who pay late |
| Script | Reddit | what do you write in a third payment reminder |
| Script | Reddit | late payment email template that works |
| Category | Reddit | best way to manage invoices as a freelancer |
| Category | Web | freelancer forum unpaid invoices thread |
| Cost | Reddit | late fees for small clients worth it |
