"""Render picks.py into Markdown shortlists. Prices, ratings, review and sold counts are looked up
in the raw data, never typed by hand. Prints the ids that have no raw data: fix those before use.

Outputs (in the data root): shortlist.md, remaining.md (subtypes not yet in the cart) and one
shortlist-<date>.md per later shopping round in picks.BATCHES.
"""
import json, re
from home import HOME, RAW
from analyze import sold

# Russian by design: the rendered list is read by a Russian-speaking user.
HEADER = "Цена — минимальная по вариантам (размер/цвет), отсюда «от». Только продавцы из Таиланда (без доставки из Китая). Рейтинг · отзывы · продано."
TITLE = "Lazada TH — подборка"
TITLE_REMAINING = "Lazada TH — докупить (нет в корзине)"
BOUGHT_SUFFIX = " — куплено, закрыто"
NO_REVIEWS = "нет отзывов"
REVIEWS, SOLD = "отз", "прод"

def index(raw=RAW):
    """itemId -> listing, first occurrence wins."""
    idx = {}
    for f in sorted(raw.glob("*.json")):
        for it in json.loads(f.read_text())["mods"].get("listItems", []):
            if it.get("tItemType") == "nt_product": idx.setdefault(it["itemId"], it)
    return idx

def k(n): return f"{n/1000:.1f}K".replace(".0K", "K") if n >= 1000 else f"{n:.0f}"

def render(picks, idx, title):
    """Return (markdown, missing ids)."""
    out, missing = [f"# {title}", "", HEADER, ""], []
    for item, subs in picks.items():
        out.append(f"## {item}")
        for sub, note, lst in subs:
            out.append(f"**{sub}**" + (f" — _{note}_" if note else ""))
            for iid, comment in lst:
                it = idx.get(iid)
                if not it: missing.append(iid); continue
                label = comment or re.sub(r"\s+", " ", it["name"])[:60].rstrip()
                stats = (f"{float(it['ratingScore']):.2f}★ ({k(int(it['review']))} {REVIEWS}, " if it.get("review") else f"{NO_REVIEWS} (")
                out.append(f"- [{label}](https://www.lazada.co.th/products/pdp-i{iid}.html) — от ฿{float(it['price']):.0f} · "
                           + stats + f"{k(sold(it.get('itemSoldCntShow')))} {SOLD})")
            out.append("")
    return "\n".join(out), missing

def remaining(picks, cart):
    """Subtypes still to buy: items absent from the cart keep every subtype, [] means covered."""
    return {item: [s for s in subs if s[0] in cart.get(item, [s[0] for s in subs])] for item, subs in picks.items()}

if __name__ == "__main__":
    from picks import PICKS, BATCHES
    from cart import CART, BOUGHT_BATCHES
    idx, missing = index(), []
    jobs = [(PICKS, "shortlist.md", TITLE),
            ({i: s for i, s in remaining(PICKS, CART).items() if s}, "remaining.md", TITLE_REMAINING)]
    jobs += [(p, f"shortlist-{d}.md", f"{TITLE} {d}" + (BOUGHT_SUFFIX if d in BOUGHT_BATCHES else "")) for d, p in BATCHES.items()]
    for picks, name, title in jobs:
        md, miss = render(picks, idx, title)
        (HOME / name).write_text(md)
        missing += miss
    print("missing ids:", missing)
