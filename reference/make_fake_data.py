"""Fake FIRMS files with a known answer, to test kill_test.py.
Nepal: 12% dip on local Saturday. Bangladesh: no dip at all. United_States: 10% Sunday dip.
Includes night passes so that UTC-vs-local date errors would show up."""
import os
import numpy as np
import pandas as pd

rng = np.random.default_rng(0)
OUT = os.path.join(os.path.dirname(__file__), "data")

SPEC = {
    # country: (utc offset hours, lat, lon range, dip weekday (Mon=0) or None, dip size)
    "Nepal": (5.75, 28.0, (81, 88), 5, 0.12),
    "Bangladesh": (6.0, 24.0, (88, 92), None, 0.0),
    "United_States": (None, 38.0, (-120, -75), 6, 0.10),
}
PASSES = {  # stream: (instrument, satellite, local pass hours)
    "Terra": ("MODIS", "Terra", [10.5, 22.5]),
    "Aqua": ("MODIS", "Aqua", [13.5, 1.5]),
    "VIIRS": ("VIIRS", "N", [13.5, 1.5]),
}

for country, (off, lat, (lon0, lon1), dip_day, dip) in SPEC.items():
    for year in range(2013, 2025):
        days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
        season = 1 + 0.9 * np.cos(2 * np.pi * (days.dayofyear - 90) / 365)  # spring peak
        weather = rng.gamma(2, 0.5, len(days))                                # clustered noise
        for stream, (inst, sat, hours) in PASSES.items():
            scale = {"Terra": 6, "Aqua": 10, "VIIRS": 40}[stream]
            rows = []
            for d, s, w in zip(days, season, weather):
                lam = scale * s * w * (1 - dip if d.dayofweek == dip_day else 1)
                for _ in range(rng.poisson(lam)):
                    lon = rng.uniform(lon0, lon1)
                    h = hours[rng.random() < 0.25]  # 25% night detections
                    o = off if off is not None else lon / 15
                    utc = d + pd.Timedelta(hours=h + rng.uniform(-0.4, 0.4) - o)
                    rows.append({
                        "latitude": lat + rng.normal(0, 2), "longitude": lon,
                        "acq_date": utc.strftime("%Y-%m-%d"), "acq_time": int(utc.strftime("%H%M")),
                        "satellite": sat, "instrument": inst,
                        "confidence": rng.choice(["l", "n", "h"]) if inst == "VIIRS" else int(rng.integers(0, 100)),
                        "daynight": "D" if 6 < h < 18 else "N", "type": 0,
                    })
            # static sources (type 2): steady, no weekly dip -> negative control
            for d in days:
                for _ in range(rng.poisson(scale * 0.1)):
                    o = off if off is not None else lon0 / 15
                    utc = d + pd.Timedelta(hours=13.5 - o)
                    rows.append({**rows[0], "acq_date": utc.strftime("%Y-%m-%d"),
                                 "acq_time": int(utc.strftime("%H%M")), "type": 2})
            sensor = "modis" if inst == "MODIS" else "viirs-snpp"
            path = os.path.join(OUT, sensor, str(year), f"{sensor}_{year}_{country}.csv")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            mode = "a" if os.path.exists(path) else "w"
            pd.DataFrame(rows).to_csv(path, mode=mode, header=(mode == "w"), index=False)
print("fake data written to", OUT)
