import datetime as dt
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from pipeline.calendar import export_ics, seasonal_tables


class CalendarTests(unittest.TestCase):
    def test_anomaly_excludes_own_year(self):
        rows = [{"date": f"{y}-01-01", "harmonized": v} for y, v in
                [(2018, 10), (2019, 10), (2020, 10), (2021, 1000)]]
        clim, anomalies, _ = seasonal_tables(pd.DataFrame(rows))
        spike = next(a for a in anomalies if a["date"] == "2021-01-01")
        self.assertEqual(spike["status"], "high")
        self.assertEqual(spike["reference_years"], 3)
        self.assertIsNone(spike["z_score"])

    def test_empty_period_and_ics_end_is_exclusive(self):
        self.assertEqual(seasonal_tables(pd.DataFrame()), ([], [], []))
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.ics"
            export_ics([{"start_week": 53, "end_week": 53}], p, 2027)
            text = p.read_text()
            self.assertIn("DTEND;VALUE=DATE:20280101", text)
            self.assertIn("Not a forecast", text)


if __name__ == "__main__":
    unittest.main()
