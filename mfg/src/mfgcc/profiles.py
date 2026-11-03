"""Stylised hourly profiles (an ASSUMPTION of the mean-field study, not data).

The repository has no hourly demand or speed data (docs/MFG_DIRECTION.md, Section 5).  The time-expanded model
therefore uses a stylised profile over the delivery day 08:00-18:00 (H = 10 hourly periods), graded like the
parameters of data/parameters/SOURCES.md:

  congestion level cong(h)   shape C (two Gaussian rush-hour bumps, width 1 h, centred 08:30 and 17:30),
                             anchors A (TomTom 2025 city values: all-day level between the peaks, AM-peak value at
                             08:30, PM-peak value at 17:30; Moscow has no peak values in the index, so its peaks
                             are imputed from the mean AM/PM-to-all-day ratios of the other eight cities, grade C);
  delivery demand share psi(h) shape and level C (no data): a flat base with a late-afternoon bump at 17:30
                             (+60%, width 1.5 h) and a small late-morning bump at 10:00 (+30%, width 1 h),
                             normalised to mean 1 over the ten periods.

``amp`` scales every deviation from the flat profile (amp = 0: flat, i.e. the static model split in ten equal
hours; amp = 1: the profile above).  Results that depend on the profile are reported as sensitivity analyses.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
HOURS = np.arange(8, 18) + 0.5  # period midpoints
WIDE_NAME = {"NewDelhi": "New Delhi", "Bombay": "Mumbai", "BuenosAires": "Buenos Aires", "NewYork": "New York"}


def _city_param(city: str, name: str):
    nm = WIDE_NAME.get(city, city)
    with open(ROOT / "data/parameters/city_parameters.csv") as fh:
        for r in csv.DictReader(fh):
            if r["city"] == nm and r["parameter"] == name:
                try:
                    return float(r["value"]) / 100.0
                except ValueError:
                    return None
    return None


def peak_levels(city: str, allday: float) -> tuple[float, float, str]:
    """(AM peak, PM peak, grade) as fractions of extra travel time."""
    am, pm = _city_param(city, "tomtom_am_peak_congestion_pct"), _city_param(city, "tomtom_pm_peak_congestion_pct")
    if am is not None and pm is not None:
        return am, pm, "A"
    ratios = []
    for c in ("NewDelhi", "Bombay", "Cairo", "BuenosAires", "NewYork", "London", "Paris", "Berlin"):
        a, p, d = (_city_param(c, "tomtom_am_peak_congestion_pct"), _city_param(c, "tomtom_pm_peak_congestion_pct"),
                   _city_param(c, "tomtom_congestion_pct"))
        if a and p and d:
            ratios.append((a / d, p / d))
    r = np.mean(ratios, axis=0)
    return allday * r[0], allday * r[1], "C (imputed)"


def congestion_profile(city: str, allday: float, amp: float = 1.0) -> np.ndarray:
    am, pm, _ = peak_levels(city, allday)
    bump_am = np.exp(-0.5 * (HOURS - 8.5) ** 2)
    bump_pm = np.exp(-0.5 * (HOURS - 17.5) ** 2)
    prof = allday + (am - allday) * bump_am + (pm - allday) * bump_pm
    return np.maximum(allday + amp * (prof - allday), 0.01)


def demand_profile(amp: float = 1.0) -> np.ndarray:
    psi = 1 + 0.6 * np.exp(-0.5 * ((HOURS - 17.5) / 1.5) ** 2) + 0.3 * np.exp(-0.5 * (HOURS - 10.0) ** 2)
    psi = psi / psi.mean()
    return 1 + amp * (psi - 1)
