import pandas as pd
from pipeline.clean import clean_frame, _utc_datetime


def sample(**extra):
    data = dict(latitude=[27.7], longitude=[85.3], acq_date=["2020-01-01"], acq_time=[2030],
                satellite=["Aqua"], instrument=["MODIS"], confidence=[80], frp=[20], daynight=["N"], type=[0])
    data.update(extra)
    return pd.DataFrame(data)


def test_nepal_civil_time_crosses_local_date():
    result = clean_frame(sample(), "Nepal")
    assert str(result.local_date.iloc[0].date()) == "2020-01-02"
    assert result.weekday.iloc[0] == 3


def test_invalid_times_are_counted_not_rounded():
    times = pd.DataFrame({"acq_date": ["2020-01-01"] * 5, "acq_time": [2360, -1, 123.5, "bad", 30]})
    parsed = _utc_datetime(times)
    assert parsed.isna().tolist() == [True, True, True, True, False]


def test_static_and_unknown_types_are_preserved():
    result = clean_frame(pd.concat([sample(type=[2]), sample(type=[None])], ignore_index=True), "Nepal")
    assert result.type.tolist() == [2, -1]


def test_viirs_low_confidence_excluded():
    result = clean_frame(sample(satellite=["N"], instrument=["VIIRS"], confidence=["l"]), "Nepal")
    assert result.empty


def test_us_dst_conversion():
    result = clean_frame(sample(latitude=[38.5], longitude=[-121.5], acq_date=["2020-07-01"], acq_time=[630]), "United_States")
    assert str(result.local.iloc[0]) == "2020-06-30 23:30:00"


def test_mixed_instrument_confidence_roundtrips_parquet(tmp_path):
    a = clean_frame(sample(), "Nepal")
    b = clean_frame(sample(satellite=["N"], instrument=["VIIRS"], confidence=["n"]), "Nepal")
    combined = pd.concat([a, b], ignore_index=True)
    path = tmp_path / "mixed.parquet"
    combined.to_parquet(path, index=False)
    assert pd.read_parquet(path).confidence.tolist() == ["80", "n"]
