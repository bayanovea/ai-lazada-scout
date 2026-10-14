"""Data root for every script: $LAZADA_SCOUT_HOME, or the checkout itself when unset.

The root holds queries.py, picks.py, cart.py, data/raw, data/pdp and the rendered *.md files,
so real shopping data can live outside the repository (e.g. ~/.lazada-scout) with the same layout.
"""
import os, pathlib, sys

HOME = pathlib.Path(os.environ.get("LAZADA_SCOUT_HOME") or pathlib.Path(__file__).resolve().parent)
RAW = HOME / "data" / "raw"
PDP = HOME / "data" / "pdp"

if str(HOME) not in sys.path:
    sys.path.insert(0, str(HOME))  # so `from queries import QUERIES` finds the data modules in HOME
