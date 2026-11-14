"""The rhythm web payload copies official kill_test.py numbers and never invents them."""
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from pipeline import rhythm_web
from pipeline.rhythm import DAYS


def write_official(folder, statuses, drop_ci=False):
    rows = []
    for country, (status, rest) in statuses.items():
        for stream in ("Terra", "Aqua", "VIIRS"):
            row = {"country": country, "subset": "all", "stream": stream, "status": "ok", "years": 12,
                   "detections": 1000, "rest_day": rest, "rest_index": 0.8, "lowest_day": rest,
                   "rest_is_lowest": True, "p_null": 0.0002, "bonferroni_m": 21, "significant": status == "pass"}
            for i, d in enumerate(DAYS):
                row[d] = 0.8 if d == rest else 1.0 + i / 100
                if not drop_ci:
                    row[f"{d}_lo"], row[f"{d}_hi"] = row[d] - 0.05, row[d] + 0.05
            rows.append(row)
    pd.DataFrame(rows).to_csv(Path(folder) / "kill_test_results.csv", index=False)
    gate = {"decision": "pass", "label": "REAL FIRMS DATA", "rule": "pre-registered",
            "countries_passing": [c for c, (s, _) in statuses.items() if s == "pass" and c != "United_States"],
            "per_country": {c: {"status": s, "predicted_rest_day": r, "streams_significant": 3 if s == "pass" else 0,
                                "streams_with_data": 3} for c, (s, r) in statuses.items()},
            "negative_control_static_sources": [{"stream": "VIIRS", "status": "ok", "detections": 5000,
                                                 "max_abs_deviation": 0.017}],
            "caveats": ["Detections are not fires."]}
    (Path(folder) / "kill_test_gate.json").write_text(json.dumps(gate))


class RhythmWebTests(unittest.TestCase):
    def test_payload_copies_official_numbers_and_sunday_caveat(self):
        statuses = {"United_States": ("pass", "Sun"), "Australia": ("pass", "Sun"), "Nepal": ("fail", "Sat")}
        with tempfile.TemporaryDirectory() as official, tempfile.TemporaryDirectory() as out:
            write_official(official, statuses)
            payload = rhythm_web.build(official, None, out)
            self.assertEqual(payload["official"]["decision"], "pass")
            self.assertEqual(payload["sunday_caveat"], rhythm_web.SUNDAY_CAVEAT)
            us = next(c for c in payload["countries"] if c["country"] == "United_States")
            sun = next(d for d in us["streams"][0]["weekdays"] if d["day"] == "Sun")
            self.assertEqual((sun["index"], sun["lo"], sun["hi"]), (0.8, 0.75, 0.85))
            self.assertTrue((Path(out) / "rhythm.json").exists())
            json.loads((Path(out) / "rhythm.json").read_text())

    def test_no_sunday_caveat_when_a_non_sunday_country_passes(self):
        statuses = {"United_States": ("pass", "Sun"), "Nepal": ("pass", "Sat")}
        with tempfile.TemporaryDirectory() as official, tempfile.TemporaryDirectory() as out:
            write_official(official, statuses)
            self.assertIsNone(rhythm_web.build(official, None, out)["sunday_caveat"])

    def test_missing_per_day_ci_is_rejected(self):
        with tempfile.TemporaryDirectory() as official, tempfile.TemporaryDirectory() as out:
            write_official(official, {"United_States": ("pass", "Sun")}, drop_ci=True)
            with self.assertRaises(ValueError):
                rhythm_web.build(official, None, out)


if __name__ == "__main__":
    unittest.main()
