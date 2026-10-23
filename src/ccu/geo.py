"""Real-map data pipeline: population zones, major road graph and free-flow travel times.

Inputs are local files only: a BBBike OpenStreetMap extract (.osm.pbf) and the GHSL
GHS-POP R2023A raster (epoch 2025, EPSG:4326, 30 arc-second cells). Nothing is downloaded.

Zones are blocks of ``block x block`` raster cells, aligned to the global raster grid and
kept only when they lie fully inside the city extract and hold at least one person.
"""
from __future__ import annotations

import json
import logging
import math
import re
import time
from array import array
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import osmium
import pandas as pd
import rasterio
from rasterio.windows import Window, from_bounds
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

log = logging.getLogger("ccu.geo")

EARTH_R_KM = 6371.0088
ACCESS_S = 120.0
MAX_ZONES = 2500
DEFAULT_BLOCK = 4
MIN_ZONE_POP = 1.0
LINK_SPEED_FACTOR = 0.7
LANE_DEFAULT_LINK = 1

# Drivable highway classes (base names). Link variants are handled via the *_link suffix.
ROAD_CLASSES = (
    "motorway", "trunk", "primary", "secondary", "tertiary",
    "unclassified", "residential", "living_street", "service",
)
N_MAJOR = 5
MAJOR_CLASSES = ROAD_CLASSES[:N_MAJOR]
DRIVABLE = frozenset(ROAD_CLASSES)
EXCLUDED_HIGHWAY = frozenset({"footway", "path", "cycleway", "pedestrian", "steps", "track"})
EXCLUDED_SERVICE = frozenset({"parking_aisle", "driveway"})
FREE_SPEED_KMH = {"motorway": 80.0, "trunk": 60.0, "primary": 45.0, "secondary": 35.0, "tertiary": 30.0}
LANE_DEFAULTS = {"motorway": 3, "trunk": 2, "primary": 2, "secondary": 1, "tertiary": 1}
# Graph road class code = index in MAJOR_CLASSES, plus N_MAJOR for link roads.
GRAPH_CLASS_NAMES = tuple(MAJOR_CLASSES) + tuple(c + "_link" for c in MAJOR_CLASSES)

_LANES_RE = re.compile(r"^\s*(\d+)")


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def haversine_m(lon1, lat1, lon2, lat2):
    """Great-circle distance in metres between lon/lat points (vectorised)."""
    lon1, lat1, lon2, lat2 = (np.radians(np.asarray(v, dtype=np.float64)) for v in (lon1, lat1, lon2, lat2))
    a = np.sin((lat2 - lat1) / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2.0) ** 2
    return 2.0 * EARTH_R_KM * 1000.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def band_area_km2(lat_south, lat_north, dlon_deg):
    """Area of a lon/lat rectangle on the sphere, in km^2 (exact spherical formula)."""
    return (EARTH_R_KM ** 2) * np.radians(dlon_deg) * (
        np.sin(np.radians(lat_north)) - np.sin(np.radians(lat_south))
    )


def _unit_xyz(lon, lat):
    lo, la = np.radians(np.asarray(lon, dtype=np.float64)), np.radians(np.asarray(lat, dtype=np.float64))
    return np.column_stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])


# ---------------------------------------------------------------------------
# OSM extract header
# ---------------------------------------------------------------------------

def pbf_header(path) -> tuple[tuple[float, float, float, float], str | None]:
    """Return ((west, south, east, north), replication timestamp) from the PBF header."""
    header = osmium.io.Reader(str(path)).header()
    box = header.box()
    bbox = (box.bottom_left.lon, box.bottom_left.lat, box.top_right.lon, box.top_right.lat)
    return tuple(float(v) for v in bbox), header.get("osmosis_replication_timestamp")


# ---------------------------------------------------------------------------
# Population raster
# ---------------------------------------------------------------------------

def snap_window(row_off, col_off, height, width, block, shape):
    """Snap a float raster window inward to whole blocks aligned on the global grid.

    Returns integer (row0, col0, nrows, ncols) with row0/col0 multiples of ``block`` and
    nrows/ncols multiples of ``block``, so every cell in the window belongs to a full block.
    """
    eps = 1e-6
    r_start = max(0, math.ceil(row_off / block - eps) * block)
    c_start = max(0, math.ceil(col_off / block - eps) * block)
    r_stop = min(shape[0], math.floor((row_off + height) / block + eps) * block)
    c_stop = min(shape[1], math.floor((col_off + width) / block + eps) * block)
    nrows = ((r_stop - r_start) // block) * block
    ncols = ((c_stop - c_start) // block) * block
    if nrows <= 0 or ncols <= 0:
        raise ValueError("bounding box holds no whole block of the population raster")
    return r_start, c_start, nrows, ncols


@dataclass
class PopWindow:
    pop: np.ndarray          # (nrows, ncols) float64 persons per cell, >= 0
    row0: int                # global raster row of the first cell
    col0: int                # global raster column of the first cell
    gt: tuple                # (x0, dx, y0, dy) of the global raster grid
    block: int


def read_population(tif_path, bbox, block) -> PopWindow:
    """Read only the raster window covering ``bbox``, snapped to whole blocks."""
    with rasterio.open(tif_path) as src:
        tr = src.transform
        west, south, east, north = bbox
        fw = from_bounds(west, south, east, north, transform=tr)
        r0, c0, nr, nc = snap_window(fw.row_off, fw.col_off, fw.height, fw.width, block, (src.height, src.width))
        arr = src.read(1, window=Window(c0, r0, nc, nr)).astype(np.float64)
        nodata = src.nodata
        gt = (tr.c, tr.a, tr.f, tr.e)
    if nodata is not None:
        arr = np.where(arr == nodata, 0.0, arr)
    arr = np.where(np.isfinite(arr) & (arr > 0.0), arr, 0.0)
    return PopWindow(pop=arr, row0=r0, col0=c0, gt=gt, block=block)


@dataclass
class ZoneGrid:
    table: pd.DataFrame      # one row per zone: zone_id, lon, lat, pop, area_km2
    bounds: np.ndarray       # (Z, 4) west, south, east, north of each zone
    zone_grid: np.ndarray    # (blocks_rows, blocks_cols) zone index or -1
    row0: int
    col0: int
    gt: tuple
    block: int
    pop_window_total: float

    @property
    def n_zones(self) -> int:
        return len(self.table)


def aggregate_population(win: PopWindow, min_pop: float = MIN_ZONE_POP) -> ZoneGrid:
    """Aggregate a whole-block population window into zones of block x block cells."""
    pop, b = win.pop, win.block
    nr, nc = pop.shape
    if nr % b or nc % b:
        raise ValueError("population window must hold whole blocks")
    nbr, nbc = nr // b, nc // b
    x0, dx, y0, dy = win.gt

    lon_c = x0 + (win.col0 + np.arange(nc) + 0.5) * dx
    lat_c = y0 + (win.row0 + np.arange(nr) + 0.5) * dy
    lon_w = np.broadcast_to(lon_c[None, :], pop.shape)
    lat_w = np.broadcast_to(lat_c[:, None], pop.shape)

    def block_sum(a):
        return a.reshape(nbr, b, nbc, b).sum(axis=(1, 3))

    zpop = block_sum(pop)
    zx = block_sum(pop * lon_w)
    zy = block_sum(pop * lat_w)

    keep = zpop >= min_pop
    ii, jj = np.nonzero(keep)
    zone_grid = np.full((nbr, nbc), -1, dtype=np.int64)
    zone_grid[ii, jj] = np.arange(len(ii))

    # Block corner coordinates (lat decreases with row, lon increases with column).
    lat_n = y0 + (win.row0 + ii * b) * dy
    lat_s = y0 + (win.row0 + (ii + 1) * b) * dy
    lon_w_edge = x0 + (win.col0 + jj * b) * dx
    lon_e_edge = x0 + (win.col0 + (jj + 1) * b) * dx
    lat_lo, lat_hi = np.minimum(lat_n, lat_s), np.maximum(lat_n, lat_s)
    area = band_area_km2(lat_lo, lat_hi, b * abs(dx))

    table = pd.DataFrame({
        "zone_id": np.arange(len(ii), dtype=np.int64),
        "lon": zx[ii, jj] / zpop[ii, jj],
        "lat": zy[ii, jj] / zpop[ii, jj],
        "pop": zpop[ii, jj],
        "area_km2": area,
    })
    bounds = np.column_stack([
        np.minimum(lon_w_edge, lon_e_edge), lat_lo, np.maximum(lon_w_edge, lon_e_edge), lat_hi,
    ])
    return ZoneGrid(
        table=table, bounds=bounds, zone_grid=zone_grid, row0=win.row0, col0=win.col0,
        gt=win.gt, block=b, pop_window_total=float(pop.sum()),
    )


def zone_index_of_points(zg: ZoneGrid, lon, lat) -> np.ndarray:
    """Zone index of each lon/lat point, or -1 when it falls outside the zones."""
    lon = np.asarray(lon, dtype=np.float64)
    lat = np.asarray(lat, dtype=np.float64)
    x0, dx, y0, dy = zg.gt
    col = np.floor((lon - x0) / dx).astype(np.int64) - zg.col0
    row = np.floor((lat - y0) / dy).astype(np.int64) - zg.row0
    nbr, nbc = zg.zone_grid.shape
    b = zg.block
    inside = (row >= 0) & (col >= 0) & (row < nbr * b) & (col < nbc * b)
    out = np.full(lon.shape, -1, dtype=np.int64)
    out[inside] = zg.zone_grid[row[inside] // b, col[inside] // b]
    return out


def zone_road_sums(zone_idx, length_m, is_major, lanes, n_zones):
    """Per-zone road sums from segments already assigned to zones (-1 = outside)."""
    ok = zone_idx >= 0
    z = zone_idx[ok]
    km = np.asarray(length_m, dtype=np.float64)[ok] / 1000.0
    major = np.asarray(is_major, dtype=bool)[ok]
    lane = np.asarray(lanes, dtype=np.float64)[ok]
    road_all = np.bincount(z, weights=km, minlength=n_zones)
    road_major = np.bincount(z[major], weights=km[major], minlength=n_zones)
    lane_major = np.bincount(z[major], weights=(km * lane)[major], minlength=n_zones)
    return road_all, road_major, lane_major


def nearest_graph_nodes(graph_lon, graph_lat, lon, lat) -> np.ndarray:
    """Index of the nearest graph node for each point (chord distance on the unit sphere)."""
    tree = cKDTree(_unit_xyz(graph_lon, graph_lat))
    _, idx = tree.query(_unit_xyz(lon, lat))
    return idx.astype(np.int64)


# ---------------------------------------------------------------------------
# OSM road scan
# ---------------------------------------------------------------------------

def _parse_lanes(value):
    if not value:
        return None
    m = _LANES_RE.match(value)
    if not m:
        return None
    n = int(m.group(1))
    return n if 1 <= n <= 16 else None


class _RoadCollector(osmium.SimpleHandler):
    """Collects node coordinates of drivable ways into flat arrays (no per-segment objects)."""

    def __init__(self):
        super().__init__()
        self.node_id = array("q")
        self.node_lon = array("d")
        self.node_lat = array("d")
        self.way_count = array("q")
        self.way_cls = array("b")
        self.way_link = array("b")
        self.way_lanes = array("h")
        self.ways_access_no = 0
        self.ways_excluded_service = 0
        self.ways_missing_locations = 0

    def way(self, w):
        tags = w.tags
        hw = tags.get("highway")
        if hw is None or hw in EXCLUDED_HIGHWAY:
            return
        link = hw.endswith("_link")
        base = hw[:-5] if link else hw
        if base not in DRIVABLE:
            return
        if tags.get("access") == "no":
            self.ways_access_no += 1
            return
        if base == "service" and tags.get("service") in EXCLUDED_SERVICE:
            self.ways_excluded_service += 1
            return
        nodes = w.nodes
        if len(nodes) < 2:
            return
        ids, lons, lats = [], [], []
        try:
            for n in nodes:
                ids.append(n.ref)
                lons.append(n.lon)
                lats.append(n.lat)
        except osmium.InvalidLocationError:
            self.ways_missing_locations += 1
            return
        lanes = _parse_lanes(tags.get("lanes"))
        if lanes is None:
            lanes = LANE_DEFAULT_LINK if link else LANE_DEFAULTS.get(base, 1)
        self.node_id.extend(ids)
        self.node_lon.extend(lons)
        self.node_lat.extend(lats)
        self.way_count.append(len(ids))
        self.way_cls.append(ROAD_CLASSES.index(base))
        self.way_link.append(1 if link else 0)
        self.way_lanes.append(lanes)


def _frombuf(a, dtype):
    return np.frombuffer(a, dtype=dtype) if len(a) else np.zeros(0, dtype=dtype)


@dataclass
class RoadScan:
    """Segments (consecutive node pairs) of all drivable ways in an extract."""
    seg_a: np.ndarray        # OSM node id at segment start (int64)
    seg_b: np.ndarray        # OSM node id at segment end (int64)
    seg_lon0: np.ndarray
    seg_lat0: np.ndarray
    seg_lon1: np.ndarray
    seg_lat1: np.ndarray
    seg_len_m: np.ndarray
    seg_mid_lon: np.ndarray
    seg_mid_lat: np.ndarray
    seg_cls: np.ndarray      # index into ROAD_CLASSES (int8)
    seg_link: np.ndarray     # 0/1 (int8)
    seg_lanes: np.ndarray    # lanes of the parent way (int16)
    stats: dict


def scan_roads(pbf_path) -> RoadScan:
    """One pass over the PBF with locations, then vectorised segment construction."""
    h = _RoadCollector()
    h.apply_file(str(pbf_path), locations=True)

    node_id = _frombuf(h.node_id, np.int64)
    node_lon = _frombuf(h.node_lon, np.float64)
    node_lat = _frombuf(h.node_lat, np.float64)
    counts = _frombuf(h.way_count, np.int64)
    way_cls = _frombuf(h.way_cls, np.int8)
    way_link = _frombuf(h.way_link, np.int8)
    way_lanes = _frombuf(h.way_lanes, np.int16)

    n = len(node_id)
    stats = {
        "ways_drivable_kept": int(len(counts)),
        "ways_skipped_access_no": h.ways_access_no,
        "ways_skipped_parking_driveway": h.ways_excluded_service,
        "ways_skipped_missing_locations": h.ways_missing_locations,
    }
    if n < 2:
        empty_i = np.zeros(0, dtype=np.int64)
        empty_f = np.zeros(0, dtype=np.float64)
        return RoadScan(empty_i, empty_i, empty_f, empty_f, empty_f, empty_f, empty_f, empty_f, empty_f,
                        np.zeros(0, np.int8), np.zeros(0, np.int8), np.zeros(0, np.int16), stats)

    # Segment k joins node k and node k+1 when both belong to the same way.
    is_last = np.zeros(n, dtype=bool)
    is_last[np.cumsum(counts) - 1] = True
    seg = np.flatnonzero(~is_last[:-1])
    way_of_node = np.repeat(np.arange(len(counts)), counts)
    sw = way_of_node[seg]

    lon0, lat0 = node_lon[seg], node_lat[seg]
    lon1, lat1 = node_lon[seg + 1], node_lat[seg + 1]
    length = haversine_m(lon0, lat0, lon1, lat1)
    stats["road_km_all_extract"] = float(length.sum() / 1000.0)

    return RoadScan(
        seg_a=node_id[seg], seg_b=node_id[seg + 1],
        seg_lon0=lon0, seg_lat0=lat0, seg_lon1=lon1, seg_lat1=lat1,
        seg_len_m=length, seg_mid_lon=(lon0 + lon1) / 2.0, seg_mid_lat=(lat0 + lat1) / 2.0,
        seg_cls=way_cls[sw], seg_link=way_link[sw], seg_lanes=way_lanes[sw].astype(np.int16),
        stats=stats,
    )


# ---------------------------------------------------------------------------
# Major road graph
# ---------------------------------------------------------------------------

@dataclass
class MajorGraph:
    node_id: np.ndarray      # OSM node ids (int64)
    lon: np.ndarray
    lat: np.ndarray
    src: np.ndarray          # int32 node indices
    dst: np.ndarray
    length_m: np.ndarray     # float32
    free_speed_kmh: np.ndarray
    time_s: np.ndarray
    road_class_code: np.ndarray  # uint8, index into GRAPH_CLASS_NAMES
    stats: dict

    @property
    def n_nodes(self) -> int:
        return len(self.lon)

    @property
    def n_edges(self) -> int:
        return len(self.src)

    def segments(self) -> np.ndarray:
        """(E, 2, 2) float32 array of [[lon0, lat0], [lon1, lat1]] per edge."""
        out = np.empty((self.n_edges, 2, 2), dtype=np.float32)
        out[:, 0, 0] = self.lon[self.src]
        out[:, 0, 1] = self.lat[self.src]
        out[:, 1, 0] = self.lon[self.dst]
        out[:, 1, 1] = self.lat[self.dst]
        return out


def build_major_graph(scan: RoadScan) -> MajorGraph:
    """Undirected graph of major classes (and links), merged at OSM node ids, largest component."""
    stats = dict(scan.stats)
    m = scan.seg_cls < N_MAJOR
    a, b = scan.seg_a[m], scan.seg_b[m]
    keep = a != b
    a, b = a[keep], b[keep]
    cls = scan.seg_cls[m][keep].astype(np.int64)
    link = scan.seg_link[m][keep].astype(np.int64)
    length = scan.seg_len_m[m][keep]

    speed_by_cls = np.array([FREE_SPEED_KMH[c] for c in MAJOR_CLASSES])
    speed = speed_by_cls[cls] * np.where(link == 1, LINK_SPEED_FACTOR, 1.0)
    time_s = length / (speed / 3.6)
    code = (cls + N_MAJOR * link).astype(np.uint8)

    # Node table from the kept segment endpoints.
    ids_all = np.concatenate([a, b])
    uniq, first = np.unique(ids_all, return_index=True)
    lon_all = np.concatenate([scan.seg_lon0[m][keep], scan.seg_lon1[m][keep]])
    lat_all = np.concatenate([scan.seg_lat0[m][keep], scan.seg_lat1[m][keep]])
    node_lon = lon_all[first]
    node_lat = lat_all[first]

    # Undirected edges: one per node pair, fastest parallel record kept.
    lo = np.minimum(a, b)
    hi = np.maximum(a, b)
    order = np.lexsort((time_s, hi, lo))
    lo, hi = lo[order], hi[order]
    length, speed, time_s, code = length[order], speed[order], time_s[order], code[order]
    first_pair = np.ones(len(lo), dtype=bool)
    first_pair[1:] = (lo[1:] != lo[:-1]) | (hi[1:] != hi[:-1])
    lo, hi = lo[first_pair], hi[first_pair]
    length, speed, time_s, code = length[first_pair], speed[first_pair], time_s[first_pair], code[first_pair]
    stats["graph_parallel_edges_merged"] = int(first_pair.size - first_pair.sum())

    src = np.searchsorted(uniq, lo).astype(np.int64)
    dst = np.searchsorted(uniq, hi).astype(np.int64)
    n = len(uniq)
    stats["graph_nodes_before_lcc"] = int(n)
    stats["graph_edges_before_lcc"] = int(len(src))

    adj = coo_matrix((np.ones(len(src), dtype=np.int8), (src, dst)), shape=(n, n))
    n_comp, labels = connected_components(adj, directed=False)
    stats["graph_components_before_lcc"] = int(n_comp)
    big = np.bincount(labels).argmax()
    keep_node = labels == big
    remap = np.full(n, -1, dtype=np.int64)
    remap[keep_node] = np.arange(int(keep_node.sum()))
    keep_edge = keep_node[src]
    src, dst = remap[src[keep_edge]], remap[dst[keep_edge]]
    stats["graph_nodes_dropped_non_lcc"] = int(n - keep_node.sum())

    graph = MajorGraph(
        node_id=uniq[keep_node],
        lon=node_lon[keep_node],
        lat=node_lat[keep_node],
        src=src.astype(np.int32),
        dst=dst.astype(np.int32),
        length_m=length[keep_edge].astype(np.float32),
        free_speed_kmh=speed[keep_edge].astype(np.float32),
        time_s=time_s[keep_edge].astype(np.float32),
        road_class_code=code[keep_edge],
        stats=stats,
    )
    stats["graph_nodes"] = graph.n_nodes
    stats["graph_edges"] = graph.n_edges
    stats["road_km_major_graph"] = float(graph.length_m.astype(np.float64).sum() / 1000.0)
    return graph


# ---------------------------------------------------------------------------
# Travel-time matrix
# ---------------------------------------------------------------------------

def travel_time_matrix(graph: MajorGraph, zone_nodes, access_s: float = ACCESS_S, chunk: int = 64):
    """Zone-to-zone free-flow time in seconds (float32): graph shortest path + access per end."""
    zone_nodes = np.asarray(zone_nodes, dtype=np.int64)
    n = graph.n_nodes
    t = graph.time_s.astype(np.float64)
    rows = np.concatenate([graph.src, graph.dst]).astype(np.int64)
    cols = np.concatenate([graph.dst, graph.src]).astype(np.int64)
    G = csr_matrix((np.concatenate([t, t]), (rows, cols)), shape=(n, n))

    uniq, inv = np.unique(zone_nodes, return_inverse=True)
    M = np.empty((len(uniq), len(zone_nodes)), dtype=np.float32)
    for s in range(0, len(uniq), chunk):
        idx = uniq[s:s + chunk]
        d = dijkstra(G, directed=True, indices=idx)
        M[s:s + len(idx)] = d[:, zone_nodes]
    T = M[inv] + np.float32(2.0 * access_s)
    n_unreach = int(np.isinf(T).sum())
    if n_unreach:
        log.warning("%d zone pairs unreachable in the major graph", n_unreach)
    return T.astype(np.float32), n_unreach


# ---------------------------------------------------------------------------
# City pipeline
# ---------------------------------------------------------------------------

POP_SOURCE = ("GHSL GHS-POP R2023A, epoch 2025, 30 arc-second global grid (EPSG:4326), "
              "Pesaresi M. et al., European Commission Joint Research Centre; "
              "file GHS_POP_E2025_GLOBE_R2023A_4326_30ss_V1_0.tif")
OSM_SOURCE = "OpenStreetMap extract from BBBike (https://download.BBBike.org), OpenStreetMap contributors, ODbL 1.0"


def build_city(city, *, pbf_path, tif_path, out_dir, continent, block_cells=DEFAULT_BLOCK,
               max_zones=MAX_ZONES, access_s=ACCESS_S, display_name=None):
    """Build zones, graph, travel-time matrix and meta for one city. Returns the meta dict."""
    t0 = time.perf_counter()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    bbox, osm_stamp = pbf_header(pbf_path)
    log.info("%s: bbox %s", city, bbox)

    scan = scan_roads(pbf_path)
    graph = build_major_graph(scan)
    log.info("%s: graph %d nodes, %d edges", city, graph.n_nodes, graph.n_edges)

    block = block_cells
    while True:
        win = read_population(tif_path, bbox, block)
        zg = aggregate_population(win)
        if zg.n_zones <= max_zones:
            break
        block += 1
        log.info("%s: %d zones at block %d exceeds %d, retrying with block %d",
                 city, zg.n_zones, block - 1, max_zones, block)
    if zg.n_zones == 0:
        raise ValueError(f"{city}: no populated zones")
    if block != block_cells:
        log.info("%s: block size increased from %d to %d cells", city, block_cells, block)

    zone_idx = zone_index_of_points(zg, scan.seg_mid_lon, scan.seg_mid_lat)
    road_all, road_major, lane_major = zone_road_sums(
        zone_idx, scan.seg_len_m, scan.seg_cls < N_MAJOR, scan.seg_lanes, zg.n_zones)
    seg_outside = int((zone_idx < 0).sum())

    table = zg.table.copy()
    table["node"] = nearest_graph_nodes(graph.lon, graph.lat, table["lon"].to_numpy(), table["lat"].to_numpy())
    table["road_km_all"] = road_all
    table["road_km_major"] = road_major
    table["lane_km_major"] = lane_major
    table = table[["zone_id", "lon", "lat", "pop", "area_km2", "road_km_all", "road_km_major",
                   "lane_km_major", "node"]]

    travel, n_unreach = travel_time_matrix(graph, table["node"].to_numpy(), access_s=access_s)

    table = table.round({"lon": 6, "lat": 6, "pop": 3, "area_km2": 4,
                         "road_km_all": 4, "road_km_major": 4, "lane_km_major": 4})
    table.to_csv(out_dir / "zones.csv", index=False)
    np.save(out_dir / "zone_bounds.npy", zg.bounds.astype(np.float64))
    np.save(out_dir / "travel_time_matrix.npy", travel)
    np.savez_compressed(
        out_dir / "major_graph.npz",
        node_id=graph.node_id, lon=graph.lon, lat=graph.lat,
        src=graph.src, dst=graph.dst, length_m=graph.length_m,
        free_speed_kmh=graph.free_speed_kmh, time_s=graph.time_s,
        road_class_code=graph.road_class_code, segments=graph.segments(),
    )

    pop_zones = float(zg.table["pop"].sum())
    meta = {
        "city": city,
        "display_name": display_name or city,
        "continent": continent,
        "bbox": {"west": bbox[0], "south": bbox[1], "east": bbox[2], "north": bbox[3]},
        "block_cells": block,
        "block_deg": block * abs(zg.gt[1]),
        "block_km_approx": block * abs(zg.gt[1]) * 111.32,
        "zone_count": zg.n_zones,
        "population_extract_total": zg.pop_window_total,
        "population_zones_total": pop_zones,
        "population_dropped_zones_total": zg.pop_window_total - pop_zones,
        "population_epoch": 2025,
        "population_source": POP_SOURCE,
        "osm_source": OSM_SOURCE,
        "osm_replication_timestamp": osm_stamp,
        "build_date": time.strftime("%Y-%m-%d"),
        "road_km_all_zones": float(road_all.sum()),
        "road_km_major_zones": float(road_major.sum()),
        "lane_km_major_zones": float(lane_major.sum()),
        "road_km_all_extract": scan.stats.get("road_km_all_extract"),
        "road_km_major_graph": graph.stats["road_km_major_graph"],
        "segments_outside_zones": seg_outside,
        "graph_nodes": graph.n_nodes,
        "graph_edges": graph.n_edges,
        "graph_stats": {k: v for k, v in graph.stats.items() if k not in ("road_km_major_graph",)},
        "scan_stats": {k: v for k, v in scan.stats.items() if k != "road_km_all_extract"},
        "travel_access_s": access_s,
        "travel_unreachable_pairs": n_unreach,
        "travel_time_max_s": float(np.max(travel)) if travel.size else 0.0,
        "free_speed_kmh": FREE_SPEED_KMH,
        "link_speed_factor": LINK_SPEED_FACTOR,
        "lane_defaults": LANE_DEFAULTS,
        "lane_default_link": LANE_DEFAULT_LINK,
        "graph_class_names": list(GRAPH_CLASS_NAMES),
        "build_seconds": round(time.perf_counter() - t0, 2),
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, default=lambda o: o.item()))
    log.info("%s: %d zones, pop %.2f M, major road %.0f km, %.1f s",
             city, zg.n_zones, zg.pop_window_total / 1e6, meta["road_km_major_zones"], meta["build_seconds"])
    return meta


# ---------------------------------------------------------------------------
# Points of interest (OpenStreetMap)
# ---------------------------------------------------------------------------

POI_CATEGORIES = ("shop", "market", "depot", "post_office", "locker", "wholesale")
POI_COLUMNS = ("lon", "lat", "osm_type", "osm_id", "name", "category", "subtype")
DEPOT_NAME_RE = re.compile(r"warehouse|logistic|depot|distribution|cargo|freight|courier|fulfil", re.IGNORECASE)
DEPOT_INDUSTRIAL = frozenset({"warehouse", "logistics", "distribution"})
DEPOT_OFFICE = frozenset({"logistics", "courier"})
PARCEL_VENDING = frozenset({"parcel_pickup", "parcel_mail_in"})
SHOP_EXCLUDED = frozenset({"vacant", "no"})
DEPOT_SCORE_WEIGHTS = {"depot": 1.0, "wholesale": 0.5, "post_office": 0.25}


def _has_parcel_vending(value) -> bool:
    return bool(value) and any(part.strip() in PARCEL_VENDING for part in value.split(";"))


def classify_poi(tags, area=False):
    """Category and subtype of an OSM object from its tags, or None when it is not a point of interest.

    ``tags`` is any mapping with ``get`` (pyosmium TagList or dict). ``area`` is True for ways.
    When several rules match, the first in this order wins: depot, locker, post_office, wholesale,
    market, shop, so each object is counted in exactly one category.
    """
    amenity = tags.get("amenity")
    building = tags.get("building")
    industrial = tags.get("industrial")
    office = tags.get("office")
    shop = tags.get("shop")

    if amenity == "post_depot":
        return "depot", amenity
    if building == "warehouse":
        return "depot", building
    if industrial in DEPOT_INDUSTRIAL:
        return "depot", industrial
    if office in DEPOT_OFFICE:
        return "depot", office
    if area and tags.get("landuse") == "industrial":
        name = tags.get("name")
        if name and DEPOT_NAME_RE.search(name):
            return "depot", "landuse=industrial"

    if amenity == "parcel_locker":
        return "locker", amenity
    if amenity == "vending_machine" and _has_parcel_vending(tags.get("vending")):
        return "locker", "vending=parcel"

    if amenity == "post_office":
        return "post_office", amenity

    if shop in ("wholesale", "trade"):
        return "wholesale", shop
    if amenity == "marketplace":
        return "market", amenity
    if shop and shop not in SHOP_EXCLUDED:
        return "shop", shop
    return None


class _PoiCollector(osmium.SimpleHandler):
    """Collects points of interest: nodes at their location, ways at the mean of their node locations."""

    def __init__(self):
        super().__init__()
        self.poi_lon = array("d")
        self.poi_lat = array("d")
        self.poi_id = array("q")
        self.poi_type = []
        self.poi_name = []
        self.poi_category = []
        self.poi_subtype = []
        self.seen = set()
        self.missing_locations = 0

    def _add(self, kind, obj_id, lon, lat, tags, hit):
        key = (kind, obj_id)
        if key in self.seen:
            return
        self.seen.add(key)
        self.poi_lon.append(lon)
        self.poi_lat.append(lat)
        self.poi_id.append(obj_id)
        self.poi_type.append(kind)
        self.poi_name.append(tags.get("name") or "")
        self.poi_category.append(hit[0])
        self.poi_subtype.append(hit[1])

    def node(self, n):
        if not n.tags:
            return
        hit = classify_poi(n.tags, area=False)
        if hit is None:
            return
        try:
            lon, lat = n.location.lon, n.location.lat
        except osmium.InvalidLocationError:
            self.missing_locations += 1
            return
        self._add("node", n.id, lon, lat, n.tags, hit)

    def way(self, w):
        if not w.tags:
            return
        hit = classify_poi(w.tags, area=True)
        if hit is None:
            return
        lons, lats = [], []
        try:
            for nd in w.nodes:
                lons.append(nd.lon)
                lats.append(nd.lat)
        except osmium.InvalidLocationError:
            self.missing_locations += 1
            return
        if not lons:
            self.missing_locations += 1
            return
        self._add("way", w.id, sum(lons) / len(lons), sum(lats) / len(lats), w.tags, hit)


def extract_pois(pbf_path):
    """One pass over the PBF; returns (DataFrame of POIs with POI_COLUMNS, stats dict)."""
    t0 = time.perf_counter()
    h = _PoiCollector()
    h.apply_file(str(pbf_path), locations=True)
    df = pd.DataFrame({
        "lon": _frombuf(h.poi_lon, np.float64),
        "lat": _frombuf(h.poi_lat, np.float64),
        "osm_type": pd.Categorical(h.poi_type, categories=["node", "way"]),
        "osm_id": _frombuf(h.poi_id, np.int64),
        "name": pd.Series(h.poi_name, dtype=object),
        "category": pd.Categorical(h.poi_category, categories=POI_CATEGORIES),
        "subtype": pd.Series(h.poi_subtype, dtype=object),
    }, columns=list(POI_COLUMNS))
    per_cat = {c: int((df["category"] == c).sum()) for c in POI_CATEGORIES}
    for c, k in per_cat.items():
        log.info("pois %s: %d", c, k)
    stats = {
        "pois_total": len(df),
        "per_category": per_cat,
        "missing_locations": h.missing_locations,
        "seconds": round(time.perf_counter() - t0, 2),
    }
    return df, stats


def assign_points_to_zones(bounds, lon, lat) -> np.ndarray:
    """Zone index of each point from (Z, 4) west, south, east, north rectangles, or -1.

    Intervals are half-open (west <= lon < east, south <= lat < north), as in zone_index_of_points.
    A point on a shared edge goes to the first zone in row order.
    """
    bounds = np.asarray(bounds, dtype=np.float64)
    lon = np.asarray(lon, dtype=np.float64)
    lat = np.asarray(lat, dtype=np.float64)
    out = np.full(lon.shape, -1, dtype=np.int64)
    for z, (w, s, e, n) in enumerate(bounds):
        hit = (out < 0) & (lon >= w) & (lon < e) & (lat >= s) & (lat < n)
        out[hit] = z
    return out


def count_pois_per_zone(zone_idx, category, n_zones) -> pd.DataFrame:
    """Per-zone POI counts, one column n_<category> per entry of POI_CATEGORIES (-1 zone ignored)."""
    zone_idx = np.asarray(zone_idx, dtype=np.int64)
    category = np.asarray(category, dtype=object)
    ok = zone_idx >= 0
    out = pd.DataFrame(index=pd.RangeIndex(n_zones))
    for c in POI_CATEGORIES:
        m = ok & (category == c)
        out[f"n_{c}"] = np.bincount(zone_idx[m], minlength=n_zones).astype(np.int64)
    return out


def depot_score(counts: pd.DataFrame) -> np.ndarray:
    """n_depot + 0.5 n_wholesale + 0.25 n_post_office per zone."""
    score = np.zeros(len(counts), dtype=np.float64)
    for c, w in DEPOT_SCORE_WEIGHTS.items():
        score += w * counts[f"n_{c}"].to_numpy(dtype=np.float64)
    return score


def select_depot_sites(zones: pd.DataFrame, n: int, rng: np.random.Generator, min_sep_km: float,
                       *, ring_pct: float = 70.0) -> np.ndarray:
    """Pick up to ``n`` zone ids for depots with high depot_score, spaced at least ``min_sep_km`` apart.

    ``zones`` needs zone_id, lon, lat, depot_score and optionally pop. Distances are measured from
    the population-weighted centroid. Zones are ordered by depot_score (descending), then by how
    close their centroid distance lies to the ring at the ``ring_pct`` percentile of that distance
    (this also orders zero-score zones when scoring zones are scarce), then by a random key from
    ``rng``. A zone is accepted when it is at least ``min_sep_km`` from every accepted zone.

    Returns an int64 array of zone ids. It is shorter than ``n`` when the extract cannot hold
    ``n`` spaced sites; a warning is logged in that case.
    """
    n = int(n)
    if n <= 0 or len(zones) == 0:
        return np.zeros(0, dtype=np.int64)
    zone_id = zones["zone_id"].to_numpy(dtype=np.int64)
    lon = zones["lon"].to_numpy(dtype=np.float64)
    lat = zones["lat"].to_numpy(dtype=np.float64)
    score = zones["depot_score"].to_numpy(dtype=np.float64)
    w = zones["pop"].to_numpy(dtype=np.float64) if "pop" in zones else np.ones(len(zones))
    if not w.sum() > 0:
        w = np.ones(len(zones))
    lon0 = float(np.sum(lon * w) / w.sum())
    lat0 = float(np.sum(lat * w) / w.sum())
    dist_km = haversine_m(lon0, lat0, lon, lat) / 1000.0
    ring = float(np.percentile(dist_km, ring_pct))
    ring_gap = np.abs(dist_km - ring)
    order = np.lexsort((rng.random(len(zones)), ring_gap, -score))

    chosen: list[int] = []
    for i in order:
        if len(chosen) >= n:
            break
        if chosen:
            sep = haversine_m(lon[i], lat[i], lon[chosen], lat[chosen]) / 1000.0
            if np.min(sep) < min_sep_km:
                continue
        chosen.append(int(i))
    if len(chosen) < n:
        log.warning("select_depot_sites: %d of %d sites at min separation %.1f km (%d zones with score > 0)",
                    len(chosen), n, min_sep_km, int(np.sum(score > 0)))
    return zone_id[np.asarray(chosen, dtype=np.int64)]


def build_city_pois(*, pbf_path, out_dir):
    """Write pois.csv, add per-zone POI counts and depot_score to zones.csv, record POI counts in meta.json.

    Existing zones.csv columns are kept as written (read as text and appended to). Re-running replaces
    the POI columns. Returns the POI part of the meta dict.
    """
    t0 = time.perf_counter()
    out_dir = Path(out_dir)
    meta = json.loads((out_dir / "meta.json").read_text())
    zones = pd.read_csv(out_dir / "zones.csv", dtype=str, keep_default_na=False)
    bounds = np.load(out_dir / "zone_bounds.npy")
    if len(bounds) != len(zones) or not np.array_equal(zones["zone_id"].astype(np.int64).to_numpy(),
                                                       np.arange(len(zones))):
        raise ValueError(f"{out_dir}: zones.csv rows do not match zone_bounds.npy")

    pois, stats = extract_pois(pbf_path)
    zone_idx = assign_points_to_zones(bounds, pois["lon"].to_numpy(), pois["lat"].to_numpy())
    counts = count_pois_per_zone(zone_idx, pois["category"].astype(object).to_numpy(), len(zones))
    counts["depot_score"] = depot_score(counts)

    pois["zone_id"] = zone_idx
    pois.to_csv(out_dir / "pois.csv", index=False, float_format="%.7f")

    new_cols = [c for c in counts.columns if c != "depot_score"] + ["depot_score"]
    base = zones.drop(columns=[c for c in new_cols if c in zones.columns])
    counts_txt = counts[new_cols].astype(str)
    base.reset_index(drop=True).join(counts_txt.reset_index(drop=True)).to_csv(
        out_dir / "zones.csv", index=False)

    in_zones = {c: int(counts[f"n_{c}"].sum()) for c in POI_CATEGORIES}
    stamp = meta.get("osm_replication_timestamp") or pbf_header(pbf_path)[1]
    poi_meta = {
        "poi_osm_replication_timestamp": stamp,
        "poi_counts": {
            "extract": stats["per_category"],
            "extract_total": stats["pois_total"],
            "in_zones": in_zones,
            "zones_with_any": int(np.sum(counts[[f"n_{c}" for c in POI_CATEGORIES]].sum(axis=1) > 0)),
            "zones_with_depot": int(np.sum(counts["n_depot"] > 0)),
            "zones_with_depot_score": int(np.sum(counts["depot_score"] > 0)),
            "missing_locations": stats["missing_locations"],
            "outside_zones": int(np.sum(zone_idx < 0)),
        },
        "poi_build_seconds": round(time.perf_counter() - t0, 2),
    }
    meta.update(poi_meta)
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, default=lambda o: o.item()))
    log.info("%s: %d POIs, %d in zones, %d zones with a depot, %.1f s",
             out_dir.name, stats["pois_total"], int(np.sum(zone_idx >= 0)),
             poi_meta["poi_counts"]["zones_with_depot"], poi_meta["poi_build_seconds"])
    return poi_meta
