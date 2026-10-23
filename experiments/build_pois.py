"""Add OpenStreetMap points of interest to the processed real-map inputs of each city.

Usage:
    python experiments/build_pois.py [city ...]

Reads data/raw/<city>.osm.pbf and data/processed/<city>/{zones.csv, zone_bounds.npy, meta.json}.
Writes data/processed/<city>/pois.csv, adds n_* counts and depot_score to zones.csv and
poi_counts to meta.json. Existing builds are not rerun.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ccu.geo import build_city_pois  # noqa: E402

CITIES = ["NewDelhi", "Cairo", "Moscow", "BuenosAires", "NewYork", "Bombay", "London", "Paris", "Berlin"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cities", nargs="*", help=f"subset of {', '.join(CITIES)} (default: all)")
    args = parser.parse_args(argv)
    unknown = [c for c in args.cities if c not in CITIES]
    if unknown:
        parser.error(f"unknown city: {', '.join(unknown)}")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    for city in args.cities or CITIES:
        t0 = time.perf_counter()
        build_city_pois(
            pbf_path=ROOT / "data" / "raw" / f"{city}.osm.pbf",
            out_dir=ROOT / "data" / "processed" / city,
        )
        logging.getLogger("ccu.geo").info("%s POIs done in %.1f s", city, time.perf_counter() - t0)


if __name__ == "__main__":
    main()
