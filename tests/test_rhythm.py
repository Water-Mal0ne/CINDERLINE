"""Scientific gates and null behavior, using explicit synthetic fixtures."""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import rhythm


def fixture(country="United_States", streams=("Terra", "Aqua"), dip=True, controls=True):
    chunks, periods = [], []
    for year in range(2013, 2019):
        dates = pd.date_range(f"{year}-01-01", f"{year}-12-31")
        rest = rhythm.DAYS.index(rhythm.REST_DAYS[country])
        for stream in streams:
            counts = np.where((dates.dayofweek == rest) & dip, 2, 10)
            chunks.append(pd.DataFrame({"country": country, "stream": stream, "type": 0,
                                        "local_date": np.repeat(dates, counts), "daynight": "D"}))
            if controls:
                chunks.append(pd.DataFrame({"country": country, "stream": stream, "type": 2,
                                            "local_date": np.repeat(dates, 2), "daynight": "D"}))
            periods.append({"country": country, "stream": stream, "year": year, "complete": True})
    return pd.concat(chunks, ignore_index=True), {"local_periods": periods}


class RhythmTests(unittest.TestCase):
    def test_weekday_exposure_leap_and_nonleap(self):
        self.assertEqual(rhythm.weekday_exposure(2020).sum(), 366)
        self.assertEqual(rhythm.weekday_exposure(2019).sum(), 365)
        self.assertTrue(set(rhythm.weekday_exposure(2020)).issubset({52, 53}))

    def test_manifest_requires_boundary_archives(self):
        files = [{"country": "Nepal", "sensor": "modis", "year": y, "status": "complete",
                  "complete": True, "coverage_start": f"{y}-01-01T00:00:00Z",
                  "coverage_end": f"{y+1}-01-01T00:00:00Z"} for y in [2013, 2014, 2015]]
        self.assertTrue(rhythm.verified_local_year({"files": files}, "Nepal", "Aqua", 2014))
        self.assertFalse(rhythm.verified_local_year({"files": files}, "Nepal", "Aqua", 2013))
        self.assertFalse(rhythm.verified_local_year({"files": files}, "Nepal", "VIIRS", 2014))

    def test_opening_year_is_not_complete_even_with_attestation(self):
        for stream, first in [("Terra", 2001), ("Aqua", 2003), ("VIIRS", 2013)]:
            manifest = {"local_periods": [dict(country="Nepal", stream=stream, year=y, complete=True)
                                           for y in [first-1, first]]}
            self.assertFalse(rhythm.verified_local_year(manifest, "Nepal", stream, first-1))
            self.assertTrue(rhythm.verified_local_year(manifest, "Nepal", stream, first))

    def test_dip_detected_and_constant_rate_null(self):
        data, manifest = fixture()
        df, _ = rhythm._prepare(data)
        results = rhythm.analyse_family(df, manifest, rhythm.DEFAULTS)
        aqua = next(r for r in results if r["country"] == "United_States" and r["stream"] == "Aqua")
        self.assertTrue(aqua["significant"])
        self.assertEqual(aqua["lowest_day"], "Sun")
        self.assertLess(aqua["p_adjusted"], .05)
        controls = rhythm.analyse_family(df, manifest, rhythm.DEFAULTS, control=True)
        aqua_control = next(r for r in controls if r["country"] == "United_States" and r["stream"] == "Aqua")
        self.assertFalse(aqua_control["significant"])
        self.assertAlmostEqual(aqua_control["rest_index"], 1)

    def test_unverified_years_cannot_pass(self):
        data, _ = fixture()
        df, _ = rhythm._prepare(data)
        rows = rhythm.analyse_family(df, {}, rhythm.DEFAULTS)
        aqua = next(r for r in rows if r["country"] == "United_States" and r["stream"] == "Aqua")
        self.assertEqual(aqua["status"], "insufficient_data")
        self.assertFalse(aqua["significant"])
        self.assertFalse(aqua["period_verified"])
        self.assertEqual(len(aqua["weekdays"]), 7)

    def test_one_stream_cannot_confirm_country(self):
        data, manifest = fixture(streams=("Aqua",))
        df, _ = rhythm._prepare(data)
        main = rhythm.analyse_family(df, manifest, rhythm.DEFAULTS)
        controls = rhythm.analyse_family(df, manifest, rhythm.DEFAULTS, control=True)
        gate = rhythm.make_gate(main, controls, "REAL FIRMS DATA")
        self.assertEqual(gate["per_country"]["United_States"]["status"], "insufficient_data")
        self.assertFalse(gate["production_allowed"])

    def test_order_does_not_change_rng_results(self):
        data, manifest = fixture()
        df, _ = rhythm._prepare(data)
        original = rhythm.analyse_family(df, manifest, rhythm.DEFAULTS)
        shuffled = rhythm.analyse_family(df.sample(frac=1, random_state=10), manifest, rhythm.DEFAULTS)
        self.assertEqual(original, shuffled)

    def test_controls_and_synthetic_label_block_release(self):
        frames, periods = [], []
        for country in ("United_States", "Nepal", "Australia"):
            frame, manifest = fixture(country)
            frames.append(frame)
            periods.extend(manifest["local_periods"])
        df, _ = rhythm._prepare(pd.concat(frames, ignore_index=True))
        manifest = {"local_periods": periods}
        main = rhythm.analyse_family(df, manifest, rhythm.DEFAULTS)
        controls = rhythm.analyse_family(df, manifest, rhythm.DEFAULTS, control=True)
        real = rhythm.make_gate(main, controls, "REAL FIRMS DATA")
        self.assertEqual(real["statistical_decision"], "pass")
        self.assertEqual(real["decision"], "pass")
        synthetic = rhythm.make_gate(main, controls, "SYNTHETIC DATA")
        self.assertFalse(synthetic["production_allowed"])
        self.assertEqual(synthetic["decision"], "insufficient_data")
        self.assertEqual(rhythm.make_gate(main, [], "REAL FIRMS DATA")["decision"], "insufficient_data")

    def _official(self, folder, decision="pass", label="REAL FIRMS DATA"):
        gate = {"decision": decision, "label": label,
                "per_country": {"United_States": {"status": "pass", "predicted_rest_day": "Sun"},
                                "Nepal": {"status": "fail", "predicted_rest_day": "Sat"}}}
        (Path(folder) / "kill_test_gate.json").write_text(json.dumps(gate))
        pd.DataFrame([{"country": "United_States", "subset": "all", "stream": s, "status": "ok",
                       "Sun_hi": hi} for s, hi in [("Terra", .76), ("Aqua", .71), ("VIIRS", 1.02)]]
                     ).to_csv(Path(folder) / "kill_test_results.csv", index=False)

    def test_official_gate_is_published_and_robustness_never_changes_it(self):
        data, manifest = fixture(controls=False)  # strict variant cannot qualify controls
        with tempfile.TemporaryDirectory() as official, tempfile.TemporaryDirectory() as out:
            self._official(official)
            result = rhythm.run(data, out, label="REAL FIRMS DATA", manifest=manifest, official=official)
            self.assertEqual(result["gate"]["decision"], "pass")
            self.assertIn("kill_test.py", result["gate"]["source"])
            us = result["robustness"]["per_country"]["United_States"]
            self.assertEqual(us["ci_upper_below_one"]["streams"], 2)
            self.assertTrue(us["ci_upper_below_one"]["passed"])
            self.assertIn("matched_static_controls", us["failed"])
            self.assertNotIn("Nepal", result["robustness"]["per_country"])
            json.dumps(result, allow_nan=False, default=str)

    def test_official_gate_missing_or_synthetic_is_insufficient(self):
        data, manifest = fixture()
        with tempfile.TemporaryDirectory() as official, tempfile.TemporaryDirectory() as out:
            self.assertEqual(rhythm.run(data, out, manifest=manifest)["gate"]["decision"], "insufficient_data")
            self._official(official, label="SYNTHETIC DATA")
            self.assertEqual(rhythm.run(data, out, manifest=manifest, official=official)["gate"]["decision"],
                             "insufficient_data")
            self._official(official)
            self.assertEqual(rhythm.run(data, out, label="SYNTHETIC DATA", manifest=manifest,
                                        official=official)["gate"]["decision"], "insufficient_data")

    def test_empty_input_writes_valid_insufficient_report(self):
        with tempfile.TemporaryDirectory() as folder:
            result = rhythm.run(pd.DataFrame(), folder, label="SYNTHETIC DATA")
            self.assertEqual(result["gate"]["decision"], "insufficient_data")
            json.dumps(result, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
