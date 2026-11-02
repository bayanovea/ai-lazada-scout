"""Fetch Lazada TH search results for every query in QUERIES into data/raw, through Chromium-Gost.

usage: fetch.py
Launches (or reuses) Chromium-Gost with its own profile and a CDP port, and runs the same
fetch('/tag/<slug>/?ajax=true') a logged-in lazada.co.th tab would. Queries that already have a raw
file are skipped, so a run stopped by a captcha continues where it left off.
"""
import hashlib, json, pathlib, random, subprocess, sys, time, urllib.parse, urllib.request
from home import RAW

GOST = "/Applications/Chromium-Gost.app/Contents/MacOS/Chromium-Gost"
PROFILE = pathlib.Path.home() / ".lazada-scout" / "browser-profile"  # per person, not per data root
CDP = "http://127.0.0.1:9333"
SITE = "https://www.lazada.co.th/"
CAPTCHA_WAIT = 600

def slug(q):
    return urllib.parse.quote(q.lower().replace(" ", "-"), safe="!~*'()")  # = encodeURIComponent

def raw_path(q):
    return RAW / f"{hashlib.md5(q.encode()).hexdigest()[:12]}_p1.json"

def todo(queries):
    """-> (queries to fetch, queries already on disk), unique, in QUERIES order."""
    qs = list(dict.fromkeys(q for subs in queries.values() for _, q in subs))
    return [q for q in qs if not raw_path(q).exists()], [q for q in qs if raw_path(q).exists()]

def classify(url, text):
    """-> ("ok", listItems) | ("captcha", None) | ("failed", None)."""
    # the anti-bot answers ajax with {"rgv587_flag": ..., "url": ".../_____tmd_____/punish..."} or redirects there
    if "punish" in url or "rgv587_flag" in text[:2000] or "_____tmd_____" in text[:5000]:
        return "captcha", None
    try:
        return "ok", json.loads(text)["mods"].get("listItems", [])
    except (ValueError, KeyError, TypeError, AttributeError):
        return "failed", None

def cdp_version():
    try:
        with urllib.request.urlopen(CDP + "/json/version", timeout=2) as r:
            return json.load(r)
    except OSError:
        return None

def ensure_browser():
    v = cdp_version()
    if v is None:
        PROFILE.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.Popen([GOST, f"--user-data-dir={PROFILE}", f"--remote-debugging-port={CDP.rsplit(':', 1)[1]}",
                              "--no-first-run", "--no-default-browser-check"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        except OSError as e:
            sys.exit(f"cannot launch {GOST}: {e}")
        for _ in range(30):
            time.sleep(0.5)
            if (v := cdp_version()): break
        else:
            sys.exit(f"Chromium-Gost did not open {CDP}")
    if "Chromium GOST" not in v.get("User-Agent", ""):
        sys.exit(f"{CDP} is not Chromium-Gost: {v.get('User-Agent')}")

FETCH_JS = """async url => {
    const r = await fetch(url, {credentials: 'include'});
    return {url: r.url, text: await r.text()};
}"""

def wait_for_human(page, url):
    """Show the captcha in the tab and wait until it is solved. False on timeout."""
    page.goto(SITE.rstrip("/") + url, wait_until="domcontentloaded", timeout=40000)
    if "punish" in page.url:
        print("CAPTCHA: реши капчу в окне Chromium-Gost (жду до 10 минут)", flush=True)
        for _ in range(CAPTCHA_WAIT // 2):
            page.wait_for_timeout(2000)
            if "punish" not in page.url: break
        else:
            return False
    page.goto(SITE, wait_until="domcontentloaded", timeout=40000)
    return True

def run(page, qs):
    """Fetch qs one by one; write each file at once. -> (fetched, failed, left unfetched after a stop)."""
    fetched, failed = [], []
    for i, q in enumerate(qs):
        if i: time.sleep(random.uniform(3, 6))
        url = f"/tag/{slug(q)}/?ajax=true"
        for _ in range(3):  # bounded: a captcha the tab does not show would otherwise loop without a human
            try:
                kind, items = classify(**page.evaluate(FETCH_JS, url))
            except Exception as e:
                if page.is_closed():
                    print("the fetch tab was closed, stopping", flush=True)
                    return fetched, failed, qs[i:]
                print(f"FAIL {q!r}: {type(e).__name__} {e!s:.100}", flush=True)
                kind, items = "error", None
            if kind != "captcha": break
            if not wait_for_human(page, url):
                return fetched, failed, qs[i:]
            time.sleep(random.uniform(3, 6))
        else:
            return fetched, failed, qs[i:]
        if kind == "ok":
            raw_path(q).write_text(json.dumps({"mods": {"listItems": items}}, ensure_ascii=False))
            fetched.append(q)
            print(f"ok {q!r}: {len(items)} items", flush=True)
        else:
            failed.append(q)
            if kind == "failed": print(f"FAIL {q!r}: no search results (no tag page?)", flush=True)
    return fetched, failed, []

def main():
    from playwright.sync_api import sync_playwright
    from queries import QUERIES
    RAW.mkdir(parents=True, exist_ok=True)
    qs, skipped = todo(QUERIES)
    print(f"{len(qs)} to fetch, {len(skipped)} already on disk", flush=True)
    left = []
    if qs:
        ensure_browser()
        with sync_playwright() as pw:
            b = pw.chromium.connect_over_cdp(CDP)
            page = b.contexts[0].new_page()
            page.goto(SITE, wait_until="domcontentloaded", timeout=40000)
            fetched, failed, left = run(page, qs)
            page.close()
            b.close()  # disconnects only: the browser stays open with its session
    else:
        fetched, failed = [], []
    print(f"fetched {len(fetched)}, skipped {len(skipped)}, failed {len(failed)}"
          + (f", not fetched: {left}" if left else ""))
    sys.exit(1 if left else 0)

if __name__ == "__main__":
    main()
