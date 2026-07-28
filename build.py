#!/usr/bin/env python3
"""Render data/*.json snapshots into a single static index.html dashboard.

Stdlib only. Every snapshot in data/ is merged into one page with client-side
filtering, so history survives each daily refresh. Run: python3 build.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "database.json"
OUT = ROOT / "index.html"

SECTIONS = [("actuarial", "Actuarial"), ("data_science", "Data Science")]

PRACTICE_AREAS = [
    "Pricing",
    "Reserving",
    "Predictive Modeling",
    "AI/ML/Deep Learning",
    "ERM",
    "Capital Modelling",
    "Other",
]
BUSINESS_LINES = [
    "Personal Insurance",
    "Commercial Insurance",
    "Reinsurance",
    "Consulting",
    "Other",
]
ITEM_TYPES = ["Publication", "Research", "Article", "News"]

REQUIRED = ["headline", "url", "source", "published", "summary", "practice_area", "item_type"]

# Where the hosted page's Refresh button sends you, since a static public page can't
# trigger a cloud run itself without embedding a credential.
ROUTINE_URL = "https://claude.ai/code/routines/trig_011WCaBkju3UMBApJV2QZ2W6"


def normalize_item(raw, date, key, label):
    pa = raw["practice_area"]
    bl = raw.get("business_line")
    item_type = raw.get("item_type") or "News"
    sort_order = raw.get("sort_order", 0)
    return {
        "date": date,
        "section": key,
        "sectionLabel": label,
        "headline": raw["headline"],
        "url": raw["url"],
        "source": raw["source"],
        "published": raw["published"],
        "summary": raw["summary"],
        "practiceArea": pa,
        "businessLine": bl or None,
        "itemType": item_type,
        "sortOrder": sort_order,
        "firstSeen": date,
        "lastSeen": date,
        "seenIn": [date],
    }


def load_database_items(path=DB_PATH):
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        items = payload.get("items") or payload.get("database") or []
        return items if isinstance(items, list) else []
    return []


def write_database_file(items, path=DB_PATH):
    payload = sorted(items, key=lambda i: (i.get("published", ""), i.get("lastSeen", ""), i.get("section", ""), i.get("headline", "")), reverse=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def merge_database_items(existing_items, new_items):
    by_key = {}
    merged = []
    for item in existing_items:
        key = item.get("url") or "%s|%s|%s" % (item.get("source", ""), item.get("headline", ""), item.get("published", ""))
        by_key[key] = item
        merged.append(item)

    for item in new_items:
        key = item.get("url") or "%s|%s|%s" % (item.get("source", ""), item.get("headline", ""), item.get("published", ""))
        if key in by_key:
            existing = by_key[key]
            existing["lastSeen"] = item.get("lastSeen") or existing.get("lastSeen") or item.get("date") or existing.get("date")
            seen_in = list(existing.get("seenIn") or [])
            for date in item.get("seenIn") or []:
                if date not in seen_in:
                    seen_in.append(date)
            existing["seenIn"] = sorted(seen_in)
            for field in ["section", "sectionLabel", "headline", "url", "source", "published", "summary", "practiceArea", "businessLine", "itemType", "sortOrder"]:
                if field in item and item[field] is not None:
                    existing[field] = item[field]
            if not existing.get("firstSeen"):
                existing["firstSeen"] = item.get("firstSeen") or item.get("date")
            if not existing.get("date"):
                existing["date"] = item.get("date")
            continue
        merged.append(item)
        by_key[key] = item

    merged.sort(key=lambda i: (i.get("published", ""), i.get("lastSeen", ""), i.get("section", ""), i.get("headline", "")), reverse=True)
    return merged


def load_snapshots():
    """Return (items, dates_desc, notes_by_date, latest_items, warnings)."""
    items, notes, warnings = [], {}, []
    latest_items = []
    if not DATA_DIR.is_dir():
        return items, [], notes, latest_items, ["data/ directory not found — nothing to render"]

    for path in sorted(DATA_DIR.glob("*.json")):
        # seen.json is the dedupe ledger and database.json is this script's own output;
        # neither is a dated snapshot. Parsing database.json here crashes on its list shape.
        if path.name in ("seen.json", DB_PATH.name):
            continue
        try:
            snap = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append("%s: invalid JSON (%s) — skipped" % (path.name, exc))
            continue
        if not isinstance(snap, dict):
            warnings.append("%s: not a snapshot object — skipped" % path.name)
            continue

        date = snap.get("date") or path.stem
        notes[date] = snap.get("run_notes") or []
        snapshot_items = []

        for key, label in SECTIONS:
            for raw in snap.get("sections", {}).get(key, []):
                missing = [f for f in REQUIRED if not raw.get(f)]
                if missing:
                    warnings.append(
                        "%s [%s] '%s': missing %s — skipped"
                        % (path.name, key, str(raw.get("headline"))[:60], ", ".join(missing))
                    )
                    continue

                pa = raw["practice_area"]
                if pa not in PRACTICE_AREAS:
                    warnings.append("%s: unknown practice_area %r" % (path.name, pa))
                bl = raw.get("business_line")
                item_type = raw.get("item_type") or "News"
                if bl and bl not in BUSINESS_LINES:
                    warnings.append("%s: unknown business_line %r" % (path.name, bl))
                if key == "actuarial" and not bl:
                    warnings.append(
                        "%s: actuarial item '%s' has no business_line"
                        % (path.name, str(raw["headline"])[:60])
                    )
                if item_type not in ITEM_TYPES:
                    warnings.append("%s: unknown item_type %r" % (path.name, item_type))

                normalized = normalize_item(raw, date, key, label)
                items.append(normalized)
                snapshot_items.append(normalized)

        if snapshot_items and (not latest_items or date >= max(notes.keys(), key=lambda d: d)):
            latest_items = snapshot_items

    dates = sorted(notes.keys(), reverse=True)
    items.sort(key=lambda i: (i["published"], i["date"], -i["sortOrder"], i["section"], i["source"]), reverse=True)
    if latest_items:
        latest_items.sort(key=lambda i: (i["published"], i["date"], -i["sortOrder"], i["section"], i["source"]), reverse=True)
    return items, dates, notes, latest_items, warnings


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DB for a Better Actuary</title>
<style>
  :root {
    --bg: #f7f7f5; --panel: #fff; --ink: #1a1a19; --muted: #6b6b66;
    --line: #e3e3df; --accent: #1f5c8b; --chip: #eeeeea; --chip-on: #1f5c8b;
    --chip-on-ink: #fff; --shadow: 0 1px 2px rgba(0,0,0,.05);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #16171a; --panel: #1e2024; --ink: #e8e8e4; --muted: #9a9a94;
      --line: #2e3136; --accent: #6fa8d1; --chip: #282b30; --chip-on: #6fa8d1;
      --chip-on-ink: #16171a; --shadow: none;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--ink);
    font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  .wrap { max-width: 900px; margin: 0 auto; padding: 32px 20px 80px; }
  header h1 { margin: 0 0 4px; font-size: 26px; letter-spacing: -.01em; }
  header p { margin: 0; color: var(--muted); font-size: 14px; }
  .tagline { margin: 0 0 4px !important; font-size: 13.5px; }
  .hrow { display: flex; gap: 16px; align-items: flex-start; justify-content: space-between; }
  .btn {
    font: inherit; font-size: 14px; font-weight: 500; white-space: nowrap;
    padding: 8px 15px; cursor: pointer; border-radius: 8px;
    background: var(--accent); color: var(--panel); border: 1px solid transparent;
  }
  .btn:hover:not(:disabled) { filter: brightness(1.08); }
  .btn:disabled { opacity: .55; cursor: default; }
  .status {
    margin: 12px 0 0 !important; font-size: 13.5px; padding: 9px 12px;
    border-radius: 8px; background: var(--chip); border: 1px solid var(--line);
  }
  .status.ok { border-color: #2e7d52; }
  .status.err { border-color: #b3453b; }
  .status.warn { border-color: #b08300; }
  @media (max-width: 560px) {
    .hrow { flex-direction: column; }
    .btn { width: 100%; }
  }

  .panel {
    background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
    padding: 16px; margin: 24px 0; box-shadow: var(--shadow);
  }
  .row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
  .row + .row { margin-top: 14px; }
  .lbl {
    font-size: 11px; text-transform: uppercase; letter-spacing: .07em;
    color: var(--muted); min-width: 92px; font-weight: 600;
  }
  input[type=search], select {
    font: inherit; font-size: 14px; padding: 7px 10px; color: var(--ink);
    background: var(--bg); border: 1px solid var(--line); border-radius: 7px;
  }
  input[type=search] { flex: 1 1 200px; min-width: 0; }
  .chip {
    font: inherit; font-size: 13px; padding: 5px 11px; cursor: pointer;
    background: var(--chip); color: var(--ink);
    border: 1px solid transparent; border-radius: 999px;
  }
  .chip[aria-pressed=true] { background: var(--chip-on); color: var(--chip-on-ink); }
  .chip.reset { background: transparent; border-color: var(--line); color: var(--muted); }

  .count { color: var(--muted); font-size: 13px; margin: 0 0 18px; }
  .notes {
    margin: 0 0 24px; font-size: 13px; color: var(--muted);
    border-left: 2px solid var(--line); padding: 2px 0 2px 12px;
  }
  .notes ul { margin: 4px 0 0; padding-left: 18px; }

  h2.sec {
    font-size: 13px; text-transform: uppercase; letter-spacing: .08em;
    color: var(--muted); margin: 32px 0 12px; padding-bottom: 8px;
    border-bottom: 1px solid var(--line);
  }
  article {
    background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
    padding: 18px; margin-bottom: 12px; box-shadow: var(--shadow);
  }
  article h3 { margin: 0 0 8px; font-size: 17px; line-height: 1.35; }
  article h3 a { color: var(--ink); text-decoration: none; }
  article h3 a:hover { color: var(--accent); text-decoration: underline; }
  .meta { font-size: 12.5px; color: var(--muted); margin-bottom: 10px; }
  .meta b { color: var(--ink); font-weight: 600; }
  .sum { margin: 0 0 12px; font-size: 15px; }
  .tags { display: flex; flex-wrap: wrap; gap: 6px; }
  .tag {
    font-size: 11.5px; padding: 3px 9px; border-radius: 999px;
    border: 1px solid var(--line); color: var(--muted); background: var(--bg);
  }
  .tag.pa { border-color: var(--accent); color: var(--accent); }
  .empty { color: var(--muted); padding: 40px 0; text-align: center; }
  footer { margin-top: 48px; font-size: 12px; color: var(--muted); }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="hrow">
      <div>
        <h1>DB for a Better Actuary</h1>
        <p class="tagline">Commercial P&amp;C and data science, daily.</p>
        <p id="sub"></p>
      </div>
      <button class="btn" id="refresh" type="button">Refresh</button>
    </div>
    <p class="status" id="status" hidden></p>
  </header>

  <div class="panel">
    <div class="row">
      <span class="lbl">Search</span>
      <input type="search" id="searchQuery" placeholder="Add a keyword to the database…">
      <select id="searchType">
        <option value="News">News</option>
        <option value="Article">Article</option>
        <option value="Research">Research</option>
        <option value="Publication">Publication</option>
      </select>
      <button class="chip" id="addSearch" type="button">Add to database</button>
    </div>
    <div class="row">
      <span class="lbl">Filter</span>
      <input type="search" id="q" placeholder="Filter current items…">
      <select id="publishedDate"></select>
      <select id="section">
        <option value="">Both sections</option>
        <option value="actuarial">Actuarial</option>
        <option value="data_science">Data Science</option>
      </select>
    </div>
    <div class="row"><span class="lbl">Practice</span><span id="pa" class="row"></span></div>
    <div class="row"><span class="lbl">Business line</span><span id="bl" class="row"></span></div>
    <div class="row"><span class="lbl">Type</span><span id="it" class="row"></span></div>
    <div class="row">
      <span class="lbl">Source</span>
      <select id="source"></select>
      <button class="chip reset" id="reset" type="button">Reset filters</button>
    </div>
    <div class="row">
      <span class="lbl">View</span>
      <select id="viewMode">
        <option value="archive">Historical archive</option>
        <option value="latest">Latest run</option>
      </select>
    </div>
  </div>

  <p class="count" id="count"></p>
  <div id="list"></div>

  <footer id="foot"></footer>
</div>

<script id="payload" type="application/json">/*__DATA__*/</script>
<script>
(function () {
  var D = JSON.parse(document.getElementById('payload').textContent);
  var PA = /*__PA__*/, BL = /*__BL__*/, IT = /*__IT__*/;
  var state = { q: '', publishedDate: '', section: '', pa: [], bl: [], itemType: [], source: '', view: 'archive' };

  var $ = function (id) { return document.getElementById(id); };
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  $('sub').textContent = D.dates.length
    ? D.items.length + ' items across ' + D.dates.length + ' day' +
      (D.dates.length === 1 ? '' : 's') + ' — latest ' + D.dates[0]
    : 'No snapshots yet. Run ./refresh.sh to populate data.';

  var publishedDateSel = $('publishedDate');
  var quarterItems = D.items || [];
  var quarters = quarterItems.map(function (i) { return i.published ? i.published.slice(0, 4) + ' Q' + Math.ceil(parseInt(i.published.slice(5, 7), 10) / 3) : null; })
    .filter(function (q, n, a) { return q && a.indexOf(q) === n; }).sort().reverse();
  publishedDateSel.innerHTML = '<option value="">All published quarters</option>' +
    quarters.map(function (q) { return '<option value="' + esc(q) + '">' + esc(q) + '</option>'; }).join('');

  var sources = D.items.map(function (i) { return i.source; })
    .filter(function (s, n, a) { return a.indexOf(s) === n; }).sort();
  $('source').innerHTML = '<option value="">All sources</option>' +
    sources.map(function (s) { return '<option value="' + esc(s) + '">' + esc(s) + '</option>'; }).join('');

  function chips(host, values, key) {
    host.innerHTML = values.map(function (v) {
      return '<button class="chip" type="button" aria-pressed="false" data-v="' + esc(v) + '">' +
        esc(v) + '</button>';
    }).join('');
    host.addEventListener('click', function (e) {
      var b = e.target.closest('.chip');
      if (!b) return;
      var v = b.dataset.v, on = b.getAttribute('aria-pressed') === 'true';
      b.setAttribute('aria-pressed', on ? 'false' : 'true');
      state[key] = on ? state[key].filter(function (x) { return x !== v; }) : state[key].concat([v]);
      render();
    });
  }
  chips($('pa'), PA, 'pa');
  chips($('bl'), BL, 'bl');
  chips($('it'), IT, 'itemType');

  ['q', 'publishedDate', 'section', 'source'].forEach(function (id) {
    $(id).addEventListener('input', function (e) { state[id] = e.target.value; render(); });
  });
  $('viewMode').addEventListener('change', function (e) {
    state.view = e.target.value;
    render();
  });

  var addBtn = $('addSearch');
  var searchInput = $('searchQuery');
  var searchType = $('searchType');
  function addSearchItem() {
    var keyword = (searchInput.value || '').trim();
    if (!keyword) {
      say('Enter a keyword first.', 'warn');
      return;
    }
    addBtn.disabled = true;
    say('Adding to the database…');
    fetch('/api/search/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyword: keyword, itemType: searchType.value })
    })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j.ok) {
          say('Added — reloading the dashboard…', 'ok');
          setTimeout(function () { location.reload(); }, 600);
        } else {
          say(j.error || 'Could not add the item.', 'err');
          addBtn.disabled = false;
        }
      })
      .catch(function () {
        say('Could not reach the local helper. Run python3 serve.py first.', 'err');
        addBtn.disabled = false;
      });
  }
  addBtn.addEventListener('click', addSearchItem);
  searchInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); addSearchItem(); }
  });
  $('reset').addEventListener('click', function () {
    state = { q: '', publishedDate: '', section: '', pa: [], bl: [], itemType: [], source: '', view: 'archive' };
    ['q', 'publishedDate', 'section', 'source'].forEach(function (id) { $(id).value = ''; });
    $('viewMode').value = 'archive';
    Array.prototype.forEach.call(document.querySelectorAll('.chip[aria-pressed]'), function (b) {
      b.setAttribute('aria-pressed', 'false');
    });
    render();
  });

  function match(i) {
    var publishQuarter = i.published ? i.published.slice(0, 4) + ' Q' + Math.ceil(parseInt(i.published.slice(5, 7), 10) / 3) : null;
    if (state.publishedDate && publishQuarter !== state.publishedDate) return false;
    if (state.section && i.section !== state.section) return false;
    if (state.source && i.source !== state.source) return false;
    if (state.pa.length && state.pa.indexOf(i.practiceArea) < 0) return false;
    if (state.bl.length && (!i.businessLine || state.bl.indexOf(i.businessLine) < 0)) return false;
    if (state.itemType.length && state.itemType.indexOf(i.itemType) < 0) return false;
    if (state.q) {
      var hay = (i.headline + ' ' + i.summary + ' ' + i.source).toLowerCase();
      if (hay.indexOf(state.q.toLowerCase()) < 0) return false;
    }
    return true;
  }

  function card(i) {
    var tags = '<span class="tag pa">' + esc(i.practiceArea) + '</span>' +
      (i.businessLine ? '<span class="tag">' + esc(i.businessLine) + '</span>' : '') +
      '<span class="tag">' + esc(i.itemType) + '</span>';
    return '<article>' +
      '<h3><a href="' + esc(i.url) + '" target="_blank" rel="noopener">' + esc(i.headline) + '</a></h3>' +
      '<div class="meta"><b>' + esc(i.source) + '</b> · published ' + esc(i.published) +
        ' · collected ' + esc(i.date) + '</div>' +
      '<p class="sum">' + esc(i.summary) + '</p>' +
      '<div class="tags">' + tags + '</div>' +
      '</article>';
  }

  function render() {
    var sourceItems = state.view === 'latest' ? (D.latestItems || []) : (D.items || []);
    var shown = sourceItems.filter(match);
    $('count').textContent = shown.length + ' of ' + sourceItems.length + ' items';

    if (!shown.length) {
      $('list').innerHTML = '<p class="empty">Nothing matches these filters.</p>';
      return;
    }
    var html = '';
    [['actuarial', 'Actuarial'], ['data_science', 'Data Science']].forEach(function (s) {
      var group = shown.filter(function (i) { return i.section === s[0]; });
      if (!group.length) return;
      html += '<h2 class="sec">' + s[1] + ' · ' + group.length + '</h2>' +
        group.map(card).join('');
    });
    $('list').innerHTML = html;
  }

  // ---- Refresh button -------------------------------------------------------
  // Served from localhost by serve.py, the button really runs the refresh. On the
  // hosted page there is no backend to call, so it opens the scheduled routine
  // instead — triggering a cloud run from the browser would need a token, and this
  // page is public.
  var ROUTINE_URL = /*__ROUTINE_URL__*/;
  var local = ['localhost', '127.0.0.1', '[::1]', ''].indexOf(location.hostname) >= 0
    && location.protocol !== 'file:';
  var btn = $('refresh'), statusEl = $('status');

  function say(msg, kind) {
    statusEl.hidden = !msg;
    statusEl.textContent = msg || '';
    statusEl.className = 'status' + (kind ? ' ' + kind : '');
  }

  btn.textContent = local ? 'Refresh now' : 'Refresh…';
  btn.title = local
    ? "Fetch today's news and rebuild this page"
    : 'Opens the scheduled routine, where you can run it on demand';

  btn.addEventListener('click', function () {
    if (!local) {
      window.open(ROUTINE_URL, '_blank', 'noopener');
      say('Opened the routine in a new tab — press “Run now” there. This page picks up the ' +
          'result a minute or two after the run finishes. To refresh from your own machine ' +
          'instead, run: python3 serve.py');
      return;
    }
    btn.disabled = true;
    say('Starting…');
    fetch('/api/refresh', { method: 'POST' })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j.state === 'busy') { say('A refresh is already running.', 'warn'); btn.disabled = false; }
        else { poll(); }
      })
      .catch(function () {
        say('Could not reach the local helper. Start it with: python3 serve.py', 'err');
        btn.disabled = false;
      });
  });

  function poll() {
    fetch('/api/refresh/status')
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j.state === 'running') {
          say('Reading articles… this takes a few minutes.' + (j.last ? ' — ' + j.last : ''));
          setTimeout(poll, 2500);
        } else if (j.state === 'done') {
          say('Done — reloading.', 'ok');
          setTimeout(function () { location.reload(); }, 800);
        } else {
          say('Refresh failed: ' + (j.last || 'check the serve.py console'), 'err');
          btn.disabled = false;
        }
      })
      .catch(function () {
        say('Lost contact with the local helper.', 'err');
        btn.disabled = false;
      });
  }

  $('foot').textContent = 'Generated ' + D.generated + ' by build.py · static file, no runtime dependencies';
  render();
})();
</script>
</body>
</html>
"""


def main():
    items, dates, notes, latest_items, warnings = load_snapshots()
    database_items = load_database_items()
    merged_items = merge_database_items(database_items, items)
    write_database_file(merged_items)

    payload = {
        "generated": items and max(dates) or "never",
        "dates": dates,
        "notes": notes,
        "items": merged_items,
        "latestItems": latest_items,
    }
    blob = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")

    html = (
        TEMPLATE.replace("/*__DATA__*/", blob)
        .replace("/*__PA__*/", json.dumps(PRACTICE_AREAS))
        .replace("/*__BL__*/", json.dumps(BUSINESS_LINES))
        .replace("/*__IT__*/", json.dumps(ITEM_TYPES))
        .replace("/*__ROUTINE_URL__*/", json.dumps(ROUTINE_URL))
    )
    OUT.write_text(html, encoding="utf-8")

    by_section = {}
    for i in items:
        by_section[i["sectionLabel"]] = by_section.get(i["sectionLabel"], 0) + 1
    summary = ", ".join("%s %d" % (k, v) for k, v in sorted(by_section.items())) or "no items"
    print("wrote %s — %d items across %d snapshot(s) [%s]"
          % (OUT.name, len(items), len(dates), summary))

    for w in warnings:
        print("  warning: %s" % w, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
