"""Fallback fetcher: Lazada TH search results via the /tag/<slug>/?ajax=true JSON endpoint in a
Playwright browser. The browser-console path (console_fetch.js) is the one that works today;
headless Playwright now gets a captcha quickly.

usage: scrape.py [pages] [--headed]
--headed opens a visible window; if Lazada shows a captcha, a human solves it there and scraping resumes.
"""
import asyncio, json, random, sys, urllib.parse, hashlib
from playwright.async_api import async_playwright
from home import RAW as OUT
from queries import QUERIES

OUT.mkdir(parents=True, exist_ok=True)
args = [a for a in sys.argv[1:] if not a.startswith("--")]
PAGES = int(args[0]) if args else 2
HEADED = "--headed" in sys.argv

def fname(q, page): return OUT / f"{hashlib.md5(q.encode()).hexdigest()[:12]}_p{page}.json"

async def main():
    todo = [(q, p) for subs in QUERIES.values() for _, q in subs for p in range(1, PAGES + 1)]
    todo = [t for t in todo if not fname(*t).exists()]
    print(f"{len(todo)} requests to do", flush=True)
    async with async_playwright() as pw:
        b = await pw.chromium.launch(headless=not HEADED)
        ctx = await b.new_context(locale="en-US", viewport={"width": 1280, "height": 860})
        page = await ctx.new_page()
        for q, p in todo:
            # /catalog/?ajax is the first thing Lazada's anti-bot blocks; /tag/<slug>/?ajax serves the same JSON
            slug = urllib.parse.quote(q.lower().replace(" ", "-"))
            url = f"https://www.lazada.co.th/tag/{slug}/?ajax=true" + (f"&page={p}" if p > 1 else "")
            d = None
            for attempt in range(2):
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=40000)
                    if "punish" in page.url:
                        print("punish at", url, flush=True)
                        if not HEADED:
                            # risk scoring is per request/session: back off and retry with fresh cookies
                            await ctx.close()
                            ctx = await b.new_context(locale="en-US", viewport={"width": 1280, "height": 860})
                            page = await ctx.new_page()
                            await asyncio.sleep(20)
                            continue
                        print("CAPTCHA: solve it in the browser window (waiting up to 10 min)", flush=True)
                        for _ in range(300):
                            await page.wait_for_timeout(2000)
                            if "punish" not in page.url: break
                        print("captcha solved", flush=True)
                        await page.wait_for_timeout(2000)
                        if "ajax=true" not in page.url: continue  # not redirected back: reload target
                    d = json.loads(await page.evaluate("document.body.innerText"))
                    break
                except Exception as e:
                    print(f"retry {q!r} p{p}: {type(e).__name__} {e!s:.100} url={page.url[:100]}", flush=True)
            if d is None:
                print(f"BLOCKED on {q!r} p{p}", flush=True); continue
            fname(q, p).write_text(json.dumps(d, ensure_ascii=False))
            print(f"ok {q!r} p{p}: {len(d['mods'].get('listItems', []))} items", flush=True)
            await asyncio.sleep(random.uniform(12, 18))
        print("done", flush=True)
        await b.close()

if __name__ == "__main__":
    asyncio.run(main())
