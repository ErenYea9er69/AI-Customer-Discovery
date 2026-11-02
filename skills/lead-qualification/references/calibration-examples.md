# Calibration examples

Product for all examples: Tidewatch, an invoice reminder tool for solo freelancers. Problems solved: late client payments, losing track of unpaid invoices, awkward reminder emails. ICP: solo freelancers and tiny studios with 3 to 15 clients. Not for: companies with a finance team, people who need payment processing.

Format: thread text, then part scores (fit / icp / intent / urgency / opportunity), total, class, reasoning.

## 1. High potential

Thread (r/freelance, 3 days old, 14 comments): "Third time this quarter a client is 40+ days late. I use a spreadsheet and I forget to chase. Is there something that just sends the reminders for me? Prefer cheap, I am solo."

Scores: 30 / 25 / 20 / 10 / 10. Total 95. Class high_potential.
Reasoning: Exact problem, solo role, asks for a tool, states a budget lean, repeated event.

## 2. High potential

Thread (r/smallbusiness, 6 days old, 22 comments): "FreshBooks went up again. I only send about 8 invoices a month. What do other one-person shops use? Mostly want auto reminders."

Scores: 25 / 22 / 18 / 9 / 10. Total 84. Class high_potential.
Reasoning: Switching intent with a named constraint. Competitor named but intent is high, so this is a lead.

## 3. Relevant

Thread (r/Entrepreneur, 12 days old, 41 comments): "How do you all deal with clients who pay late? I hate the awkward emails."

Scores: 22 / 15 / 6 / 6 / 8. Total 57. Class relevant_potential.
Reasoning: Same problem, role unknown, no tool in mind. A level 0 or 1 reply fits.

## 4. Relevant

Thread (r/Freelancers, 20 days old, 9 comments): "Looking for invoicing software for my 3-person design studio. Needs reminders and Stripe."

Scores: 18 / 18 / 14 / 5 / 8. Total 63. Class relevant_potential.
Reasoning: Tool request, near fit on size, no urgency stated.

## 5. Customer insight

Thread (r/freelance, 30 days old, 60 comments): "Rant: I spent my whole Friday writing payment reminders. Why are clients like this?"

Scores: 20 / 10 / 2 / 6 / 6. Total 44. Class customer_insight.
Reasoning: Real pain, no intent. Keep for research. Reply only at level 0 if the community allows.

## 6. Competitor intel

Thread (r/smallbusiness, 15 days old, 11 comments): "Honestly QuickBooks reminders work fine for us, just wish the late fee setting was easier."

Scores: 8 / 8 / 2 / 3 / 8. Total 29. Class reject. If the total were 30 or more it would be competitor_intel.
Reasoning: Happy competitor user. Do not reply.

## 7. Reject: seller

Thread (r/SaaS, 2 days old): "I built a tool that sends invoice reminders. Looking for feedback from freelancers!"

Post type seller_promo. author_is_potential_customer false. Reject.

## 8. Reject: wrong ICP

Thread (r/Accounting, 4 days old, 30 comments): "Our AR team of 12 needs automated dunning with ERP sync and SSO."

Scores: 12 / 0 / 14 / 8 / 10. Total 44 would pass the insight line, but the author matches the not_for list (finance team, SSO). Set icp_match 0, then the total is 44 and the class is customer_insight at most. For this lead, reject: the problem looks similar but the buyer is different.

## Scoring habits to copy

- Write the numbers before the reason.
- When unsure between two numbers, choose the lower.
- A high total with a seller author is still a reject.
- A thread with intent 14 or more and fit 20 or more is the core lead type. Expect 1 in 10.
