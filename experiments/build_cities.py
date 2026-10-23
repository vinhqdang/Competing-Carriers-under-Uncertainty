"""Build processed real-map inputs for each city.

Usage:
    python experiments/build_cities.py [city ...]

Reads data/raw/<city>.osm.pbf and the GHS-POP raster, writes data/processed/<city>/.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ccu.geo import build_city  # noqa: E402

CITIES = {
    "NewDelhi": {"display_name": "New Delhi", "continent": "Asia"},
    "Cairo": {"display_name": "Cairo", "continent": "Africa"},
    "Moscow": {"display_name": "Moscow", "continent": "Europe"},
    "BuenosAires": {"display_name": "Buenos Aires", "continent": "South America"},
    "NewYork": {"display_name": "New York", "continent": "North America"},
}
TIF = ROOT / "data" / "raw" / "ghs" / "GHS_POP_E2025_GLOBE_R2023A_4326_30ss_V1_0.tif"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cities", nargs="*", help=f"subset of {', '.join(CITIES)} (default: all)")
    parser.add_argument("--block", type=int, default=4, help="zone block size in raster cells (default 4)")
    args = parser.parse_args(argv)
    unknown = [c for c in args.cities if c not in CITIES]
    if unknown:
        parser.error(f"unknown city: {', '.join(unknown)}")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    for city in args.cities or list(CITIES):
        info = CITIES[city]
        t0 = time.perf_counter()
        meta = build_city(
            city,
            pbf_path=ROOT / "data" / "raw" / f"{city}.osm.pbf",
            tif_path=TIF,
            out_dir=ROOT / "data" / "processed" / city,
            continent=info["continent"],
            display_name=info["display_name"],
            block_cells=args.block,
        )
        logging.getLogger("ccu.geo").info(
            "%s done in %.1f s: zones=%d block=%d", city, time.perf_counter() - t0,
            meta["zone_count"], meta["block_cells"])


if __name__ == "__main__":
    main()
