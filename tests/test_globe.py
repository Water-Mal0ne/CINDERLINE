import numpy as np
import pandas as pd

from pipeline.globe import build, manifest_fingerprint


def fixture():
    rows = []
    for year, stream, cell, frp, count in [(2012, "Aqua", "27.00:85.00", 5, 2),
                                         (2012, "Terra", "27.00:85.00", 5, 99),
                                         (2013, "Aqua", "27.00:85.00", 5, 100),
                                         (2013, "VIIRS", "27.00:85.00", 5, 4),
                                         (2013, "VIIRS", "27.25:85.25", 75, 3)]:
        rows.extend(dict(country="Nepal", year=year, stream=stream, cell_id=cell, frp=frp, daynight="D", type=0)
                    for _ in range(count))
    data = pd.DataFrame(rows)
    data.attrs = {"label": "SYNTHETIC DATA", "manifest": {"files": [dict(country="Nepal", sensor=s, year=y, complete=True, status="complete", sha256=str(y))
                  for s, ys in [("modis", [2011, 2012, 2013, 2014]), ("viirs-snpp", [2012, 2013, 2014])] for y in ys]}}
    model = {"grid_size": .25, "selection": {"Nepal": {"selected": "M1"}},
             "ratios": {"B1": .25, "M1": {"Nepal|D:low": .5, "Nepal|D:high": 2.}}}
    return data, model


def test_globe_exact_known_weights_without_pooling_streams(tmp_path):
    data, model = fixture()
    result = build(data, model, tmp_path / "globe.json")
    assert result["years"] == [2012, 2013]
    assert result["coverage_regions"][0]["sources"] == ["observed Aqua", "converted VIIRS"]
    assert len(result["cells"]) == 2
    assert result["cells"][0]["lat"] == 27.125
    assert result["cells"][0]["lon"] == 85.125
    np.testing.assert_allclose(np.sum([c["values"] for c in result["cells"]], axis=0), [2, 8])
    assert result["cells"][1]["values"][0] == 0


def test_globe_missing_country_year_stays_null(tmp_path):
    data, model = fixture()
    second = pd.DataFrame([dict(country="United_States", year=2013, stream="Aqua", cell_id="38.00:-122.00", frp=20, daynight="D", type=0)])
    attrs = data.attrs.copy()
    attrs["manifest"] = {"files": attrs["manifest"]["files"] + [dict(country="United_States", sensor="modis", year=y, complete=True, status="complete") for y in [2012, 2013, 2014]]}
    data = pd.concat([data, second], ignore_index=True)
    data.attrs = attrs
    model["selection"]["United_States"] = {"selected": "B1"}
    result = build(data, model, tmp_path / "globe.json")
    usa = next(c for c in result["cells"] if c["region"] == "United_States")
    assert usa["values"] == [None, 1.0]


def test_manifest_fingerprint_ignores_local_paths_and_order():
    a = {"country": "Nepal", "sensor": "modis", "year": 2013, "sha256": "abc", "complete": True, "status": "complete"}
    b = {**a, "year": 2014}
    assert manifest_fingerprint({"files": [a, b]}) == manifest_fingerprint({"files": [{**b, "path": "elsewhere"}, a]})
    assert manifest_fingerprint({"files": [a]}) != manifest_fingerprint({"files": [{**a, "sha256": "changed"}]})
