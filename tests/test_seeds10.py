"""Statistics of the ten-seed summary (experiments/summarize_seeds10.py): bootstrap interval and the derived gain shares."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))

from summarize_seeds10 import boot_ci, boot_ratio_ci, derive  # noqa: E402


def test_boot_ci_brackets_mean_and_is_deterministic():
    x = np.array([1.0, 2.0, 3.0, 4.0, 10.0])
    lo, hi = boot_ci(x)
    assert lo < x.mean() < hi
    assert (lo, hi) == boot_ci(x)
    assert boot_ci([5.0, 5.0, 5.0]) == (5.0, 5.0)


def test_boot_ratio_ci():
    m, lo, hi = boot_ratio_ci([1, 2, 3, 4], [2, 4, 6, 8])
    assert abs(m - 0.5) < 1e-12 and abs(lo - 0.5) < 1e-9 and abs(hi - 0.5) < 1e-9


def test_gain_share_against_social_optimum():
    r = dict(sc0=-100.0, sc_so_e3=-200.0, sc_dip_target=-205.0, sc_dip=-205.0, w_ne_zmc=100.0, w_ne_best=100.0, w_ne_worst=100.0,
             sc_grid_best=-150.0, sc_congestion_only=-101.0, sc_delivery_only=-150.0, gain_both_pct=50.0, gain_delivery_only_pct=50.0,
             gain_congestion_only_pct=1.0, grid_calls_mean_pt=10.0, grid_calls_sum=100.0, dip_calls=63.0, grid_mode="full")
    d = derive(dict(r))
    assert abs(d["poa_zmc"] - 2.0) < 1e-12
    assert abs(d["so_share_grid"] - 0.5) < 1e-12          # (100 - 150) / (100 - 200)
    assert abs(d["so_share_dip"] - 1.05) < 1e-12          # DIP beats the E3 optimum
    assert abs(d["so_share_best_dip"] - 1.0) < 1e-12      # against the best social cost found
    assert abs(d["dip_calls_share63"] - 0.1) < 1e-12
    r["sc0"], r["sc_so_e3"], r["sc_dip_target"], r["sc_dip"] = -100.0, -100.2, -100.2, -100.2  # optimum within 0.5%: share undefined
    assert np.isnan(derive(dict(r))["so_share_grid"])
