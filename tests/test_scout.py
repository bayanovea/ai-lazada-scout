"""Offline tests on small fixtures: ranking order, local-seller filter, missing ids in render."""
import analyze, render

def listing(iid, rating, reviews, sold, location="Bangkok", in_stock=True):
    return dict(itemId=iid, name=f"item {iid}", price="100", ratingScore=str(rating), review=str(reviews),
                itemSoldCntShow=f"{sold} sold", location=location, inStock=in_stock, tItemType="nt_product")

def test_ranking_prefers_many_reviews_over_thin_perfect_rating():
    items = [
        listing("perfect-thin", 5.0, 6, 10),      # 5.0 from 6 reviews is pulled hard towards the 4.3 prior
        listing("solid", 4.9, 2000, 5000),         # many reviews, many sold
        listing("good-fewer-sold", 4.9, 2000, 50), # same rating, fewer sold: log-sold bonus decides
        listing("too-few", 5.0, 3, 999999),        # below MIN_REVIEWS, dropped regardless of sold count
    ]
    assert [r["id"] for r in analyze.ranked("q", items)] == ["solid", "good-fewer-sold", "perfect-thin"]

def test_local_seller_filter():
    assert analyze.is_local(listing("a", 4.9, 10, 10, location="Nonthaburi"))
    assert not analyze.is_local(listing("b", 4.9, 10, 10, location="China"))
    assert not analyze.is_local(listing("c", 4.9, 10, 10, location=None))      # cross-border listings carry no location
    assert not analyze.is_local(listing("d", 4.9, 10, 10, in_stock=False))
    assert analyze.sold("26.9K sold") == 26900 and analyze.sold(None) == 0

def test_render_reports_missing_ids_and_never_invents_numbers():
    idx = {"111": listing("111", 4.87, 1234, 5600)}
    picks = {"Швабра": [("плоская", "note", [("111", "comment"), ("999", "no raw data")])]}
    md, missing = render.render(picks, idx, "title")
    assert missing == ["999"]
    assert "pdp-i111.html) — от ฿100 · 4.87★ (1.2K отз, 5.6K прод)" in md
    assert "999" not in md
