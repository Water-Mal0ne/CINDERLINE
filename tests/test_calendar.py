import datetime as dt
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from pipeline.calendar import export_ics, normalized_daily, seasonal_tables


class CalendarTests(unittest.TestCase):
    def test_anomaly_excludes_own_year(self):
        rows = [{"date": f"{y}-01-{day:02d}", "harmonized": v} for y, v in
                [(2018, 10), (2019, 10), (2020, 10), (2021, 1000)] for day in range(1, 8)]
        clim, anomalies, _ = seasonal_tables(pd.DataFrame(rows))
        spike = next(a for a in anomalies if a["date"] == "2021-01-01")
        self.assertEqual(spike["status"], "high")
        self.assertEqual(spike["reference_years"], 3)
        self.assertIsNone(spike["z_score"])

    def test_incomplete_week_is_not_a_low_activity_anomaly(self):
        rows = [{"date": f"{year}-01-{day:02d}",
                 "harmonized": 10 if year != 2021 or day == 1 else None}
                for year in [2018, 2019, 2020, 2021] for day in range(1, 8)]
        climatology, anomalies, _ = seasonal_tables(pd.DataFrame(rows))
        self.assertFalse(any(a["date"].startswith("2021") for a in anomalies),
                         "One known day and six missing days are not a seven-day low-activity observation.")
        week = next(row for row in climatology if row["week"] == 1)
        self.assertEqual(week["years"], 3)
        self.assertEqual(week["median"], 70)

    def test_missing_days_cannot_create_a_reference_distribution(self):
        rows = [{"date": f"{year}-01-{day:02d}",
                 "harmonized": 10 if year == 2018 or day == 1 else None}
                for year in [2018, 2019, 2020, 2021] for day in range(1, 8)]
        climatology, anomalies, _ = seasonal_tables(pd.DataFrame(rows))
        self.assertFalse(anomalies, "Three incomplete reference weeks cannot establish a low baseline.")
        week = next(row for row in climatology if row["week"] == 1)
        self.assertIsNone(week["median"])

    def test_constant_daily_activity_has_no_leap_year_tail_anomaly(self):
        rows = [{"date": str(day.date()), "harmonized": 10}
                for year in [2018, 2019, 2020, 2021, 2022, 2023]
                for day in pd.date_range(f"{year}-01-01", f"{year}-12-31")]
        _, anomalies, _ = seasonal_tables(pd.DataFrame(rows))
        self.assertFalse(anomalies,
                         "Week 53 contains one or two days; duration alone must not create an anomaly.")

    def test_normalization_preserves_declared_raw_baseline(self):
        row = {"date": "2012-04-01", "raw_aqua": 12, "raw_viirs": None,
               "raw": 12, "harmonized": 12, "source": "observed Aqua"}
        result = normalized_daily(pd.DataFrame([row])).iloc[0]
        self.assertEqual(result["raw"], 12,
                         "Verified Aqua fallback must not be overwritten by a hard-coded 2012 switch.")

    def test_empty_period_and_ics_end_is_exclusive(self):
        self.assertEqual(seasonal_tables(pd.DataFrame()), ([], [], []))
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.ics"
            export_ics([{"start_week": 53, "end_week": 53}], p, 2027)
            text = p.read_text()
            self.assertNotIn(b"\r\r\n", p.read_bytes())
            self.assertIn(b"BEGIN:VCALENDAR\r\n", p.read_bytes())
            self.assertIn("DTEND;VALUE=DATE:20280101", text)
            self.assertIn("Not a forecast", text)


if __name__ == "__main__":
    unittest.main()
