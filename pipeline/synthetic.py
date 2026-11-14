"""Clearly labeled controlled data for software tests; never a real-data fallback without labeling."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

LOCATIONS = {"Nepal": (27.75, 85.25, "Asia/Kathmandu"), "United_States": (38.5, -121.5, "America/Los_Angeles")}


def generate(countries=None, years=None, seed=7):
    countries = countries or ["Nepal", "United_States"]
    years = list(years or range(2012, 2026))
    rng = np.random.default_rng(seed)
    frames, files = [], []
    for country in countries:
        lat, lon, zone = LOCATIONS[country]
        for year in years:
            dates = pd.date_range(f"{year}-01-01", f"{year}-12-31")
            season = 1.4 + np.cos(2 * np.pi * (dates.dayofyear - 100) / 365.25)
            base = np.maximum(1, np.rint((3 + .14 * (year - years[0])) * season)).astype(int)
            for stream, factor in [("Aqua", 1), ("VIIRS", 4), ("Terra", 1)]:
                counts = base * factor
                repeated = dates.repeat(counts)
                n = len(repeated)
                local_aware = (repeated + pd.Timedelta(hours=13.5 if stream != "Terra" else 10.5)).tz_localize(zone)
                local = local_aware.tz_localize(None)
                frame = pd.DataFrame(dict(country=country, stream=stream, utc=local_aware.tz_convert("UTC"),
                                          local=local, local_date=local.normalize(), weekday=local.dayofweek,
                                          year=local.year, lat=lat, lon=lon, cell_id=f"{lat:.2f}:{lon:.2f}",
                                          frp=20.0, daynight="D", type=0, confidence="h" if stream == "VIIRS" else "90",
                                          timezone=zone, file_year=year, label="SYNTHETIC DATA"))
                frames.append(frame)
            for sensor in ["modis", "viirs-snpp"]:
                files.append(dict(country=country, sensor=sensor, year=year, status="complete", complete=True,
                                  coverage_start=f"{year}-01-01T00:00:00Z", coverage_end=f"{year+1}-01-01T00:00:00Z",
                                  synthetic=True, completeness_basis="Generated full civil year; known observation support"))
    frame = pd.concat(frames, ignore_index=True)
    frame.attrs.update(label="SYNTHETIC DATA", manifest={"label": "SYNTHETIC DATA", "files": files},
                       truth="VIIRS detections exactly four times Aqua; rising seasonal reference; no inserted rest-day effect")
    return frame


def save_switch_check(output_dir):
    """Known trend with a constructed fourfold switch and independently fitted overlap ratio."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    years = np.arange(2005, 2025)
    truth = 100 + 3 * (years - 2005)
    from .harmonize import fit_ratios
    overlap = pd.DataFrame([dict(country="Synthetic", year=int(y), stratum="D:medium", stream=s, n=float(n))
                            for y, count in zip(years, truth) if 2013 <= y <= 2017
                            for s, n in [("Aqua", count), ("VIIRS", 4 * count)]])
    ratio = fit_ratios(overlap)["B1"]
    raw = np.where(years >= 2012, truth * 4, truth)
    recovered = np.where(years >= 2012, raw * ratio, raw)
    table = pd.DataFrame({"year": years, "known_reference": truth, "naive_switch": raw, "recovered": recovered,
                          "label": "SYNTHETIC DATA"})
    table.to_csv(output / "synthetic_switch.csv", index=False)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(years, raw, label="Naive sensor switch", color="#e76f51")
    ax.plot(years, truth, label="Known reference", color="#234638", linewidth=3)
    ax.plot(years, recovered, "--", label="Converted to reference", color="#60a5fa")
    ax.axvline(2012, color="#8c8c8c", linewidth=.8)
    ax.set(title="SYNTHETIC DATA — controlled fourfold instrument switch", ylabel="Synthetic detection count", xlabel="Year")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output / "synthetic_switch.png", dpi=150)
    plt.close(fig)
    return table
