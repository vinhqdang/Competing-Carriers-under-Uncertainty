# Data

## Raw inputs (`data/raw/`, not modified by the pipeline)

- `<City>.osm.pbf`: OpenStreetMap extracts for NewDelhi, Cairo, Moscow, BuenosAires, NewYork, from BBBike (https://download.BBBike.org), replication timestamp 2026-10-16T23:00:00Z.
- `ghs/GHS_POP_E2025_GLOBE_R2023A_4326_30ss_V1_0.tif`: GHSL GHS-POP R2023A, epoch 2025, EPSG:4326, 30 arc-second cells (about 0.00833 deg), people per cell.

## Processed outputs (`data/processed/<city>/`)

- `zones.csv`: one row per populated zone (population >= 1). `lon`, `lat` are the population-weighted centroid (deg). `pop` is people. `area_km2` is the spherical area of the block. `road_km_all` covers all drivable highway classes, `road_km_major` covers motorway, trunk, primary, secondary, tertiary and their `_link` variants (km). `lane_km_major` is the major road length times lanes (km). `node` is the index of the nearest node of `major_graph.npz`.
- `zone_bounds.npy`: (Z, 4) west, south, east, north of each zone block (deg).
- `major_graph.npz`: undirected major-road graph, largest connected component. Arrays: `node_id` (OSM id), `lon`, `lat`, `src`, `dst`, `length_m`, `free_speed_kmh`, `time_s`, `road_class_code` (0-4 major classes, 5-9 the same classes as links), `segments` (E, 2, 2) for plotting.
- `travel_time_matrix.npy`: (Z, Z) float32 free-flow travel time in seconds between zone centroids, graph shortest path plus 120 s access at each end.
- `meta.json`: bbox, block size, zone count, population totals, road totals, graph counts, source strings and build settings.

## Units and conventions

- Population: persons. Density: people per km^2. Distances: metres in the graph, km in zone tables.
- Free-flow speeds: motorway 80, trunk 60, primary 45, secondary 35, tertiary 30 km/h; link roads 0.7 times these.
- Lanes: OSM `lanes` tag when present (first integer); otherwise motorway 3, trunk 2, primary 2, secondary 1, tertiary 1; link roads 1.
- Zones are 4 x 4 raster cells (about 3.7 km) by default, aligned to the global raster grid and kept only when fully inside the extract bbox.
- Roads are assigned to zones by segment midpoint. Segments outside populated zones count only in the graph and the extract totals.

## Rebuilding

```
python experiments/build_cities.py            # all five cities, or name cities
python experiments/plot_cities.py             # writes figures/*.png
python -m pytest -q                           # unit tests on synthetic data
```

## Attribution

- Road data: (c) OpenStreetMap contributors, licensed under the Open Database License (ODbL) 1.0, https://www.openstreetmap.org/copyright
- Population data: GHSL GHS-POP R2023A, Pesaresi, M. et al., European Commission, Joint Research Centre (JRC), https://ghsl.jrc.ec.europa.eu
