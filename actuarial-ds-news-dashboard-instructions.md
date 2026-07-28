# Actuarial & Data Science News Dashboard — Build Instructions

## Goal
Build a dashboard that surfaces daily news relevant to actuarial science and data science: new methodology, industry trends, emerging risks, and open problems worth solving.

## Scope — two sections

### 1. Actuarial
Methodology updates, regulatory/standards changes, industry trends, emerging risks.

Sources:
- SOA — https://www.soa.org/news-and-publications/
- CAS — https://www.casact.org/news
- IFoA — https://www.actuaries.org.uk/news-and-insights
- Actuary.com — https://www.theactuarymagazine.org/
- InsuranceERM — https://www.insuranceerm.com/
- Artemis (ILS/cat risk) — https://www.artemis.bm/news/

### 2. Data Science / ML
New techniques, tools, and research relevant to actuarial applications.

Sources:
- arXiv cs.LG — https://arxiv.org/list/cs.LG/recent
- arXiv stat.ML — https://arxiv.org/list/stat.ML/recent
- Papers With Code (trending) — https://paperswithcode.com/
- Towards Data Science — https://towardsdatascience.com/
- Google AI Blog — https://ai.googleblog.com/

Use RSS/API where available; fall back to scraping only if no feed exists.

## Scope filter — Actuarial section is commercial P&C only
(Added 2026-07-28, supersedes the broader source scope above.)

Every item in the Actuarial section must concern **commercial (business-insured) property & casualty
insurance**. Applies to all six actuarial sources, SOA included, and is applied at collection time.

Out of scope: life, annuities, mortality/longevity, retirement/pensions; health of any kind, including
group and employer-sponsored benefits; all personal lines; and reinsurance/ILS where the substance is
capital-markets mechanics rather than the underlying commercial exposure.

This filter is deliberately narrow. SOA will often yield zero items, since it is the life and health
body, and Artemis will lose most of its ILS deal flow. The Actuarial section is therefore expected to
run below the 5–8 target on many days. Do not pad to reach the target and do not relax the filter to
fill space — report the shortfall instead. See `.claude/agents/news-dashboard.md` §3a for the full
keep/drop lists.

The Data Science section is not subject to this filter.

## Cadence
Daily refresh. Only surface items published in the last 24–48 hours; dedupe against previous runs.

## Content depth
Don't stop at headlines. Open each article/paper and extract the actual substance: what methodology or model is proposed, what data/results support it, what changed vs. prior practice, and why it matters. Summary should be 3–5 sentences of real content, not a teaser.

## Tagging (apply to every Actuarial item)
Tag each item with:
- **Practice area**: Pricing | Reserving | Predictive Modeling | AI/ML/Deep Learning | ERM | Capital Modelling | Other
- **Business line**: Personal Insurance | Commercial Insurance | Reinsurance | Consulting | Other

Tag Data Science items with practice area only where relevant to actuarial work (e.g. a paper on gradient boosting → Predictive Modeling; a new LLM technique → AI/ML/Deep Learning). Business line tag not required for Data Science items unless the paper specifies an insurance application.

Use Claude to assign tags: feed it the extracted article/paper content and the tag lists above, and have it pick the best-fit practice area and business line (or "Other") rather than relying on keyword matching.

## Output structure
Two top-level sections: Actuarial, Data Science. Within each, list items with their tags shown (not separate subsections per tag combo — use tags as filter/sort controls). 5–8 items per section per day. Each item: headline (linked to source URL), 3–5 sentence substantive summary, practice area tag, business line tag (Actuarial only), source name, date.

## Format
Single-page HTML dashboard, static file, no external runtime dependencies beyond CDN-loaded CSS/JS if needed. Include client-side filter controls for practice area and business line. Store daily snapshots so history isn't lost on refresh.

## Non-goals
No login/auth, no email delivery in v1, no sentiment scoring or analytics beyond what's specified above.
