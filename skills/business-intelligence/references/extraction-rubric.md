# Extraction rubric

Use this table to decide where each field comes from and how much to trust it.

| Field | Best source pages | Signal words to look for | Trust level |
| --- | --- | --- | --- |
| main_product_or_service | home page hero, meta description | "helps you", "for", "so you" | High if the hero and the meta agree |
| problems_solved | use cases, solutions, home page "problem" block, FAQ | "stop", "no more", "tired of", "without", "instead of" | High when stated, medium when implied |
| features | features, product, pricing table | nouns in lists and tier tables | High |
| icp | customers, case studies, pricing tier names, about | job titles, company sizes, "teams of", "agencies", "solo" | Medium. Mark as inference unless the page says "built for X". |
| pricing_info | pricing page only | currency symbols, "per month", "per seat", "free plan" | High, never inferred |
| competitors_and_alternatives | comparison pages, "vs" pages, FAQ, migration guides | "switch from", "alternative to", "import from" | Medium. Import tools name the real alternatives. |
| trigger_events | case studies, testimonials, blog titles | "after we", "when we hit", "before our" | Medium |
| unique_selling_points | home page, about | "only", "first", "built for", "no X required" | Medium. Marketing claims are not proof. |

## Page type rules

- Testimonials: quote the situation the customer describes ("we lost two weeks reconciling"). The situation is a problem phrase. The praise is not.
- Case studies: the "before" paragraph holds the best pain vocabulary and trigger events.
- Pricing tiers: tier names and limits reveal the ICP size (a "Solo" tier and a "Team of 10" tier name two different buyers).
- Integration lists: each integration names a tool the customer already uses. Use them as search context ("works with Stripe" means customers use Stripe).
- Blog titles: titles written as questions are pain phrases someone already searches.

## Meta data the crawler adds

The crawler adds the page title, the meta description, the Open Graph description and JSON-LD fields (name, description, offers, aggregateRating). Treat JSON-LD price and rating as facts only when the same value appears in the visible text. Treat aggregateRating with care: skip it unless the page shows reviews.

## Red flags

- A claim with a number and no source on the page ("saves 10 hours a week"). Record it as a fact with the category "claim" and do not repeat the number in any reply.
- Two pages that disagree (price, plan names). Record both as facts with their URLs and add a low-confidence inference.
- Lists of logos with no names. Skip them.
