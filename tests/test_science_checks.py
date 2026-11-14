import pandas as pd
import pytest

from pipeline.validation.science_checks import bridge_ratio, children, coarse_cell, select_training_cells, spatial_metrics


def test_coarse_cell_preserves_floor_boundaries_in_both_hemispheres():
    assert coarse_cell("27.25:84.75") == "27.00:84.50"
    assert coarse_cell("-0.25:-120.25") == "-0.50:-120.50"
    assert coarse_cell("-0.50:-120.50") == "-0.50:-120.50"
    assert all(coarse_cell(child)=="-0.50:-120.50" for child in children("-0.50:-120.50"))
    with pytest.raises(ValueError):
        coarse_cell("27.10:84.75")


def test_grid_selection_uses_training_and_sums_child_multiplicities():
    frame=pd.DataFrame({"cell_id":["0.00:0.00","0.25:0.25","1.00:1.00","2.00:2.00"],
                        "year":[2013,2017,2013,2019],"n":[3,4,6,100000]})
    assert select_training_cells(frame,1)==["0.00:0.00"]


def test_bridge_ratio_never_fits_validation_years():
    annual=pd.DataFrame({"Terra":[10]*9,"Aqua":[20]*5+[10000]*4},index=range(2003,2012))
    assert bridge_ratio(annual)==2


def test_coarse_aggregation_reduces_local_error_without_improving_total_bias():
    dates=pd.to_datetime(["2018-01-01","2018-01-02"])
    index=pd.MultiIndex.from_product([["a","b"],dates],names=["cell_id","date"])
    fine=pd.DataFrame({"Aqua":[10,0,0,0],"estimate":[0,0,10,0]},index=index)
    coarse=fine.groupby(level="date").sum()
    coarse["cell_id"]="parent"
    coarse=coarse.reset_index().set_index(["cell_id","date"])
    a,b=spatial_metrics(fine),spatial_metrics(coarse)
    assert a["bias_pct"]==b["bias_pct"]==0
    assert a["recorded_activity_jaccard"]==0
    assert b["recorded_activity_jaccard"]==1
    # This demonstrates why higher coarse agreement is not spatial truth.
    assert a["monthly_normalized_absolute_error_pct"]==200
    assert b["monthly_normalized_absolute_error_pct"]==0
