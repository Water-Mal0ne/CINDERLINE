"""Review B3: full weekday shapes from the official kill_test.py results (no new statistics).

python -m pipeline.review.weekday_shapes   ->  reports/review/weekday_shapes.md, weekday_shapes.csv

A day is called "low" / "high" here only when its 95% year-bootstrap interval lies entirely below / above 1.0.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def describe(rows: pd.DataFrame, rest: str) -> str:
    notes = []
    for r in rows.itertuples():
        low = [d for d in DAYS if getattr(r, f"{d}_hi") < 1]
        high = [d for d in DAYS if getattr(r, f"{d}_lo") > 1]
        rest_i = getattr(r, rest)
        bits = [f"{r.stream}: {rest} {rest_i:.3f}"]
        if rest in high:
            bits.append(f"{rest} is ABOVE average")
        elif rest in low:
            bits.append(f"{rest} below average")
        others_low = [d for d in low if d != rest]
        if others_low:
            bits.append("also low: " + ", ".join(others_low))
        if high and rest not in high:
            bits.append("high: " + ", ".join(high))
        notes.append("; ".join(bits))
    return " | ".join(notes)


def main():
    res = pd.read_csv(ROOT / "reports/official/kill_test_results.csv")
    res = res[(res.subset == "all") & (res.status == "ok")]
    out_rows, lines = [], ["# Full weekday shapes (review B3)", "",
                           "Source: `reports/official/kill_test_results.csv` (official pre-specified test, all "
                           "detections, 2013-2024). Index 1.00 = average day. In brackets: 95% year-bootstrap "
                           "interval. A day is called low/high only if its whole interval is below/above 1.", ""]
    for country, g in res.groupby("country", sort=False):
        rest = g.rest_day.iloc[0]
        lines.append(f"## {country.replace('_', ' ')} (rest day {rest})")
        lines.append("")
        lines.append("| Stream | " + " | ".join(DAYS) + " |")
        lines.append("|---|" + "---|" * 7)
        for r in g.itertuples():
            cells = []
            for d in DAYS:
                v, lo, hi = getattr(r, d), getattr(r, f"{d}_lo"), getattr(r, f"{d}_hi")
                mark = "**" if d == rest else ""
                cells.append(f"{mark}{v:.3f}{mark} ({lo:.2f}-{hi:.2f})")
                out_rows.append({"country": country, "stream": r.stream, "day": d, "index": v, "lo": lo, "hi": hi,
                                 "rest_day": rest})
            lines.append(f"| {r.stream} | " + " | ".join(cells) + " |")
        lines.append("")
        lines.append("Shape: " + describe(g, rest))
        lines.append("")
    out = ROOT / "reports/review"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(out_rows).assign(label="REAL FIRMS DATA").to_csv(out / "weekday_shapes.csv", index=False)
    (out / "weekday_shapes.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(l for l in lines if l.startswith("Shape") or l.startswith("## ")))


if __name__ == "__main__":
    main()
