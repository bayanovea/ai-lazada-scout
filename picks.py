# item -> list of (subtype, note, [(itemId, short comment)])
# Sample data, written by Claude Code after reading analyze.py output. Labels, notes and comments are
# Russian by design: this is what the user reads. Numbers are never written here; render.py looks them up.
PICKS = {
 "Швабра": [
  ("С ведром-центрифугой", "ведро в комплекте", [("5307905593", "базовый набор, +5 насадок"), ("2608425836", "Swash, брендовая"), ("11668472", "Poly-Brite Hurricane, премиум")]),
  ("Плоская с отжимом", "", [("1959626024", "Allsking"), ("5003599227", "широкая 42–50 см, +2 насадки"), ("3086934905", "«ленивая», 10K отзывов")]),
 ],
 "Весы настольные": [
  ("Кухонные до 10 кг, шаг 1 г", "для готовки: тарировка (обнулить вес миски), смена единиц", [("4786749506", "LI MEI, нержавейка, 10.7K отзывов"), ("4880950827", "та же модель; «от» — за вариант 500 г, нужен 10KG"), ("4695608316", "водозащита, зарядка по USB")]),
  ("Для кофе, шаг 0.1 г, с таймером", "3–5 кг; таймер — для пуровера", [("5277372577", "3 кг/0.1 г, 1.1K отзывов"), ("5046061068", "Timecafe, аккумулятор, тач-экран"), ("5545692250", "3 или 5 кг")]),
 ],
}

# later shopping rounds: date -> picks, rendered to shortlist-<date>.md (kept out of shortlist.md/remaining.md)
BATCHES = {}
