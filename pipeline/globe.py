"""All-cell annual reference-scale counts for the globe, without expanding daily grids."""
from __future__ import annotations
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .harmonize import _archive_years, _strata, predict_counts


def manifest_fingerprint(manifest):
    """Identify exact input archives independently of local paths or list ordering."""
    records = [{k: record.get(k) for k in ["country", "sensor", "year", "sha256", "complete", "status"]}
               for record in manifest.get("files", [])]
    records.sort(key=lambda r: (str(r["country"]), str(r["sensor"]), int(r["year"] or 0)))
    return hashlib.sha256(json.dumps(records, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build(detections, model_card, output_path):
    """Use the fitted model unchanged; return and write globe JSON.

    Ratios are linear, so aggregating cell/year/stratum counts before conversion is
    equivalent to summing daily converted counts. Terra is never added to Aqua.
    """
    if not isinstance(model_card, dict):
        model_card = json.loads(Path(model_card).read_text(encoding="utf-8"))
    selections, ratios = model_card["selection"], model_card["ratios"]
    regions = sorted(str(c) for c in detections.country.unique())
    unknown = set(regions) - set(selections)
    if unknown:
        raise ValueError(f"No validated model selection for countries: {sorted(unknown)}")
    availability = {c: {s: _archive_years(detections, c, s) for s in ["Aqua", "VIIRS"]} for c in regions}
    years = sorted(set().union(*(a["Aqua"] | a["VIIRS"] for a in availability.values())))
    if not years:
        raise ValueError("No archive-qualified full local years in cleaned dataset manifest")
    cell_size = float(model_card.get("grid_size", .25))
    output = {"years": years, "cell_size": cell_size,
              "label": detections.attrs.get("label", "UNVERIFIED INPUT"),
              "reference": "MODIS Aqua-equivalent archived detections",
              "coverage_regions": [], "cells": [],
              "archive_manifest_fingerprint": manifest_fingerprint(detections.attrs.get("manifest", {})),
              "archive_files": len(detections.attrs.get("manifest", {}).get("files", [])),
              "coverage_note": "Only listed regions have data. Zero means no qualifying archived detections, not observed absence of fire. Cloud/overpass coverage is unknown."}
    for country in regions:
        country_years = availability[country]
        source_years = {"VIIRS": country_years["VIIRS"], "Aqua": country_years["Aqua"] - country_years["VIIRS"]}
        eligible = country_years["Aqua"] | country_years["VIIRS"]
        sources = ["converted VIIRS" if y in country_years["VIIRS"] else "observed Aqua" if y in country_years["Aqua"] else "unavailable" for y in years]
        output["coverage_regions"].append({"id": country, "name": country.replace("_", " "), "sources": sources})
        pieces = []
        for stream, stream_years in source_years.items():
            mask = (detections.country == country) & (detections.type == 0) & (detections.stream == stream) & detections.year.isin(stream_years)
            columns = ["country", "cell_id", "year", "frp", "daynight"] if stream == "VIIRS" else ["cell_id", "year"]
            subset = detections.loc[mask, columns].copy()
            if subset.empty:
                continue
            if stream == "VIIRS":
                subset["stratum"] = _strata(subset)
                counts = subset.groupby(["country", "cell_id", "year", "stratum"], observed=True).size().rename("n").reset_index()
                counts["value"] = predict_counts(counts, selections[country]["selected"], ratios)
                values = counts.groupby(["cell_id", "year"], observed=True).value.sum()
            else:
                values = subset.groupby(["cell_id", "year"], observed=True).size().astype(float).rename("value")
            pieces.append(values.reset_index())
        if not pieces:
            continue
        all_counts = pd.concat(pieces, ignore_index=True)
        table = all_counts.pivot(index="cell_id", columns="year", values="value").reindex(columns=years)
        for year in years:
            table[year] = table[year].fillna(0) if year in eligible else np.nan
        for cell, row in table.sort_index().iterrows():
            south, west = (float(x) for x in str(cell).split(":"))
            output["cells"].append({"id": f"{country}:{cell}", "region": country,
                                    "lat": south + cell_size / 2, "lon": west + cell_size / 2,
                                    "values": [float(v) if np.isfinite(v) else None for v in row.to_numpy()]})
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_text(json.dumps(output, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    # Windows preview/file watchers can briefly hold the old payload open.
    # Keep atomic publication and retry only this transient sharing failure.
    for attempt in range(6):
        try:
            os.replace(pending, path)
            break
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(.15 * (attempt + 1))
    return output
