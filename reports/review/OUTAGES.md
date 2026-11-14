# Satellite outages in the record (review task A6)

Data: REAL FIRMS DATA. No app change yet; this is a report. Dates are from NASA/NOAA notices (sources below);
the "in our data" columns are from the published national daily series (`web/public/data/{country}.json`).

| Outage (documented) | In our data | Test years? | Calendar effect |
|---|---|---|---|
| Aqua MODIS science data outage, 16 Aug - 2 Sep 2020 (FMU/SSR error; partly reprocessed from direct-broadcast data) | Aqua counts fall but are not zero (Australia 29/day vs ~200 before; Brazil 623 vs 1,541) | Yes (2020) | Calendar 2020 uses converted VIIRS, so not shown as low. It does lower the Aqua reference in test weeks, which inflates the model's apparent bias (Australia 2020 selected-model bias +27%). |
| Aqua safe mode, 31 Mar 2022 - data from 17 Apr 2022 | Zero Aqua detections in all 7 countries 2-16 Apr 2022 | Yes (2022) | Calendar 2022 uses converted VIIRS, not affected; Aqua reference missing for ~2 test weeks. |
| Suomi-NPP safe mode from 26 Jul 2022; VIIRS back 10 Aug; land products resumed 20 Aug 2022 | Zero VIIRS detections in all 7 countries 28 Jul - 10 Aug 2022; reduced around it | Yes (2022) | **Shown as low activity.** Calendar values drop (US 50/day vs 1,374 before) and the weeks are flagged as low anomalies: US 4, Brazil 3, Australia 2, Egypt 2, India 2. |
| S-NPP GPS/geolocation anomaly, 9-16 Jul 2024 | Zero VIIRS in all 7 countries 11-15 Jul 2024 | Yes (2024) | Low flags in Australia, Brazil, Egypt, India and the US (1-2 each). |
| S-NPP VIIRS processing outage from 24 Jul 2024 (one notice: data lost to 1 Aug) | Zero VIIRS in all 7 countries 25-28 Jul 2024 | Yes (2024) | Low flags in Australia (2) and India (1). |
| Not matched to a notice we checked | Zero VIIRS in all 7 countries 31 May - 2 Jun and 4-5 Nov 2024 | Yes (2024) | Not yet checked. NASA lists separate S-NPP alerts for May 2024 (geolocation) and November 2024. |

So: every outage above falls inside the 2020-2024 test years, and before review task E5 the VIIRS outages showed up
in the calendar as low activity and low-anomaly flags.

**Fixed in E5** (`python -m pipeline.review.no_observation`, summary in `no_observation_summary.json`): 38 days per
country are now "no observation" (33 documented VIIRS outage days plus 5 days with no VIIRS detections in any of the
seven countries: 31 May-2 Jun and 4-5 Nov 2024). Weeks containing them are grey in the calendar and excluded from the
typical-season statistics and anomaly flags (1-3 flags per country removed; critical periods unchanged). The Aqua
outages fall in years where the calendar uses converted VIIRS, so they mark no calendar days. The held-out
evaluation and the globe's annual totals are unchanged.

Sources: [Aqua MODIS science data outage (LAADS)](https://ladsweb.modaps.eosdis.nasa.gov/alerts-and-issues/171853),
[2020-08-16 Aqua MODIS anomaly (LAADS)](https://ladsweb.modaps.eosdis.nasa.gov/alerts-and-issues/171856),
[Aqua safe mode alert (Earthdata)](https://www.earthdata.nasa.gov/data/alerts-outages/aqua-safe-mode-alert),
[Aqua safe mode event (MCST)](https://mcst.gsfc.nasa.gov/news/aqua-safe-mode-event),
[S-NPP VIIRS safe mode (NOAA CoastWatch)](https://coastwatch.noaa.gov/cwn/news/2022-07-28/s-nppviirs-instrument-safe-mode.html),
[Suomi NPP recovers from safe mode (Earthdata)](https://www.earthdata.nasa.gov/data/alerts-outages/suomi-npp-recovers-from-safe-mode),
[S-NPP geolocation anomaly July 2024 (Earthdata)](https://www.earthdata.nasa.gov/data/alerts-outages/suomi-npp-viirs-data-product-geolocation-anomaly-july-2024),
[S-NPP VIIRS data product anomaly July 2024 (Earthdata)](https://www.earthdata.nasa.gov/data/alerts-outages/suomi-npp-viirs-data-product-anomaly-july-2024),
[S-NPP VIIRS anomaly November 2024 (Earthdata)](https://www.earthdata.nasa.gov/data/alerts-outages/suomi-npp-viirs-data-product-anomaly-november-2024).
