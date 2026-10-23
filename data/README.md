# Data

## Raw inputs (`data/raw/`, not modified by the pipeline)

- `<City>.osm.pbf`: OpenStreetMap extracts for NewDelhi, Cairo, Moscow, BuenosAires, NewYork, Bombay (Mumbai), from BBBike (https://download.BBBike.org), replication timestamp 2026-10-16T23:00:00Z.
- `ghs/GHS_POP_E2025_GLOBE_R2023A_4326_30ss_V1_0.tif`: GHSL GHS-POP R2023A, epoch 2025, EPSG:4326, 30 arc-second cells (about 0.00833 deg), people per cell.

## Processed outputs (`data/processed/<city>/`)

- `zones.csv`: one row per populated zone (population >= 1). `lon`, `lat` are the population-weighted centroid (deg). `pop` is people. `area_km2` is the spherical area of the block. `road_km_all` covers all drivable highway classes, `road_km_major` covers motorway, trunk, primary, secondary, tertiary and their `_link` variants (km). `lane_km_major` is the major road length times lanes (km). `node` is the index of the nearest node of `major_graph.npz`.
- `zone_bounds.npy`: (Z, 4) west, south, east, north of each zone block (deg).
- `major_graph.npz`: undirected major-road graph, largest connected component. Arrays: `node_id` (OSM id), `lon`, `lat`, `src`, `dst`, `length_m`, `free_speed_kmh`, `time_s`, `road_class_code` (0-4 major classes, 5-9 the same classes as links), `segments` (E, 2, 2) for plotting.
- `travel_time_matrix.npy`: (Z, Z) float32 free-flow travel time in seconds between zone centroids, graph shortest path plus 120 s access at each end.
- `meta.json`: bbox, block size, zone count, population totals, road totals, graph counts, source strings and build settings. After the POI step it also holds `poi_counts`, `poi_osm_replication_timestamp` and `poi_build_seconds`.
- `pois.csv`: one row per OSM point of interest in the extract (see below). `lon`, `lat` are node locations or the mean of a way's node locations (deg). `osm_type` is `node` or `way`, `osm_id` the OSM id, `name` the `name` tag (may be empty), `category` one of the six classes, `subtype` the matched tag value, `zone_id` the zone containing the point or -1 when outside all zones.
- `zones.csv` also has per-zone columns `n_shop`, `n_market`, `n_depot`, `n_post_office`, `n_locker`, `n_wholesale` (POI counts inside the zone block) and `depot_score` = `n_depot` + 0.5 `n_wholesale` + 0.25 `n_post_office`. The original columns are unchanged.

## Units and conventions

- Population: persons. Density: people per km^2. Distances: metres in the graph, km in zone tables.
- Free-flow speeds: motorway 80, trunk 60, primary 45, secondary 35, tertiary 30 km/h; link roads 0.7 times these.
- Lanes: OSM `lanes` tag when present (first integer); otherwise motorway 3, trunk 2, primary 2, secondary 1, tertiary 1; link roads 1.
- Zones are 4 x 4 raster cells (about 3.7 km) by default, aligned to the global raster grid and kept only when fully inside the extract bbox.
- Roads are assigned to zones by segment midpoint. Segments outside populated zones count only in the graph and the extract totals.

## Points of interest (OpenStreetMap)

Read from the same `.osm.pbf` extracts in one pass (`ccu.geo.extract_pois`). Nodes are taken at their location, ways at the mean of their node locations (not an area centroid). Relations are skipped. Each object is counted once, in the first matching class of this order: depot, locker, post_office, wholesale, market, shop.

| Category | OSM tags |
| --- | --- |
| `shop` | `shop=*` except `shop=vacant` and `shop=no`; `subtype` = shop value |
| `market` | `amenity=marketplace` |
| `depot` | `amenity=post_depot`; `building=warehouse`; `industrial=warehouse\|logistics\|distribution`; `office=logistics\|courier`; `landuse=industrial` ways whose name contains warehouse, logistic, depot, distribution, cargo, freight, courier or fulfil (case-insensitive) |
| `post_office` | `amenity=post_office` |
| `locker` | `amenity=parcel_locker`; `amenity=vending_machine` with `vending` listing `parcel_pickup` or `parcel_mail_in` |
| `wholesale` | `shop=wholesale`, `shop=trade` (so these are not counted under `shop`) |

Zone counts use the zone rectangles in `zone_bounds.npy` as half-open intervals, the same convention as `zone_index_of_points`. Points outside every zone stay in `pois.csv` with `zone_id` -1.

`ccu.geo.select_depot_sites(zones, n, rng, min_sep_km)` ranks zones by `depot_score`, breaks ties and zero scores by closeness of the centroid distance (from the population-weighted centroid) to the 70th-percentile ring, then by random key, and keeps zones at least `min_sep_km` apart. It returns fewer than `n` sites, with a warning, when the spacing cannot be met.

Caveats:

- OSM completeness varies strongly by city. Cairo has about 2.5 k points for 42 zones and Moscow about 58 k for 160 zones. These differences reflect mapping effort and tagging habits, not the amount of commercial or logistics activity.
- The counts are not business census data. They are a sample of mapped features at the extract date.
- `depot` mixes warehouses with courier and logistics offices (for example 35 `courier` points in Buenos Aires, and 173 `logistics` points in Moscow, where the subtype does not show whether the tag was `office` or `industrial`). Some named businesses carry `building=warehouse`, for example a coffee roaster in New York, so the tag does not always mean a storage facility. The name rule for `landuse=industrial` also matches any name containing "depot", such as a bus depot.
- `wholesale` is mostly `shop=trade` in Buenos Aires (590 of 754) and New York; this is a tagging convention, not a verified wholesale count.
- `locker` is zero in Cairo and Mumbai and nearly zero in Buenos Aires, so these cities cannot support locker-based analysis from OSM.
- Depot scores use fixed weights (1, 0.5, 0.25). They are a heuristic for ranking zones, not an estimate of demand.

Counts in the extract (all points inside the extract bbox, from `meta.json` `poi_counts`). Build time is the POI step only, on this machine:

| City | POIs | shop | market | depot | post_office | locker | wholesale | Zones | Zones with depot | Build (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| New Delhi | 9,467 | 8,980 | 144 | 157 | 113 | 3 | 70 | 120 | 36 | 8.5 |
| Cairo | 2,512 | 2,429 | 28 | 10 | 37 | 0 | 8 | 42 | 5 | 6.6 |
| Moscow | 57,780 | 55,012 | 147 | 1,030 | 1,042 | 513 | 36 | 160 | 124 | 14.5 |
| Buenos Aires | 43,073 | 41,736 | 68 | 336 | 178 | 1 | 754 | 208 | 79 | 8.2 |
| New York | 34,657 | 32,955 | 100 | 817 | 521 | 37 | 227 | 234 | 109 | 38.4 |
| Mumbai | 4,729 | 4,146 | 96 | 379 | 82 | 0 | 26 | 143 | 46 | 6.1 |
| Total | 152,218 | 145,258 | 583 | 2,729 | 1,973 | 554 | 1,121 | 907 | 399 | 82.3 |

Zones with depot means zones with `n_depot` > 0. The zone-level columns count only points inside zones, so they differ slightly from these extract totals. The OSM replication timestamp is 2026-10-16T23:00:00Z for all six extracts.

## Rebuilding

```
python experiments/build_cities.py            # all six cities, or name cities
python experiments/build_pois.py              # adds pois.csv, zone POI columns, meta poi_counts
python experiments/plot_cities.py             # writes figures/*.png
python experiments/plot_pois.py               # writes figures/<city>_pois.png, pois_overview.png, poi_counts.png
python -m pytest -q                           # unit tests on synthetic data
```

## Attribution

- Road data: (c) OpenStreetMap contributors, licensed under the Open Database License (ODbL) 1.0, https://www.openstreetmap.org/copyright
- Population data: GHSL GHS-POP R2023A, Pesaresi, M. et al., European Commission, Joint Research Centre (JRC), https://ghsl.jrc.ec.europa.eu
