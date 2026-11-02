# search-fetch Specification

## Purpose

Gets Lazada TH search results for every query in `QUERIES` into `data/raw` without manual steps, through a real browser the anti-bot accepts.

## Requirements

### Requirement: Fetch missing queries into raw files
The fetcher SHALL request every query from `QUERIES` that has no `data/raw/<md5(query)[:12]>_p1.json` yet, and write each result to that path as `{"mods": {"listItems": [...]}}`, the shape `analyze.py` and `render.py` read.

#### Scenario: New query is fetched
- **WHEN** `QUERIES` contains a query with no raw file and the fetcher runs
- **THEN** `data/raw/<md5(query)[:12]>_p1.json` exists with the query's list items, and `analyze.py` shows its candidates

#### Scenario: Already fetched query is skipped
- **WHEN** a query already has its raw file
- **THEN** the fetcher sends no request for it and leaves the file unchanged

### Requirement: Fetch through a dedicated Chromium-Gost browser
The fetcher SHALL send requests only from a lazada.co.th tab of Chromium-Gost running with a dedicated persistent profile. It SHALL reuse that browser when it is already running and launch it in a visible window otherwise. It SHALL NOT fall back to curl or a headless browser.

#### Scenario: Browser not running
- **WHEN** the fetcher starts and the dedicated Chromium-Gost is not running
- **THEN** it launches Chromium-Gost with the dedicated profile in a visible window and fetches through it

#### Scenario: Browser already running
- **WHEN** the dedicated Chromium-Gost is already running
- **THEN** the fetcher uses it without launching a second instance

#### Scenario: Login survives runs
- **WHEN** the user has logged in to Lazada once in the dedicated browser
- **THEN** later runs send requests with that session, without logging in again

### Requirement: Human pace between requests
The fetcher SHALL wait a random 3 to 6 seconds between consecutive requests.

#### Scenario: Several queries
- **WHEN** the fetcher requests more than one query
- **THEN** consecutive requests are at least 3 seconds apart

### Requirement: Captcha waits for the user
When a response is a captcha instead of JSON, the fetcher SHALL show the captcha in the browser window, tell the user in its output to solve it there, wait up to 10 minutes, and then retry the same query and continue. If the captcha is not solved in time it SHALL stop, keeping every file already written.

#### Scenario: Captcha solved
- **WHEN** a request gets a captcha and the user solves it within 10 minutes
- **THEN** the fetcher retries that query and continues with the rest

#### Scenario: Captcha not solved
- **WHEN** a request gets a captcha and 10 minutes pass without it being solved
- **THEN** the fetcher stops with a message naming the queries not fetched, and the raw files written before the captcha remain

#### Scenario: Re-run after a stop
- **WHEN** the fetcher is run again after stopping on a captcha
- **THEN** it fetches only the queries that still have no raw file

### Requirement: Query without results does not stop the run
When a query returns neither JSON nor a captcha (for example, Lazada has no tag page for it), the fetcher SHALL report it as failed, write no file for it, and continue with the next query.

#### Scenario: No tag page
- **WHEN** one query has no tag page on Lazada
- **THEN** that query is reported as failed, has no raw file, and the other queries are fetched

### Requirement: Run summary
At the end of a run the fetcher SHALL print, per query, its item count or failure, and totals of fetched, skipped and failed queries.

#### Scenario: Mixed run
- **WHEN** a run fetches some queries, skips some and fails one
- **THEN** the output lists each fetched and failed query and the three totals
