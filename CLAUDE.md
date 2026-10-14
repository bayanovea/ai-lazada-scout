# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal shopping scout for Lazada Thailand. The user gives a household shopping list in Russian (often not knowing the Thai or even the right English name for a product type). Claude finds the candidates, splits each item into meaningful subtypes, and renders a short annotated list with links, so the user picks in a minute instead of browsing for half an hour. The user never searches Lazada themselves; the only hand work is pasting a fetch script into their browser console.

All user-facing text (item names, subtype labels, comments, notes in the rendered markdown) is in Russian. Search queries are Thai or English.

## Pipeline

```
queries.py  ──fetch──▶  data/raw/<md5(q)[:12]>_p<N>.json   (raw Lazada listItems per query)
                               │
                        analyze.py  →  ranked table to stdout (Claude reads it and picks)
                               │
picks.py + cart.py  ──render.py──▶  shortlist.md, remaining.md, shortlist-<date>.md
```

- `home.py` — data root: `$LAZADA_SCOUT_HOME`, or the checkout when unset. Everything below (data modules, `data/raw`, `data/pdp`, rendered files) lives there. The checkout holds a small sample; real shopping data lives in `~/.lazada-scout`.
- `queries.py` — `QUERIES`: item → list of `(subtype label, search query)`.
- `picks.py` — `PICKS`: item → `(subtype, note, [(itemId, short comment)])`. `BATCHES[<date>]` holds later shopping rounds, rendered to separate `shortlist-<date>.md` files (the user asked for separate files per round).
- `cart.py` — `CART`: what is already in the user's cart (per item, subtypes still to buy; empty list = covered). `BOUGHT_BATCHES`: rounds fully bought. Drives `remaining.md` and the "bought, closed" title suffix.
- `render.py` — looks every itemId up in `data/raw`; prices, ratings, review and sold counts are never typed by hand. Prints `missing ids` for picks that have no raw data — fix those before shipping.
- `analyze.py` — ranks local (non-cross-border, in-stock, ≥5 reviews) candidates by a Bayesian rating plus a log-sold bonus. `analyze.py [top] [item substring]`.
- `split_dump.py <dump.json>` — splits a `console_fetch.js` dump into `data/raw`.
- `variants.py <itemId>...` — prints size/colour/pack variants from the product page (cached in `data/pdp/`). PDP pages carry variant names only, not per-variant prices.

## Commands

```bash
.venv/bin/python analyze.py              # ranked candidates for every item
.venv/bin/python analyze.py 15 Швабра    # one item, top 15 per subtype
.venv/bin/python render.py               # regenerate all *.md; check "missing ids: []"
.venv/bin/python variants.py 4812542240  # variant names of a product
.venv/bin/python -m pytest -q            # three offline tests
LAZADA_SCOUT_HOME=~/.lazada-scout .venv/bin/python render.py   # against the real data
```

Python venv in `.venv` (Playwright installed). Node 18 on this machine is too old for Playwright, hence Python.

## Fetching data (anti-bot reality)

Lazada blocks scripted access fast; the working path is the browser console, not `scrape.py`.

1. Add new queries to `queries.py`, paste the same query strings into the `queries` array of `console_fetch.js`.
2. User pastes `console_fetch.js` into DevTools on a logged-in lazada.co.th tab. It fetches `/tag/<slug>/?ajax=true` per query, downloads `lazada_dump.json`, copies it to the clipboard and keeps `window.lazadaOut` (Chrome silently blocks repeated auto-downloads).
3. `split_dump.py lazada_dump.json` writes `data/raw/<md5(query)[:12]>_p1.json` per query. Then `analyze.py` and `render.py` see it.

Known facts, do not rediscover:
- `/catalog/?ajax=true&q=` survives ~75 requests then captcha; `/tag/<english-slug>/?ajax=true` lasts longer. Adding `q=` or `page=1` to `/tag/` triggers captcha. Thai slugs do not work as tags.
- Headless Playwright (`scrape.py`) now gets captcha too; `scrape.py --headed` lets a human solve it but is rarely worth it. VPN/datacenter IPs are blocked outright.
- PDP pages (`/products/pdp-i<id>.html`) still fetch via curl; `variants.py` relies on that.
- `/tag/` results are loose: sanity-check relevance of every candidate by name.
- Items with `location: None` or a "BRAND | name" title are cross-border; skip them. Only Thai sellers are listed.

## Picking rules

- Every item is split into subtypes that reflect a real choice (form factor, mechanism, size class), not into search queries. 2–4 candidates per subtype, each with a short Russian comment saying why it is there.
- Price shown is "от" (from): the minimum across variants. When size matters, say which variant to choose in the comment or note.
- When the user's requirement is specific (e.g. "bigger bin", "cable not adapter"), the note must carry it; the user noticed when a requirement was lost.
- Alternatives the user did not ask for go in as "Альтернатива: …" subtypes.
- New shopping round = new key in `BATCHES` dated `YYYY-MM-DD` (suffix `-2` for a second round the same day).

Per-item user requirements and round history live in Claude's memory file `lazada-scraping`, not in the repo; keep `picks.py` notes in sync with them.
