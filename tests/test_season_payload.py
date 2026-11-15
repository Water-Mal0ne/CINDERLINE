import json
import math
import shutil
from pathlib import Path

import pytest

from pipeline.review.season_payload import MASKS, YEARS, build, metrics

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/review/season"


def test_payload_is_exact_reproducible_projection_of_verified_study():
    generated = build(SOURCE)
    published = json.loads((ROOT / "web/public/data/season-comparison.json").read_text())
    assert generated == published
    assert generated["provenance"]["checked_summary_values"] == 84
    assert len(generated["countries"]) == 7
    for country in generated["countries"].values():
        for mask in MASKS:
            assert [f["year"] for f in country["masks"][mask]] == list(YEARS)
        for primary, padded in zip(country["masks"]["primary"], country["masks"]["padded"]):
            for p, q in zip(primary["months"], padded["months"]):
                assert 0 < q[0] <= p[0]
                assert all(qv <= pv + 1e-7 for pv, qv in zip(p[1:], q[1:]))
                if country["model"] == "B1":
                    assert math.isclose(p[3], p[4], rel_tol=1e-12, abs_tol=1e-8)


def test_equal_year_summary_retains_india_tradeoff_and_nepal_improvement():
    data = build(SOURCE)
    for mask in MASKS:
        def means(country, column):
            outcomes = [metrics(f["months"], column) for f in data["countries"][country]["masks"][mask]]
            return [sum(v[i] for v in outcomes) / len(outcomes) for i in (0, 1)]
        simple, selected = means("India", 3), means("India", 4)
        assert selected[0] < simple[0]
        assert selected[1] > simple[1]
        assert means("Nepal", 4)[1] < means("Nepal", 3)[1]


def test_constant_ratio_changes_counts_but_not_seasonal_shares():
    months = [[28, m, 4 * m, 2 * m, m] for m in range(1, 13)]
    assert metrics(months, 2) == (3, 0)
    assert metrics(months, 3) == (1, 0)


def test_zero_total_and_missing_month_are_not_successful_pattern_matches():
    months = [[28, 1, 0, 0, 0] for _ in range(12)]
    assert metrics(months, 2) == (1, None)
    months[0][0] = 0
    assert metrics(months, 1) == (0, None)
    assert metrics([[28, 0, 1, 1, 1] for _ in range(12)], 2) == (None, None)


@pytest.fixture
def copied_source(tmp_path):
    destination = tmp_path / "study"
    (destination / "verification").mkdir(parents=True)
    for name in ("daily_inputs.csv", "excluded_dates.csv", "whole_year_comparison.csv", "input_manifest.json", "verification/independent_verification.json"):
        shutil.copyfile(SOURCE / name, destination / name)
    return destination


def test_source_change_is_rejected_even_if_values_would_parse(copied_source):
    with (copied_source / "daily_inputs.csv").open("a") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="differs from the independently verified"):
        build(copied_source)


def test_failed_independent_receipt_cannot_publish(copied_source):
    receipt_path = copied_source / "verification/independent_verification.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["status"] = "FAIL"
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="no passing independent"):
        build(copied_source)
