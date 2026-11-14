# Harmonization evaluation

Data: **SYNTHETIC DATA**

Model selected on 2018–2019 daily MAE; final metrics on 2020–2024.

```csv
region,model,split,aggregation,n_periods,bias_pct,mae,correlation,peak_week_error,label
Nepal,B0,test,monthly,60,300.0,563.85,1.0,0.0,SYNTHETIC DATA
Nepal,B1,test,monthly,60,0.0,0.0,1.0,0.0,SYNTHETIC DATA
Nepal,M1,test,monthly,60,0.0,0.0,1.0,0.0,SYNTHETIC DATA
United_States,B0,test,monthly,60,300.0,563.85,1.0,0.0,SYNTHETIC DATA
United_States,B1,test,monthly,60,0.0,0.0,1.0,0.0,SYNTHETIC DATA
United_States,M1,test,monthly,60,0.0,0.0,1.0,0.0,SYNTHETIC DATA

```

- Counts refer to archived qualifying detections, not fires or burned area.
- Cloud/overpass observation coverage is unknown; zeros mean no archived detections only.
- Full local years require adjacent UTC annual archives.
- No validated pre-Aqua bridge; this build supports dates with Aqua or VIIRS archives.
- M1 matches reported FRP strata empirically, not physically equal pixel-scale energy.
- M2 omitted; map exposes 12 training-period-active cells per country, national totals use all cells.