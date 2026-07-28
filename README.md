# Actuarial & Data Science News Dashboard

A daily-refreshed static dashboard of news relevant to actuarial science and data science:
new methodology, industry trends, emerging risks, and open problems worth solving.

**Live dashboard:** https://sean-shepherd.github.io/actuarial-ds-news-dashboard/

## How it works

A scheduled Claude Code cloud agent runs every morning at 8:00 AM Eastern. It:

1. Fetches the sources listed in [`actuarial-ds-news-dashboard-instructions.md`](actuarial-ds-news-dashboard-instructions.md)
   (RSS/API where available, scraping only as fallback).
2. Filters to items published in the last 24–48 hours, deduped against `data/seen.json`.
3. Opens each article or paper and extracts the actual substance — methodology, data, results,
   what changed vs. prior practice.
4. Tags each item with a practice area and, for Actuarial items, a business line.
5. Writes a dated snapshot to `data/YYYY-MM-DD.json` and rebuilds `index.html`.
6. Commits and pushes, which redeploys GitHub Pages.

## Layout

```
index.html              generated dashboard — never hand-edit
build.py                deterministic renderer: data/*.json -> index.html
data/YYYY-MM-DD.json    one snapshot per run day; the durable record
data/seen.json          dedupe ledger: normalized URL -> first-seen date
.claude/agents/         the news-dashboard agent definition
```

Snapshots are append-only. All of them are embedded in the page, so history survives every
refresh and is filterable by date.

## Running it manually

```bash
claude                      # then: use the news-dashboard agent
python3 build.py            # re-render index.html from existing snapshots
```

`build.py` is stdlib-only Python 3 and takes no arguments. It validates each snapshot as it
renders — missing required fields skip the item with a warning, and off-list tags warn.
