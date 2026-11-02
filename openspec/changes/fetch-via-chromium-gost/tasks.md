# Tasks

## 1. Fetcher

- [x] 1.1 Add `fetch.py` pure helpers (slug, raw file path, todo list from `QUERIES` minus existing raw files, response classification ok / captcha / failed) and offline tests for them in `tests/`; verify `.venv/bin/python -m pytest -q` passes
- [x] 1.2 Add browser handling to `fetch.py`: attach to Chromium-Gost on port 9333 or launch it detached with `~/.lazada-scout/browser-profile`, check the `Chromium GOST` user agent, open lazada.co.th; verify a run with the browser closed launches one window and a second run reuses it (no second process)
- [x] 1.3 Add the fetch loop: in-page `fetch` per todo query, 3–6 s pace, write `{"mods": {"listItems": [...]}}` per query immediately, per-query line and totals at the end; verify with a query added to the sample `queries.py` that `analyze.py` shows its candidates and a re-run reports it as skipped
- [x] 1.4 Add captcha handling: show the blocked URL in the tab, one-line prompt, poll up to 10 minutes, retry (at most 3 captcha rounds per query), exit non-zero with the queries left on timeout; verify the logic with a test on the classifier and, if a captcha shows up in a real run, by solving it in the window

## 2. Remove the manual path

- [x] 2.1 Delete `console_fetch.js`, `split_dump.py`, `scrape.py` (check `git diff console_fetch.js` first: it has an uncommitted user edit) and move Playwright from optional to required in `requirements.txt`; verify `grep -rn 'console_fetch\|split_dump\|scrape.py' --include='*.py' .` finds nothing
- [x] 2.2 Rewrite `CLAUDE.md` ("Pipeline", "Commands", "Fetching data") and the fetch parts of `README.md` for `fetch.py`, including the one-time optional login in the Chromium-Gost window and the stale "Node 18" line; verify no doc still tells the user to paste a script

## 3. End to end

- [x] 3.1 Run `LAZADA_SCOUT_HOME=~/.lazada-scout .venv/bin/python fetch.py` against the real data, then `render.py`; verify `missing ids: []` and that no manual step was needed
- [x] 3.2 Cleanup pass before commit (residue / transient state / open questions)
