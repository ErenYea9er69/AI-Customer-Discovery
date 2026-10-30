Always comeback to this so u make this transformation as i want+ 

# Transform Agent-Reach into an AI Customer Discovery & Lead Generation Agent

## 1. Main Objective

Transform this existing repository into a fully functional AI customer discovery and lead generation application.

The user should provide either:

- Their website URL. or A product or service description.
- Both, if available.

The AI should understand the business, identify its target customers and the problems it solves, search relevant online communities for people experiencing those problems, evaluate potential customers, and generate personalized, helpful replies.

The final product should have a dashboard where users review leads, understand customer problems, edit AI-generated replies, approve them, and optionally enable controlled automatic posting.

This is no longer a general-purpose internet research tool.

It is a customer intelligence and opportunity discovery agent.

## 2. Phase One: Full Repository & Platform Audit

Before changing anything, inspect the entire cloned repository.

Do not assume you understand the project from its README.

Inspect:

- Every directory and source file.
- All platform/channel integrations.
- Every supported search and reading operation.
- Backend tools and dependencies.
- Authentication and session management.
- CLI commands and their output formats.
- Existing tests and configuration.
- Platform limitations and authentication requirements.
- Existing abstractions that we can reuse.

Create a platform audit that evaluates every existing integration.

For each platform, determine:

1. Does it provide actual customer complaints or discussions?
2. Can it search relevant posts or conversations?
3. Can it access comments and replies?
4. Can it identify people asking for solutions?
5. Does it support useful search filters?
6. Is its data reliable enough for lead qualification?
7. Does it require authentication or paid access?
8. Does it support publishing replies through a documented and permitted method?
9. Is it worth maintaining for this particular product?

Classify every integration into:

- Core: essential to customer discovery.
- Optional: useful for specific industries or customer types.
- Disabled: irrelevant to the default workflow.
- Remove: obsolete, redundant, or genuinely unnecessary.

### Platform selection

Reddit should be the primary discovery source.

Web search and public web reading should serve as supplementary sources for finding relevant discussions and community pages.

Consider keeping these integrations available when they provide actual value:

- Reddit: customer complaints, questions, frustrations, recommendations and discussions.
- X/Twitter: public conversations and requests for solutions.
- Facebook: relevant community and group discussions.
- LinkedIn: B2B problems and professional discussions.
- GitHub: issues and feature requests for developer products.
- V2EX: technology-related discussions.
- Other existing platforms when the target market justifies them.

YouTube, Bilibili and podcast transcription should not run by default. They are generally lower-priority sources for identifying people actively seeking solutions.

Disable unrelated integrations such as stock-market research, job discovery and general video research from the customer discovery workflow.

Important: Do not blindly delete reusable source infrastructure. Remove irrelevant integrations from the actual product workflow, UI, dependencies and configuration where appropriate. Keep a clean adapter architecture for useful optional sources.

Do not introduce new integrations without a clear reason.

Create a document named PLATFORM_AUDIT.md containing your findings and decisions.

## 3. Phase Two: Business Understanding Engine

Build an onboarding screen where the user submits their website or describes their business.

The AI should analyze the website and extract:

- Business and product name.
- Industry and niche.
- Main product or service.
- Features and capabilities.
- Problems the product solves.
- Customer outcomes.
- Ideal customer profile (ICP).
- Target industries.
- Target customer roles.
- Customer demographics when relevant.
- Customer frustrations.
- Existing alternatives and competitors.
- Unique selling points.
- Pricing information when available.
- Geographic market.
- Situations that trigger customers to search for a solution.

Analyze relevant website pages, not only the homepage.

Prioritize:

- Homepage.
- Product and service pages.
- Pricing.
- Features.
- FAQ.
- Case studies.
- About page.

Do not invent product features, guarantees or capabilities.

Separate verified facts from AI inferences. Include confidence levels and links to the original website pages.

After extraction, show the user an editable business profile.

The user must confirm the profile before launching research.

## 4. Phase Three: Intelligent Customer Discovery

Build a research engine that uses the business profile to discover actual potential customers.

The agent should automatically generate search queries based on:

- The identified niche.
- ICP.
- Problems the product solves.
- Customer language.
- Competitor alternatives.
- Common frustrations.
- Buying signals.

Do not rely only on product keywords.

Search for expressions such as:

- "I'm struggling with..."
- "Does anyone know a better way to..."
- "Looking for an alternative to..."
- "I hate having to..."
- "Is there a tool that..."
- "How do you solve..."
- "This is too expensive."
- "I wish there was..."
- "Can anyone recommend..."
- "What do you use for..."

Also identify indirect complaints where people describe a problem without knowing that a product category exists to solve it.

Use the available Agent-Reach integrations as the discovery infrastructure.

The agent should select sources based on the actual customer profile instead of automatically searching every supported platform.

For example:

A developer tool should prioritize Reddit developer communities, GitHub Issues and relevant technology forums.

A B2B service should prioritize professional discussions and relevant business communities.

A consumer product should prioritize communities where its target customers discuss purchasing decisions and daily frustrations.

Reddit should remain the default primary source.

## 5. Phase Four: Lead Qualification & Intelligence

Do not treat every complaint as a potential customer.

Analyze every discovered conversation.

For each result, extract:

- Original URL.
- Platform and subreddit/community.
- Author or public username when available.
- Publication date.
- Original title.
- Relevant post or comment excerpt.
- Exact customer problem.
- Pain-point category.
- Customer profile match.
- Existing solution or competitor mentioned.
- Purchase intent.
- Urgency.
- How the product addresses the problem.
- Evidence supporting the classification.

### Lead scoring

Give every potential lead a score from 0 to 100.

Use an explainable scoring system:

- ICP match: 25 points.
- Problem and product fit: 30 points.
- Buying intent: 20 points.
- Problem urgency: 15 points.
- Recency: 10 points.

Show the score breakdown and explain every important decision.

Classify results into:

- High-potential lead.
- Relevant potential lead.
- Customer research insight.
- Competitor intelligence.
- Irrelevant conversation.

Keep customer research insights separate from actual sales opportunities.

A person complaining about something does not automatically have buying intent.

### Quality controls

Implement:

- Duplicate detection.
- Semantic similarity detection.
- Spam filtering.
- Irrelevance filtering.
- Stale conversation filtering.
- Original source verification.
- Confidence scoring.

Never invent a complaint or customer requirement.

Store the original source and supporting evidence for every lead.

## 6. Phase Five: AI Reply Generation

This is one of the most important parts.

For every qualified lead, generate personalized responses based on the actual conversation.

Do not generate generic promotional comments.

The agent should:

1. Understand the person's exact situation.
2. Identify the main problem.
3. Suggest a practical solution.
4. Provide useful advice.
5. Introduce the user's product only when it genuinely fits.
6. Keep the tone natural and appropriate for that community.

Generate two possible approaches when relevant:

A. Value-first response:
A helpful answer that provides value without mentioning the product.

B. Product-aware response:
A helpful answer that naturally introduces the product as one possible solution.

The AI must:

- Avoid aggressive marketing.
- Avoid irrelevant product mentions.
- Never pretend to be an ordinary customer.
- Never invent personal experiences.
- Never invent product capabilities.
- Disclose the user's affiliation when recommending their own product.
- Respect the community's self-promotion rules.
- Adapt the length and tone to the original discussion.

Allow users to edit generated replies.

## 7. Phase Six: Posting and Automation

Agent-Reach currently provides read-only functionality. Do not assume its existing integrations support publishing.

Audit the actual capabilities of each platform.

Implement a separate publishing layer.

Support three modes:

1. Draft mode: generate and save replies.
2. Manual approval: user reviews and approves each reply before publishing.
3. Automatic mode: publish eligible replies without individual approval.

Manual approval should be the default.

Automatic posting must only use documented and permitted publishing methods, such as supported official APIs.

Never bypass login protections, CAPTCHAs, access controls or platform restrictions.

Add:

- Per-platform enable/disable settings.
- Allowed subreddit/community lists.
- Per-day publishing limits.
- Minimum time intervals.
- Duplicate reply prevention.
- Community rule checks.
- Posting history.
- Error handling.
- Emergency stop.

Never automatically send bulk direct messages or spam communities.

The user must explicitly enable automatic mode and configure its limits.

If a platform does not support permitted automated publishing, provide a copy-reply and open-original-post workflow instead.

## 8. Phase Seven: Dashboard

Build a functional dashboard around the complete workflow.

Do not build a dashboard that only displays search results.

It should include:

### Overview

- Total conversations discovered.
- Qualified leads.
- High-potential leads.
- Common customer problems.
- Most promising communities.
- Research activity.
- Reply status.

### Business Profile

- Website.
- Product description.
- Extracted niche.
- ICP.
- Problems solved.
- Competitors.
- Editable business information.

### Discovery

- Active research campaigns.
- Search queries.
- Selected platforms.
- Relevant communities.
- Research progress.
- Search history.

### Leads Inbox

Each lead should display:

- Customer/problem title.
- Source.
- Score.
- Buying intent.
- Pain-point category.
- Date.
- Qualification reason.
- Original discussion link.

Allow filtering by score, platform, date, problem category and status.

Clicking a lead should open its complete evidence and analysis.

### Reply Studio

Display:

- Original conversation.
- Extracted problem.
- AI analysis.
- Suggested solution.
- Generated replies.
- Editable response field.
- Copy button.
- Open original discussion.
- Approve and publish action.

### Analytics

Identify patterns across discovered conversations:

- Most common complaints.
- Repeated customer requests.
- Problems with the highest urgency.
- Competitors receiving negative feedback.
- Missing features in existing alternatives.
- Common workarounds.
- Emerging customer needs.

Turn those findings into actionable product and marketing suggestions.

### Settings

- LLM provider and model.
- API configurations.
- Platform connections.
- Research limits.
- Posting settings.
- Data retention.
- Export options.

## 9. Phase Eight: Data and Architecture

Use the existing Python architecture wherever it makes sense.

Do not rewrite working integrations without a clear reason.

If no dashboard or backend exists, use a lightweight architecture:

- Python and FastAPI for the backend.
- React, TypeScript and Vite for the frontend.
- SQLite for local persistence.
- Reusable platform adapters.
- Structured LLM outputs.
- Background jobs for research campaigns.

Keep these concerns separate:

- Website analysis.
- Business profile management.
- Search planning.
- Platform discovery.
- Content extraction.
- Lead qualification.
- Reply generation.
- Publishing.
- Analytics.

Create reusable modules rather than one giant agent function.

Use environment variables for credentials. Never hardcode secrets or expose API keys in the frontend.

Make the model provider configurable. Do not force users into a single paid AI provider.

Keep Agent-Reach CLI commands working unless a specific change is necessary.

## 10. Phase Nine: Testing and Verification

Do not finish after creating the UI.

Test the complete workflow.

Required test scenarios:

1. Submit a website and extract its business profile.
2. Submit a manual product description.
3. Edit and confirm the extracted ICP.
4. Generate customer-specific search queries.
5. Search Reddit through an available working integration.
6. Retrieve original posts and relevant comments.
7. Filter unrelated discussions.
8. Detect duplicate posts.
9. Score potential leads.
10. Explain scoring decisions.
11. Generate personalized replies.
12. Edit and save replies.
13. Approve a reply.
14. Verify publishing behavior where a permitted integration exists.
15. Export leads.
16. Handle unavailable platforms and expired sessions.

Do not use fake search results as evidence of successful implementation.

Mock data is acceptable for automated tests, but the actual application must clearly distinguish test data from real discoveries.

Test API failures, authentication failures, empty search results and LLM errors.

## 11. Execution Rules

Work directly inside the cloned repository.

Before modifications:

- Check Git status.
- Protect existing uncommitted user changes.
- Map the complete architecture.
- Identify reusable functionality.
- Write a short implementation plan.

Then implement the actual application.

Do not stop after writing the plan or audit.

Prioritize a complete working workflow over implementing many incomplete features.

Do not change unrelated functionality.

Do not remove working integrations merely to simplify the project.

Do not create placeholder buttons or disconnected dashboard pages.

Do not claim a feature works unless you have tested it.

When a platform or API imposes a real limitation, explain it and provide the best supported alternative.

Keep documentation updated.

## Final Deliverable

The result should be a working AI customer discovery agent.

The user's experience should be:

1. Enter a website or product description.
2. AI understands the business and its ideal customers.
3. Confirm the extracted business profile.
4. Launch customer discovery.
5. AI searches relevant discussions and communities.
6. AI identifies complaints, unmet needs and buying signals.
7. AI filters and ranks potential customers.
8. AI explains why each person is relevant.
9. AI generates personalized helpful replies.
10. User reviews and approves replies, or enables controlled automatic publishing.
11. Dashboard tracks leads, replies and customer pain-point insights.

The ultimate objective is to help someone find real people who experience problems their product solves, understand those problems, and start relevant conversations that can turn into customers.

Build this as a complete, reliable application, not another general-purpose web scraper.
