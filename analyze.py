"""Rank fetched candidates per item/subtype and print a compact table for review.

usage: analyze.py [top] [item substring]
Only Thai sellers in stock with at least 5 reviews are listed, ordered by a Bayesian rating
plus a small bonus for the number sold.
"""
import json, hashlib, math, re, sys
from home import RAW

OVERSEAS = {"China", "Hong Kong", "Overseas", "Mainland China", "South Korea", "Japan", "Taiwan", "Singapore", "Malaysia"}
PRIOR_R, PRIOR_N = 4.3, 30   # prior rating and its weight in reviews, pulls thin ratings towards 4.3
MIN_REVIEWS = 5
SOLD_BONUS = 0.05            # per decade of units sold

def sold(s):
    """'26.9K sold' -> 26900.0; missing or unparsable -> 0."""
    m = re.match(r"([\d.]+)\s*([KkMm]?)", (s or "").replace(",", ""))
    if not m: return 0
    return float(m[1]) * {"": 1, "k": 1e3, "m": 1e6}[m[2].lower()]

def bayes(rating, reviews):
    return (rating * reviews + PRIOR_R * PRIOR_N) / (reviews + PRIOR_N)

def score(row):
    return row["bayes"] + SOLD_BONUS * math.log10(row["sold"] + 1)

def is_local(it):
    """Thai seller, in stock. Cross-border listings carry an overseas or empty location."""
    loc = it.get("location")
    return bool(loc) and loc not in OVERSEAS and it.get("inStock", True)

def load(q):
    h = hashlib.md5(q.encode()).hexdigest()[:12]
    out = []
    for f in sorted(RAW.glob(f"{h}_p*.json")):
        out += json.loads(f.read_text())["mods"].get("listItems", [])
    return out

def rows(q, items=None):
    res, seen = [], set()
    for it in load(q) if items is None else items:
        if it.get("tItemType") != "nt_product" or it["itemId"] in seen: continue
        seen.add(it["itemId"])
        if not is_local(it): continue
        r = float(it.get("ratingScore") or 0); n = int(it.get("review") or 0)
        res.append(dict(id=it["itemId"], name=it["name"], price=float(it.get("price") or 0),
            r=r, n=n, sold=sold(it.get("itemSoldCntShow")), loc=it.get("location", "?"), bayes=bayes(r, n),
            mall=any(i.get("bizType") in ("official", "LazMall") or "mall" in str(i.get("domClass", "")).lower() for i in it.get("icons", [])),
            ad=it.get("isSponsored", False), url="https://www.lazada.co.th/products/pdp-i%s.html" % it["itemId"]))
    return res

def ranked(q, items=None):
    rs = [x for x in rows(q, items) if x["n"] >= MIN_REVIEWS]
    rs.sort(key=score, reverse=True)
    return rs

if __name__ == "__main__":
    from queries import QUERIES
    top = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    only = sys.argv[2] if len(sys.argv) > 2 else None
    for item, subs in QUERIES.items():
        if only and only not in item: continue
        print(f"\n######## {item}")
        for label, q in subs:
            rs = ranked(q)
            print(f"\n== {label} [{q}] — {len(rs)} local w/ >={MIN_REVIEWS} reviews")
            for x in rs[:top]:
                print(f"  ฿{x['price']:>6.0f} | {x['r']:.2f}★ {x['n']:>5} rev | {x['sold']:>7.0f} sold | {x['loc'][:10]:<10} | {x['id']} | {x['name'][:110]}")
