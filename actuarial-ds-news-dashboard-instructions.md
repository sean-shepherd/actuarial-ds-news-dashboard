# Actuarial & Data Science News Dashboard — Build Instructions

## Goal
Build a dashboard that surfaces daily news relevant to actuarial science and data science: new methodology, industry trends, emerging risks, and open problems worth solving.

## Scope — two sections

### 1. Actuarial
Methodology updates, regulatory/standards changes, industry trends, emerging risks.

Sources:
- SOA — start at https://www.soa.org/ and look for news, research, articles, and publications; use https://www.soa.org/research/topics/general-ins-landing/ or https://www.soa.org/news-and-publications/ if no obvious feed is available.
- CAS — start at https://www.casact.org/ and look for research, publications, articles, and news; use https://www.casact.org/research, https://www.casact.org/publications-research/publications, or https://www.casact.org/news if needed.
- IFoA — start at https://www.actuaries.org.uk/ and look for news, insights, research, or publications; use https://www.actuaries.org.uk/news-and-insights if needed.
- Actuary.com — start at https://www.theactuarymagazine.org/ and browse news/articles/features if the feed is unavailable.
- InsuranceERM — start at https://www.insuranceerm.com/ and look for news, articles, research, or archive pages if needed.
- Artemis (ILS/cat risk) — start at https://www.artemis.bm/ and look for news, articles, or market commentary if the feed is unavailable.

Commercial-lines trade press (added 2026-07-28; all six feeds verified live and same-day at the time
of adding). These are the primary supply for the commercial P&C filter below — the actuarial
institutions above rarely publish commercial P&C inside a news window, so fetch these first:
- Business Insurance — https://www.businessinsurance.com/feed/
- Risk & Insurance — https://riskandinsurance.com/feed/
- Insurance Journal — https://www.insurancejournal.com/feed/
- Carrier Management — https://www.carriermanagement.com/feed/
- Claims Journal — https://www.claimsjournal.com/feed/
- Reinsurance News — https://www.reinsurancene.ws/feed/

### 2. Data Science / ML
New techniques, tools, and research relevant to actuarial applications.

Sources:
- arXiv cs.LG — start at https://arxiv.org/ and browse recent listings; use https://arxiv.org/list/cs.LG/recent if needed.
- arXiv stat.ML — start at https://arxiv.org/ and browse recent listings; use https://arxiv.org/list/stat.ML/recent if needed.
- Papers With Code (trending) — start at https://huggingface.co/ or https://paperswithcode.com/ and look for trending papers/benchmarks if needed.
- Towards Data Science — start at https://towardsdatascience.com/ and browse the latest posts if the feed is unavailable.
- Google AI Blog — start at https://blog.google/technology/ai/ or https://research.google/blog/ and look for posts or research updates if needed.

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
Daily refresh, with a different lookback per section (changed 2026-07-28):

- **Actuarial — 7 days.** Commercial-lines trade press does not publish on a daily cadence, and a strict
  48-hour window was rejecting genuinely relevant items that were merely three or four days old.
- **Data Science — 24–48 hours.** arXiv publishes daily; a wider window here just adds noise.

Each refresh should add newly discovered items from the current lookback window while preserving a historical baseline spanning the last three years. The dashboard should support filtering by published quarter rather than by recent day counts, so older historical items remain easily discoverable alongside freshly added ones. Dedupe against previous runs, which is what stops the wider Actuarial window from re-surfacing the same item for seven consecutive days. The dedupe ledger is doing real work now, so do not reset it casually.

## Content depth
Don't over-read the material. Treat this as a lightweight headline-first dashboard: screen each headline and brief source description for actuarial/data-science relevance and commercial-insurance fit, then provide a 3-sentence summary and a link for more information. The goal is not to reproduce the full article or paper, and summaries should stay concise rather than substantive deep dives.

## Tagging (apply to every item)
Tag each item with:
- **Practice area**: Pricing | Reserving | Predictive Modeling | AI/ML/Deep Learning | ERM | Capital Modelling | Other
- **Business line**: Personal Insurance | Commercial Insurance | Reinsurance | Consulting | Other
- **Item type**: Publication | Research | Article | News

Tag Data Science items with practice area only where relevant to actuarial work (e.g. a paper on gradient boosting → Predictive Modeling; a new LLM technique → AI/ML/Deep Learning). Business line tag not required for Data Science items unless the paper specifies an insurance application.

Use Claude to assign tags from the headline and brief source context, and have it pick the best-fit practice area, business line (or "Other"), and item type rather than relying on keyword matching.

## Output structure
Two top-level sections: Actuarial, Data Science. Within each, list items with their tags shown (not separate subsections per tag combo — use tags as filter/sort controls). Keep a historical baseline spanning the last three years, and on each refresh add newly discovered items from the last 24–48 hours. Each item: headline (linked to source URL), 3-sentence summary, practice area tag, business line tag (Actuarial only), item-type tag, source name, published date. Do not show run notes in the dashboard UI.

## Format
Single-page HTML dashboard, static file, no external runtime dependencies beyond CDN-loaded CSS/JS if needed. Include client-side filter controls for practice area and business line. Store daily snapshots so history isn't lost on refresh.

## Non-goals
No login/auth, no email delivery in v1, no sentiment scoring or analytics beyond what's specified above.
