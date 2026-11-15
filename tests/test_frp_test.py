"""Scientific invariants for the paired FRP comparison, without private raw archives."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pipeline.review import frp_test


def test_weekday_exposure_handles_52_and_53_occurrences():
    dates = pd.date_range('2013-01-01', '2013-12-31')
    frame = pd.DataFrame({'date': dates, 'C': 3, 'V': 3, 'F': 12.})
    indices, exposure, _ = frp_test.indices(frame)
    assert set(exposure) == {52, 53}
    np.testing.assert_allclose(indices, 1.)


def test_constant_power_per_detection_cannot_create_a_contrast():
    dates = pd.date_range('2016-01-01', '2016-12-31')
    counts = np.random.default_rng(10).integers(0, 100, len(dates))
    frame = pd.DataFrame({'date': dates, 'C': counts, 'V': counts, 'F': 7.5 * counts})
    indices, _, _ = frp_test.indices(frame)
    np.testing.assert_allclose(indices[:, 1], indices[:, 2], rtol=0, atol=1e-14)
    np.testing.assert_allclose(indices.sum(axis=0), 7.)


def test_zero_observation_day_remains_in_denominator_until_excluded():
    dates = pd.date_range('2024-01-01', periods=14)
    frame = pd.DataFrame({'date': dates, 'C': 1, 'V': 1, 'F': 10.})
    frame.loc[0, ['C', 'V', 'F']] = 0
    observed, exposure, _ = frp_test.indices(frame)
    excluded, reduced_exposure, _ = frp_test.indices(frame.iloc[1:])
    assert exposure[0] == 2 and reduced_exposure[0] == 1
    assert observed[0, 1] < 1
    np.testing.assert_allclose(excluded, 1.)


def test_undefined_measure_does_not_become_zero_index():
    dates = pd.date_range('2024-01-01', periods=14)
    frame = pd.DataFrame({'date': dates, 'C': 1, 'V': 1, 'F': 0.})
    with pytest.raises(AssertionError):
        frp_test.indices(frame)


def test_public_export_preserves_failed_stream_and_post_result_receipt():
    root = Path(__file__).resolve().parents[1] / 'reports/review/frp'
    result = json.loads((root/'results.json').read_text())
    gate = json.loads((root/'data_gate.json').read_text())
    exported = frp_test.public_payload(result, gate)
    assert [r['stream'] for r in exported['streams']] == ['Terra', 'Aqua', 'VIIRS']
    for row, source in zip(exported['streams'], [r for r in result['summaries'] if r['mask'] == 'primary']):
        assert row['passed'] == source['pass']
        assert row['delta'] == source['mean_delta']
        assert row['ci_low'] == source['ci_lower']
        assert row['count_weekdays'] == source['mean_weekday_profiles']['V']
        assert row['frp_weekdays'] == source['mean_weekday_profiles']['F']
    assert exported['protocol']['git_receipt_after_original_results'] is True
    assert frp_test.check_protocol()['sha256'] == exported['protocol']['sha256']


def test_public_export_rejects_failed_or_stale_verification():
    with pytest.raises(ValueError, match='did not pass'):
        frp_test.verify_export_sources({'status': 'FAIL'}, {})
    with pytest.raises(ValueError, match='predates the current runner'):
        frp_test.verify_export_sources({'status': 'PASS', 'analysis_script_sha256': 'stale'}, {})
