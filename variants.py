"""Print variant names (size/colour/pack) from product pages: variants.py <itemId>...
Pages are fetched with curl once and cached in data/pdp/. They carry variant names only, not per-variant prices.
"""
import sys, re, json, subprocess, time
from home import PDP

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
PDP.mkdir(parents=True, exist_ok=True)
for iid in sys.argv[1:]:
    p = PDP / f"{iid}.html"
    if not p.exists():
        subprocess.run(["curl", "-s", "-m", "20", "-A", UA, f"https://www.lazada.co.th/products/pdp-i{iid}.html", "-o", str(p)]); time.sleep(2)
    s = p.read_text(errors="ignore")
    if "punish" in s[:3000]: print(iid, "BLOCKED"); p.unlink(); continue  # captcha page, do not cache it
    m = re.search(r'"skuBase":\{"properties":(\[.*?\]),"skus"', s)
    props = json.loads(m[1]) if m else []
    print(iid, " || ".join(pr["name"] + ": " + " | ".join(v["name"] for v in pr["values"]) for pr in props))
