"""Zone aggregation and geodesy checks on a synthetic raster and fake road segments (no OSM files)."""
import math

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from ccu.geo import (
    aggregate_population,
    band_area_km2,
    haversine_m,
    nearest_graph_nodes,
    read_population,
    snap_window,
    zone_index_of_points,
    zone_road_sums,
)

RES = 0.01
X0, Y0 = 10.0, 50.0


@pytest.fixture
def synthetic_tif(tmp_path):
    rng = np.random.default_rng(0)
    rows, cols = 8, 12
    data = rng.integers(1, 50, size=(rows, cols)).astype(np.float64)
    data[0, 0] = -9999.0   # nodata-like negative value must count as zero
    data[5, 7] = 0.0
    path = tmp_path / "synthetic_pop.tif"
    with rasterio.open(
        path, "w", driver="GTiff", height=rows, width=cols, count=1, dtype="float64",
        crs="EPSG:4326", transform=from_origin(X0, Y0, RES, RES),
    ) as dst:
        dst.write(data, 1)
    return path, data


def test_haversine_one_degree_on_equator_and_quarter_meridian():
    R = 6371008.8
    assert haversine_m(0.0, 0.0, 1.0, 0.0) == pytest.approx(math.radians(1.0) * R, abs=1.0)
    assert haversine_m(0.0, 0.0, 0.0, 90.0) == pytest.approx(math.pi / 2 * R, abs=1.0)
    # vectorised call returns an array of the same length
    out = haversine_m(np.zeros(3), np.zeros(3), np.array([1.0, 0.0, 2.0]), np.zeros(3))
    assert out.shape == (3,) and out[1] == pytest.approx(0.0, abs=1e-9)


def test_snap_window_keeps_whole_blocks_only():
    r0, c0, nr, nc = snap_window(row_off=1.2, col_off=2.9, height=9.5, width=10.1, block=4, shape=(100, 100))
    assert (r0, c0) == (4, 4)
    assert nr % 4 == 0 and nc % 4 == 0 and nr > 0 and nc > 0
    assert r0 + nr <= 1.2 + 9.5 and c0 + nc <= 2.9 + 10.1


def test_zone_aggregation_sums_to_raster_total(synthetic_tif):
    path, data = synthetic_tif
    bbox = (X0, Y0 - 8 * RES, X0 + 12 * RES, Y0)   # the whole raster
    win = read_population(path, bbox, block=4)
    zg = aggregate_population(win)

    clipped = np.where(data > 0, data, 0.0)
    assert zg.pop_window_total == pytest.approx(clipped.sum())
    assert zg.table["pop"].sum() == pytest.approx(clipped.sum())
    assert zg.n_zones == 6                                   # 2 block rows x 3 block columns
    # zone populations are the block sums of the clipped raster
    expected0 = clipped[0:4, 0:4].sum()
    assert zg.table.loc[0, "pop"] == pytest.approx(expected0)
    # zone areas: 4x4 cells of 0.01 deg at the equator, about 1.11 km per 0.01 deg
    area = band_area_km2(Y0 - 4 * RES, Y0, 4 * RES)
    assert zg.table["area_km2"].iloc[0] == pytest.approx(area, rel=0.02)
    # centroids are population weighted and lie inside their block
    lon0, lat0 = zg.table.loc[0, "lon"], zg.table.loc[0, "lat"]
    assert X0 < lon0 < X0 + 4 * RES and Y0 - 4 * RES < lat0 < Y0


def test_points_map_to_zones_and_outside_points_map_to_minus_one(synthetic_tif):
    path, _ = synthetic_tif
    win = read_population(path, (X0, Y0 - 8 * RES, X0 + 12 * RES, Y0), block=4)
    zg = aggregate_population(win)
    lon = np.array([X0 + 0.005, X0 + 0.045, X0 + 0.005, X0 + 5.0])
    lat = np.array([Y0 - 0.005, Y0 - 0.005, Y0 - 0.045, Y0 - 0.005])
    z = zone_index_of_points(zg, lon, lat)
    assert z[0] == 0          # top-left block
    assert z[1] == 1          # next block to the east
    assert z[2] == 3          # second block row, first column
    assert z[3] == -1         # outside the raster window


def test_fake_segments_road_sums_and_lane_km(synthetic_tif):
    path, _ = synthetic_tif
    win = read_population(path, (X0, Y0 - 8 * RES, X0 + 12 * RES, Y0), block=4)
    zg = aggregate_population(win)
    # three fake segments: two major (lanes 2 and default-like 3) in zone 0, one minor in zone 1
    mid_lon = np.array([X0 + 0.01, X0 + 0.02, X0 + 0.05, X0 + 9.0])
    mid_lat = np.array([Y0 - 0.01, Y0 - 0.02, Y0 - 0.01, Y0 - 0.01])
    length_m = np.array([1000.0, 500.0, 2000.0, 700.0])
    is_major = np.array([True, True, False, True])
    lanes = np.array([2, 3, 1, 1])
    zi = zone_index_of_points(zg, mid_lon, mid_lat)
    road_all, road_major, lane_major = zone_road_sums(zi, length_m, is_major, lanes, zg.n_zones)
    assert road_all[0] == pytest.approx(1.5)                 # 1000 m + 500 m
    assert road_all[1] == pytest.approx(2.0)                 # minor segment only
    assert road_major[0] == pytest.approx(1.5)
    assert road_major[1] == pytest.approx(0.0)
    assert lane_major[0] == pytest.approx(1.0 * 2 + 0.5 * 3)  # km times lanes
    # the segment outside the zones contributes to no zone
    assert road_all.sum() == pytest.approx(3.5)


def test_nearest_graph_node_on_sphere():
    glon = np.array([10.0, 10.1, 11.0])
    glat = np.array([50.0, 50.0, 50.0])
    idx = nearest_graph_nodes(glon, glat, np.array([10.09]), np.array([50.001]))
    assert idx[0] == 1
