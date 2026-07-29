# DB for a Better Actuary

*(Actuarial & Data Science news dashboard)*

A daily-refreshed static dashboard of news relevant to actuarial science and data science:
new methodology, industry trends, emerging risks, and open problems worth solving.

The dashboard keeps a historical baseline spanning the last three years and also refreshes for newly published items each run.

**Live dashboard:** https://sean-shepherd.github.io/actuarial-ds-news-dashboard/

## How it works

A scheduled Claude Code cloud agent runs every morning at 10:00 AM Toronto time, year-round.
(Cron is UTC-only and can't follow daylight saving, so the routine fires at both 14:00 and 15:00
UTC and no-ops whichever firing isn't 10:00 AM local — see [`.claude/routine.json`](.claude/routine.json).)
Each run:

1. Fetches the sources listed in [`actuarial-ds-news-dashboard-instructions.md`](actuarial-ds-news-dashboard-instructions.md)
   (RSS/API where available, scraping only as fallback).
2. Filters to items published in the last 24–48 hours, deduped against `data/seen.json`, while preserving a historical baseline spanning the last three years.
3. Opens each article or paper and extracts the actual substance — methodology, data, results,
   what changed vs. prior practice.
4. Tags each item with a practice area and, for Actuarial items, a business line.
5. Writes a dated snapshot to `data/YYYY-MM-DD.json` and rebuilds `index.html`.
6. Commits and pushes, which redeploys GitHub Pages.

## Layout

```
index.html              generated dashboard — never hand-edit
build.py                deterministic renderer: data/*.json -> index.html
refresh.sh              manual refresh: run agent, rebuild, commit, push
serve.py                local server that makes the in-page Refresh button work
data/YYYY-MM-DD.json    one snapshot per run day; the durable record
data/seen.json          dedupe ledger: normalized URL -> first-seen date
.claude/agents/         the news-dashboard agent definition
```

Snapshots are append-only. All of them are embedded in the page, so history survives every
refresh and is filterable by date.

## Running it manually

You don't have to wait for the 10am routine.

### The Refresh button

```bash
python3 serve.py            # then open http://127.0.0.1:8787/ and click Refresh
python3 serve.py --push     # Refresh also pushes, so the live site updates too
```

The button does the real thing when the page is served by `serve.py`: it runs the refresh,
streams progress into the page, and reloads when the new items are in. By default it commits
locally and leaves pushing to you; `--push` makes it go all the way to the live site.

`serve.py` binds to `127.0.0.1` only, on purpose — `POST /api/refresh` executes `refresh.sh`,
so it must not be exposed to a network.

On the **hosted** page the same button opens the scheduled routine instead, where you can run
it on demand. A static page on GitHub Pages has no backend, and triggering a cloud run from the
browser would mean embedding a credential in a public repo.

### From the command line

```bash
./refresh.sh                # fetch today's news, rebuild, commit, push (updates the live site)
./refresh.sh --no-push      # same, but stop at the commit — nothing leaves your machine
./refresh.sh --build-only   # re-render index.html from existing snapshots; fetches nothing
```

This is safe to run alongside the scheduled routine. Re-running on a day that already has a
snapshot rebuilds it rather than duplicating items, and if the routine pushed first, the script
rebases onto it and retries.

You can also trigger the cloud routine on demand from
[its routine page](https://claude.ai/code/routines/trig_011WCaBkju3UMBApJV2QZ2W6), which exercises
the same path the schedule uses.

`build.py` is stdlib-only Python 3 and takes no arguments. It validates each snapshot as it
renders — missing required fields skip the item with a warning, and off-list tags warn.
