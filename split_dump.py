"""Split a console_fetch.js dump into data/raw: split_dump.py lazada_dump.json
Each query becomes data/raw/<md5(query)[:12]>_p1.json with the same {"mods": {"listItems": [...]}} shape.
"""
import json, hashlib, sys
from home import RAW

RAW.mkdir(parents=True, exist_ok=True)
for path in sys.argv[1:]:
    for q, d in json.load(open(path)).items():
        f = RAW / f"{hashlib.md5(q.encode()).hexdigest()[:12]}_p1.json"
        f.write_text(json.dumps({"mods": {"listItems": d["mods"].get("listItems", [])}}, ensure_ascii=False))
        print(f"{q!r}: {len(d['mods'].get('listItems', []))} items -> {f.name}")
