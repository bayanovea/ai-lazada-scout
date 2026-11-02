# Design

## Context

Motivation: see proposal.md. The working request today is `console_fetch.js`: `fetch('/tag/<slug>/?ajax=true', {credentials: 'include'})` from a logged-in lazada.co.th tab, 3–6 s apart. Slug rule: `encodeURIComponent(q.toLowerCase().replace(/ /g, '-'))`, the same as `scrape.py:31`. The raw file name `md5(query)[:12]_p1.json` is what `analyze.py` and `render.py` look up.

The 2026-11-02 spike: Chromium-Gost 146 launched with `--user-data-dir=<dir> --remote-debugging-port=9333`, Playwright `connect_over_cdp("http://127.0.0.1:9333")`, `page.goto("https://www.lazada.co.th/")`, then `page.evaluate` of the fetch: 200, 40 items, `navigator.webdriver === false`.

## Goals / Non-Goals

**Goals:**
- One command per round, run by Claude: `.venv/bin/python fetch.py`.
- Same request, pace and output as the console path.

**Non-Goals:**
- Pages beyond 1: `page=` on `/tag/` triggers captcha (CLAUDE.md, known facts).
- PDP fetching: `variants.py` keeps using curl.
- Detecting whether the user is logged in. The spike fetched fine without login; login only improves the session's standing.

## Decisions

- **Launch Chromium-Gost ourselves, attach over CDP.** Not `chromium.launch_persistent_context`: that runs Playwright's bundled Chromium with automation flags (`navigator.webdriver` true), which is what `scrape.py` did and what got captcha. A normally launched browser that we only attach to looks like the user's browser. Binary: `/Applications/Chromium-Gost.app/Contents/MacOS/Chromium-Gost`, flags `--user-data-dir=~/.lazada-scout/browser-profile --remote-debugging-port=9333 --no-first-run --no-default-browser-check`, started detached.
- **Reuse a running instance.** If `http://127.0.0.1:9333/json/version` answers, attach; otherwise launch and poll it for up to 15 s. After the run, disconnect and leave the browser open: a solved captcha and a fresh session carry over to the next round, and the user closes it when they like.
- **Fixed profile path `~/.lazada-scout/browser-profile`**, not under `$LAZADA_SCOUT_HOME`: the login belongs to the person, not to a data root, and with `LAZADA_SCOUT_HOME` unset the profile would land in the checkout.
- **Port 9333, not 9222**, so it does not collide with another debugging browser.
- **Fetch with `page.evaluate`, not `page.goto` per query.** The request comes from the page with its cookies and referer, exactly like the console script. Pace: `random.uniform(3, 6)` seconds between requests.
- **Classify each response in the page**: JSON with `mods` → ok; final URL or body containing `punish` / captcha markup → captcha; anything else → failed (no tag page). Only list items are stored, as `split_dump.py` did.
- **Captcha handling**: navigate the tab to the blocked URL so the captcha is visible, print one line asking the user to solve it in the Chromium-Gost window, poll every 2 s until the tab URL no longer contains `punish`, up to 10 minutes; then go back to lazada.co.th and retry the query, at most 3 captcha rounds per query so a captcha the tab does not show cannot loop without a human. Timeout or a third captcha → print the queries left and exit non-zero.
- **Write each file as soon as it is fetched**, so a stop or crash keeps the work and a re-run continues (skip-existing is the resume mechanism).
- **A closed fetch tab stops the run** with the queries left, like a captcha timeout: every later `evaluate` would fail at once.
- **Delete `console_fetch.js`, `split_dump.py`, `scrape.py`** rather than keep them as fallbacks: the user chose a single path; git history keeps them.
- **Pure helpers (`slug`, raw file path, todo list from `QUERIES` minus existing files, response classification) are plain functions** so they get offline tests next to `tests/test_scout.py`; the browser part is checked by a real run.

## Risks / Trade-offs

- [Lazada starts flagging Chromium-Gost too] → the captcha wait lets the user clear it by hand; if it happens every round, revisit with the user (the IP-level block of 2026-10-06 would hit any path).
- [Chromium-Gost update changes the binary path or CDP behaviour] → the path is one constant; a failed launch prints the path it tried.
- [Port 9333 taken by something else] → `/json/version` answers but is not our browser; check the `User-Agent` contains `Chromium GOST` and fail with a clear message otherwise.
- [Running browser was started without our profile] → a Chromium-Gost started by the user normally has no CDP port, so it never answers on 9333; a second instance with our profile starts next to it.

## Migration Plan

Delete the three old files in the same change; the raw file format is unchanged, so existing `data/raw` in `~/.lazada-scout` keeps working. Rollback: restore them from git.
