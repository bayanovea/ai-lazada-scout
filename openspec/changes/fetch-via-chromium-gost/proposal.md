# Proposal

## Why

Every shopping round the user pastes `console_fetch.js` into DevTools, waits for it to finish and reports where the dump landed, then Claude runs `split_dump.py`. Scripted fetching was dropped because Lazada blocked it (headless Playwright got captcha, and ~75 requests in a row got the home IP blocked for 5+ hours, curl included), while the user's real logged-in browser kept working. A spike on 2026-11-02 showed the same in-page `fetch` works when a script drives Chromium-Gost over CDP (`navigator.webdriver` is `false`), so the manual steps can go.

## What Changes

- New `fetch.py`: reads `QUERIES`, launches (or reuses) Chromium-Gost with its own persistent profile and a CDP port, runs `fetch('/tag/<slug>/?ajax=true')` from a lazada.co.th tab for every query without raw data, and writes `data/raw/<md5(query)[:12]>_p1.json` directly.
- On captcha the script asks the user to solve it in the Chromium-Gost window, waits up to 10 minutes, then resumes; everything fetched so far stays on disk.
- **BREAKING** Remove `console_fetch.js`, `split_dump.py` and `scrape.py`. Chromium-Gost is the only fetch path; no curl or headless fallback.
- Update `CLAUDE.md` ("Pipeline", "Commands", "Fetching data") and `README.md` to describe the new round: add queries, run `fetch.py`.

## Capabilities

### New Capabilities
- `search-fetch`: getting Lazada search results for the queries in `QUERIES` into `data/raw`, in the shape `analyze.py` and `render.py` read.

### Modified Capabilities

## Impact

- Code: new `fetch.py`; `console_fetch.js`, `split_dump.py`, `scrape.py` deleted; `analyze.py`, `render.py` and the raw file format unchanged.
- Dependencies: Playwright (already in `.venv`) becomes required, used only to connect over CDP; `requirements.txt` updated. Needs `/Applications/Chromium-Gost.app`.
- Local state: browser profile at `~/.lazada-scout/browser-profile` (cookies, login), outside the repo.
- Docs: `CLAUDE.md`, `README.md`.
