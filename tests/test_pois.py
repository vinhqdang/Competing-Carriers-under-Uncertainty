"""Point-of-interest classification, per-zone counting and depot-site selection on synthetic data (no OSM files)."""
import numpy as np
import pandas as pd
import pytest

from ccu.geo import (
    POI_CATEGORIES,
    assign_points_to_zones,
    classify_poi,
    count_pois_per_zone,
    depot_score,
    haversine_m,
    select_depot_sites,
)


@pytest.mark.parametrize("tags, area, expected", [
    ({"shop": "supermarket"}, False, ("shop", "supermarket")),
    ({"shop": "vacant"}, False, None),
    ({"shop": "no"}, False, None),
    ({"shop": "wholesale"}, False, ("wholesale", "wholesale")),
    ({"shop": "trade"}, True, ("wholesale", "trade")),
    ({"amenity": "marketplace"}, True, ("market", "marketplace")),
    ({"amenity": "post_office"}, False, ("post_office", "post_office")),
    ({"amenity": "post_depot"}, True, ("depot", "post_depot")),
    ({"building": "warehouse"}, True, ("depot", "warehouse")),
    ({"industrial": "logistics"}, True, ("depot", "logistics")),
    ({"office": "courier"}, False, ("depot", "courier")),
    ({"landuse": "industrial", "name": "Bulk Cargo Park"}, True, ("depot", "landuse=industrial")),
    ({"landuse": "industrial", "name": "Steel Works"}, True, None),
    ({"landuse": "industrial", "name": "Cargo Park"}, False, None),
    ({"amenity": "parcel_locker"}, False, ("locker", "parcel_locker")),
    ({"amenity": "vending_machine", "vending": "parcel_pickup;parcel_mail_in"}, False, ("locker", "vending=parcel")),
    ({"amenity": "vending_machine", "vending": "cigarettes"}, False, None),
    ({"man_made": "goods_conveyor"}, False, None),
    ({"highway": "residential", "name": "Main Road"}, True, None),
])
def test_classify_poi_rules(tags, area, expected):
    assert classify_poi(tags, area=area) == expected


def test_classify_poi_precedence_counts_each_object_once():
    # A shop tagged as a warehouse-type depot is a depot, not a shop.
    assert classify_poi({"shop": "wholesale", "building": "warehouse"}, area=True)[0] == "depot"
    assert classify_poi({"shop": "wholesale"}, area=False)[0] == "wholesale"


def test_categories_are_the_six_named_classes():
    assert POI_CATEGORIES == ("shop", "market", "depot", "post_office", "locker", "wholesale")


def _grid_bounds():
    """Four 1 x 1 degree zones in a 2 x 2 layout, row order: SW, SE, NW, NE."""
    return np.array([
        [0.0, 0.0, 1.0, 1.0],
        [1.0, 0.0, 2.0, 1.0],
        [0.0, 1.0, 1.0, 2.0],
        [1.0, 1.0, 2.0, 2.0],
    ])


def test_points_map_to_zones_half_open_and_outside_is_minus_one():
    bounds = _grid_bounds()
    lon = np.array([0.5, 1.0, 0.5, 2.0, -0.1, 1.2])
    lat = np.array([0.5, 0.5, 1.2, 1.5, 0.5, 1.9])
    z = assign_points_to_zones(bounds, lon, lat)
    # (1.0, 0.5) lies on the shared edge: half-open intervals send it to the east zone (index 1).
    # (2.0, 1.5) is on the outer east edge, so it is outside every zone.
    np.testing.assert_array_equal(z, [0, 1, 2, -1, -1, 3])


def test_per_zone_counts_and_depot_score():
    bounds = _grid_bounds()
    lon = np.array([0.2, 0.3, 0.4, 1.5, 1.6, 0.5, 0.6, 5.0])
    lat = np.array([0.2, 0.3, 0.4, 1.5, 1.6, 1.5, 1.6, 5.0])
    cat = np.array(["shop", "depot", "wholesale", "depot", "post_office", "locker", "shop", "shop"], dtype=object)
    z = assign_points_to_zones(bounds, lon, lat)
    counts = count_pois_per_zone(z, cat, n_zones=len(bounds))

    assert list(counts.columns) == [f"n_{c}" for c in POI_CATEGORIES]
    np.testing.assert_array_equal(counts["n_shop"], [1, 0, 1, 0])
    np.testing.assert_array_equal(counts["n_depot"], [1, 0, 0, 1])
    np.testing.assert_array_equal(counts["n_wholesale"], [1, 0, 0, 0])
    np.testing.assert_array_equal(counts["n_post_office"], [0, 0, 0, 1])
    np.testing.assert_array_equal(counts["n_locker"], [0, 0, 1, 0])
    # The point at (5, 5) is outside all zones and is not counted anywhere.
    assert counts[[f"n_{c}" for c in POI_CATEGORIES]].to_numpy().sum() == 7

    np.testing.assert_allclose(depot_score(counts), [1.0 + 0.5, 0.0, 0.0, 1.0 + 0.25])


def test_count_pois_per_zone_empty_input():
    counts = count_pois_per_zone(np.zeros(0, dtype=np.int64), np.zeros(0, dtype=object), n_zones=3)
    assert counts.shape == (3, len(POI_CATEGORIES))
    assert counts.to_numpy().sum() == 0


def _zone_grid(n_side=12, step_deg=0.05):
    """Square grid of zones around (77.0, 28.0) with pop weights and a depot score on a few cells."""
    ii, jj = np.meshgrid(np.arange(n_side), np.arange(n_side), indexing="ij")
    lon = 77.0 + (jj.ravel() - n_side / 2) * step_deg
    lat = 28.0 + (ii.ravel() - n_side / 2) * step_deg
    score = np.zeros(len(lon))
    for i, s in ((5, 3.0), (30, 2.0), (60, 2.0), (61, 1.5), (100, 1.0)):
        if i < len(lon):
            score[i] = s
    return pd.DataFrame({
        "zone_id": np.arange(len(lon)), "lon": lon, "lat": lat,
        "pop": np.full(len(lon), 1000.0), "depot_score": score,
    })


def _min_pairwise_km(zones, ids):
    sel = zones.set_index("zone_id").loc[ids]
    lon, lat = sel["lon"].to_numpy(), sel["lat"].to_numpy()
    best = np.inf
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            best = min(best, float(haversine_m(lon[i], lat[i], lon[j], lat[j])) / 1000.0)
    return best


def test_select_depot_sites_spacing_and_score_order():
    zones = _zone_grid()
    rng = np.random.default_rng(0)
    ids = select_depot_sites(zones, n=4, rng=rng, min_sep_km=3.0)
    assert len(ids) == 4
    assert len(set(ids.tolist())) == 4
    assert _min_pairwise_km(zones, ids) >= 3.0
    # The highest scoring zone is always taken first; it is the top pick when nothing blocks it.
    assert int(ids[0]) == 5


def test_select_depot_sites_drops_lower_scores_that_are_too_close():
    zones = _zone_grid()
    # Zones 60 and 61 are adjacent (0.05 deg apart, about 5.5 km); with 6 km spacing only one can be chosen.
    ids = select_depot_sites(zones, n=3, rng=np.random.default_rng(1), min_sep_km=6.0)
    assert not ({60, 61} <= set(ids.tolist()))
    assert _min_pairwise_km(zones, ids) >= 6.0


def test_select_depot_sites_falls_back_to_zero_score_zones_by_ring_distance():
    zones = _zone_grid()
    # Only five zones score; asking for 12 must fill the rest with zero-score zones near the ring.
    ids = select_depot_sites(zones, n=12, rng=np.random.default_rng(2), min_sep_km=2.0)
    assert len(ids) == 12
    assert _min_pairwise_km(zones, ids) >= 2.0
    scored = set(np.flatnonzero(zones["depot_score"].to_numpy() > 0).tolist())
    assert scored & set(ids.tolist())


def test_select_depot_sites_returns_fewer_when_spacing_cannot_be_met():
    zones = _zone_grid(n_side=4, step_deg=0.05)
    ids = select_depot_sites(zones, n=10, rng=np.random.default_rng(3), min_sep_km=100.0)
    assert 1 <= len(ids) < 10
    if len(ids) > 1:
        assert _min_pairwise_km(zones, ids) >= 100.0


def test_select_depot_sites_zero_request_and_empty_zones():
    zones = _zone_grid()
    assert len(select_depot_sites(zones, n=0, rng=np.random.default_rng(4), min_sep_km=1.0)) == 0
    assert len(select_depot_sites(zones.iloc[0:0], n=3, rng=np.random.default_rng(4), min_sep_km=1.0)) == 0
