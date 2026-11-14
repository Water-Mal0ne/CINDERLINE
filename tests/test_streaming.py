from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from pipeline.streaming import aggregate_archives as streaming



def fixture():
    return pd.DataFrame({"latitude": [23.8]*8, "longitude": [90.4]*8,
                         "acq_date": ["2019-12-31"]*8, "acq_time": [1830,1830,1830,1830,1830,1830,1830,1830],
                         "satellite": ["Aqua"]*8, "instrument": ["MODIS"]*8, "confidence": [90]*8,
                         "frp": [5,5,20,20,20,75,75,np.nan], "daynight": ["N"]*8,
                         "type": [0,0,0,0,0,1,2,-1]})


def test_chunk_sufficient_counts_equal_whole_cleaned_data():
    raw = fixture()
    whole = streaming.clean_frame(raw, "Bangladesh")
    expected = streaming.sufficient_stats(whole)
    pieces = [streaming.sufficient_stats(streaming.clean_frame(part, "Bangladesh")) for part in [raw.iloc[:3], raw.iloc[3:6], raw.iloc[6:]]]
    for i, keys in enumerate([streaming.CELL_KEYS, streaming.FIT_KEYS, streaming.RHYTHM_KEYS]):
        combined = pd.concat([p[i] for p in pieces]).groupby(keys, observed=True, dropna=False).sum(numeric_only=True).reset_index().sort_values(keys).reset_index(drop=True)
        pd.testing.assert_frame_equal(combined, expected[i].sort_values(keys).reset_index(drop=True))
    assert int(expected[0].n.sum()) == 8
    assert set(whole.year) == {2020}  # UTC archive boundary does not become local December31
    assert set(whole.type) == {0,1,2,-1}


def test_weighted_calibration_matches_detection_counts():
    from pipeline.harmonize import fit_ratios
    raw = fixture().iloc[:5].copy()
    raw["acq_date"] = "2013-06-01"
    aqua = streaming.clean_frame(raw, "Bangladesh")
    viirs_raw = pd.concat([raw]*4, ignore_index=True)
    viirs_raw["instrument"], viirs_raw["satellite"], viirs_raw["confidence"] = "VIIRS", "N", "h"
    viirs = streaming.clean_frame(viirs_raw, "Bangladesh")
    _, counts, _ = streaming.sufficient_stats(pd.concat([aqua,viirs],ignore_index=True))
    ratio = fit_ratios(counts[counts.type==0])
    assert ratio["B1"] == .25
    assert all(value == .25 for value in ratio["M1"].values())


def test_weighted_rhythm_is_exactly_equal_to_raw_detection_inference():
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from pipeline.streaming import weighted_rhythm
    from pipeline import rhythm
    chunks, periods = [], []
    for year in range(2013, 2020):
        dates = pd.date_range(f"{year}-01-01", f"{year}-12-31")
        for stream in rhythm.STREAMS:
            for fire_type in [0, 1, 2, -1]:
                n = np.where((dates.dayofweek == 5) & (fire_type == 0), 2, 7)
                chunks.append(pd.DataFrame({"country":"Nepal", "stream":stream, "type":fire_type,
                    "local_date":np.repeat(dates,n), "daynight":"D" if fire_type%2==0 else "N"}))
            periods.append({"country":"Nepal","stream":stream,"year":year,"complete":True})
    raw, _ = rhythm._prepare(pd.concat(chunks, ignore_index=True))
    counts = raw.groupby(streaming.RHYTHM_KEYS).size().rename("n").reset_index()
    # Splitting a sufficient-statistic row must not change any result.
    a, b = counts.copy(), counts.copy()
    a["n"] = a.n // 2
    b["n"] = b.n - a.n
    counts = pd.concat([a,b],ignore_index=True).sample(frac=1, random_state=9)
    for manifest in [{"local_periods":periods}, {}]:
        for subset, control in [("all",False),("day",False),("all",True)]:
            expected = rhythm.analyse_family(raw,manifest,rhythm.DEFAULTS,subset,control)
            actual = weighted_rhythm.analyse_family(counts,manifest,subset=subset,control=control)
            assert expected == actual


def test_commissioning_guard_rejects_partial_opening_year_even_with_adjacent_archives():
    from pipeline.streaming import weighted_rhythm
    files = [{"country":"Egypt","sensor":"modis","year":year,"status":"complete","complete":True,
              "coverage_start":f"{year}-01-01T00:00:00Z","coverage_end":f"{year+1}-01-01T00:00:00Z"}
             for year in range(2001,2005)]
    manifest = {"files":files,"local_periods":[{"country":"Egypt","stream":"Aqua","year":2002,"complete":True}]}
    assert not weighted_rhythm.verified_local_year(manifest,"Egypt","Aqua",2002)
    assert weighted_rhythm.verified_local_year(manifest,"Egypt","Aqua",2003)


def test_weighted_rhythm_rejects_fractional_counts():
    from pipeline.streaming import weighted_rhythm
    _, _, counts = streaming.sufficient_stats(streaming.clean_frame(fixture(),"Bangladesh"))
    counts["n"] = .5
    with pytest.raises(ValueError,match="finite integers"):
        weighted_rhythm.analyse_family(counts,{})


def test_synthetic_weighted_provenance_blocks_a_passing_statistical_fixture(tmp_path):
    from pipeline.streaming import weighted_rhythm
    from pipeline import rhythm
    rows, periods = [], []
    for country in ["United_States","Australia","Nepal"]:
        rest = rhythm.DAYS.index(rhythm.REST_DAYS[country])
        for stream in ["Aqua","Terra"]:
            for year in range(2013,2020):
                exposure = rhythm.weekday_exposure(year)
                periods.append({"country":country,"stream":stream,"year":year,"complete":True})
                for day in range(7):
                    for kind in [0,2]:
                        n = int(exposure[day]*(2 if kind==2 or day==rest else 10))
                        rows.append(dict(country=country,stream=stream,year=year,weekday=day,daynight="D",type=kind,n=n))
    frame = pd.DataFrame(rows)
    result = weighted_rhythm.run_counts(frame,{"label":"SYNTHETIC DATA","local_periods":periods},tmp_path)
    assert result["gate"]["statistical_decision"] == "pass"
    assert result["gate"]["label"] == "SYNTHETIC DATA"
    assert result["gate"]["production_allowed"] is False


def test_dictionary_codec_preserves_json_types_and_float_precision():
    from pipeline.streaming.estimate_dictionary import compact_table, decode_table, encode
    values = [None,0,False,1,True,0.0,1.0,-0.0,"0",.12345678901234568]
    rows = [[value,"repeated long provenance value"] for value in values]*30
    packed = compact_table(["mixed","provenance"],rows)
    assert packed["encoding"] == "column-dictionary-v1"
    assert encode(decode_table(packed)) == encode(rows)


@pytest.mark.parametrize("value",[-1,2,.5,True,None])
def test_dictionary_codec_rejects_invalid_indexes(value):
    from pipeline.streaming.estimate_dictionary import decode_table
    with pytest.raises(ValueError,match="Invalid dictionary index"):
        decode_table({"columns":["v"],"rows":[[value]],"dictionaries":{"v":[None,7]}})
