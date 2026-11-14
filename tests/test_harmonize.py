import numpy as np
import pandas as pd
from pipeline.harmonize import fit_ratios, predict_counts, _archive_years, metrics, bootstrap_daily, raw_display_series, _daily


def test_training_ratio_does_not_read_test_targets():
    rows = pd.DataFrame([dict(country="Nepal", year=y, stratum="D:medium", stream=s, n=n)
                         for y in [2013, 2014, 2020] for s, n in [("Aqua", 10), ("VIIRS", 40)]])
    first = fit_ratios(rows)
    rows.loc[(rows.year == 2020) & (rows.stream == "Aqua"), "n"] = 999999
    assert fit_ratios(rows) == first
    assert first["B1"] == .25


def test_known_fourfold_switch_is_recovered():
    fit = fit_ratios(pd.DataFrame([dict(country="Nepal", year=2013, stratum="D:medium", stream=s, n=n)
                                  for s, n in [("Aqua", 100), ("VIIRS", 400)]]))
    frame = pd.DataFrame(dict(country=["Nepal"], stratum=["D:medium"], n=[560]))
    assert predict_counts(frame, "B1", fit)[0] == 140
    assert predict_counts(frame, "M1", fit)[0] == 140


def test_missing_archive_is_not_zero_observation():
    df = pd.DataFrame()
    assert _archive_years(df, "Nepal", "Aqua") == set()
    df.attrs["manifest"] = {"files": [dict(country="Nepal", sensor="modis", year=y, complete=True, status="complete") for y in [2018, 2019, 2020]]}
    assert _archive_years(df, "Nepal", "Aqua") == {2019}


def test_metrics_ignore_unknowns_and_keep_real_bias():
    result = metrics([10, np.nan, 20], [20, 1000, 40])
    assert result["bias_pct"] == 100
    assert result["mae"] == 15


def test_vectorized_bootstrap_matches_direct_ratio_sums():
    dates = pd.date_range("2020-01-01", periods=4)
    frame = pd.DataFrame(dict(country=["Nepal"] * 4, date=[dates[0], dates[0], dates[2], dates[2]],
                              stratum=["D:low", "N:high", "D:low", "D:unknown"], n=[3, 9, 8, 2]))
    fits = [{"B1": .25, "M1": {"Nepal|D:low": .15, "Nepal|N:high": .5}},
            {"B1": .3, "M1": {"Nepal|D:low": .2, "Nepal|N:high": .45}}]
    for model in ["B1", "M1"]:
        direct = []
        for fit in fits:
            d = frame.assign(pred=predict_counts(frame, model, fit)).groupby("date").pred.sum().reindex(dates, fill_value=0)
            direct.append(d.to_numpy())
        np.testing.assert_allclose(bootstrap_daily(frame, dates, "Nepal", model, fits), direct, atol=1e-12)


def test_partial_instrument_opening_year_is_not_full_aqua_year():
    df = pd.DataFrame()
    df.attrs["manifest"] = {"files": [dict(country="Nepal", sensor="modis", year=y, complete=True, status="complete")
                                      for y in range(2000, 2006)]}
    assert _archive_years(df, "Nepal", "Aqua") == {2003, 2004}
    assert _archive_years(df, "Nepal", "Terra") == {2001, 2002, 2003, 2004}


def test_historical_raw_baseline_uses_eligible_aqua_before_viirs():
    daily = pd.DataFrame({"Aqua": [2., 3., 4., np.nan], "VIIRS": [np.nan, np.nan, 16., np.nan]},
                         index=pd.to_datetime(["2003-01-01", "2012-01-01", "2013-01-01", "2025-01-01"]))
    np.testing.assert_allclose(raw_display_series(daily).to_numpy(), [2, 3, 16, np.nan], equal_nan=True)


def test_extending_history_preserves_heldout_model_predictions():
    frame = pd.DataFrame([dict(country="Nepal", cell_id="ALL", date=pd.Timestamp(d), stream=s,
                              stratum="D:medium", n=n) for d, s, n in
                          [("2003-01-01", "Aqua", 2), ("2012-01-01", "Aqua", 3),
                           ("2020-01-01", "Aqua", 5), ("2020-01-01", "VIIRS", 20)]])
    ratios = {"B1": .25, "M1": {"Nepal|D:medium": .2}}
    availability = {"Terra": set(range(2003, 2025)), "Aqua": set(range(2003, 2025)), "VIIRS": set(range(2013, 2025))}
    short = _daily(frame, "Nepal", "ALL", pd.date_range("2013-01-01", "2024-12-31"), ratios, availability)
    long = _daily(frame, "Nepal", "ALL", pd.date_range("2003-01-01", "2024-12-31"), ratios, availability)
    pd.testing.assert_frame_equal(short.loc["2020":"2024"], long.loc["2020":"2024"])
    assert long.loc["2003-01-01", "Aqua"] == 2
    assert np.isnan(long.loc["2003-01-01", "VIIRS"])
