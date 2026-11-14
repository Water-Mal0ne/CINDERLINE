# Harmonization evaluation

Data: **REAL FIRMS DATA**

Model selected on 2018–2019 daily MAE; final metrics on 2020–2024.

```csv
region,model,split,aggregation,n_periods,bias_pct,mae,correlation,peak_week_error,label
Nepal,B0,test,monthly,60,1167.2458526613727,2474.4333333333334,0.9886094578804726,0.6,REAL FIRMS DATA
Nepal,B1,test,monthly,60,92.06577068015572,198.42926968654237,0.9886094578804732,0.6,REAL FIRMS DATA
Nepal,M1,test,monthly,60,-8.084784461867427,30.204338867142518,0.9953581558825817,0.4,REAL FIRMS DATA
United_States,B0,test,monthly,60,601.4414766161509,31835.4,0.9329572033540141,10.0,REAL FIRMS DATA
United_States,B1,test,monthly,60,6.311571279063758,1606.3003544939904,0.932957203354014,10.0,REAL FIRMS DATA
United_States,M1,test,monthly,60,12.926294448432046,2078.6268211129122,0.9170009702055187,8.6,REAL FIRMS DATA

```

- Counts refer to archived qualifying detections, not fires or burned area.
- Cloud/overpass observation coverage is unknown; zeros mean no archived detections only.
- Full local years require adjacent UTC annual archives.
- No validated pre-Aqua bridge; this build supports dates with Aqua or VIIRS archives.
- M1 matches reported FRP strata empirically, not physically equal pixel-scale energy.
- M2 omitted; map exposes 12 training-period-active cells per country, national totals use all cells.