# Background

CINDERLINE is a historical calendar of satellite hotspot detections. It puts observations from different instruments on a declared comparison scale so a change in the sensor is less likely to be mistaken for a change in burning activity.

The NASA Space Apps challenge asks for a web application that joins the MODIS and VIIRS records into a burning activity calendar. Users should be able to inspect patterns, unusual periods and historical seasons for an area they choose. CINDERLINE addresses that task with archived observations; it does not issue forecasts or emergency warnings.

## What a satellite detects

A satellite carries instruments that measure radiation from the Earth. An active-fire algorithm looks for an unusually strong heat signal and records a hotspot when its tests are met. NASA FIRMS, the Fire Information for Resource Management System, distributes these observations and their supporting fields. CINDERLINE uses its country archives, rather than receiving measurements directly from a satellite. [Source: NASA's FIRMS product description.](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html)

A detection refers to a pixel observed at a particular time. The pixel is the patch of ground represented by that measurement, not the outline of a burning area. A small heat source can occupy part of a pixel; a large continuing event can generate many detections across pixels, passes and days. Counting detections therefore does not count separate events or ignitions. [Sources: project measurement limits](../LIMITATIONS.md) and [NASA's interpretation notes](https://firms.modaps.eosdis.nasa.gov/alerts/notes.php).

An overpass is the time when the satellite crosses a location and can observe it. Terra's daytime observations have historically been in the morning, while Aqua and the VIIRS platforms have had afternoon passes. Their nighttime observations provide another sample, but neither instrument watches a location continuously. Clouds, viewing conditions and activity between passes can leave gaps. NASA also reports that Terra and Aqua's crossing times are drifting as their orbits change, so the historical schedules should not be treated as fixed guarantees. [Source: NASA's MODIS-to-VIIRS transition guidance.](https://ladsweb.modaps.eosdis.nasa.gov/learn/modis-to-viirs-transition)

## Why the instruments cannot be joined directly

MODIS is an instrument carried by both Terra and Aqua. VIIRS is a different instrument; the calendar uses the historical VIIRS record from Suomi NPP, abbreviated S-NPP. These names identify the instruments and their spacecraft, not separate kinds of burning.

| Record used here | Nominal active-fire pixel resolution | Role in CINDERLINE |
| --- | --- | --- |
| Terra MODIS | 1 km | Separate comparison and weekly-rhythm stream |
| Aqua MODIS | 1 km | Reference scale for the calendar |
| S-NPP VIIRS | 375 m | Later observations converted to the Aqua reference scale |

The product resolutions and stream choices are recorded in [METHODS.md](../METHODS.md), under "FIRMS products used". Nominal resolution is a product specification; actual pixel footprints vary with viewing geometry. VIIRS can detect smaller heat sources that MODIS misses, so replacing raw MODIS counts with raw VIIRS counts can create an apparent jump even without an equivalent change on the ground.

This is visible in the held-out United States comparison. Unconverted VIIRS totals are 601.4% above Aqua over the test weeks, while the selected conversion is 1.7% above Aqua. Those numbers measure agreement with Aqua, not error against a known total of real events. [Source: the weekly evaluation table.](../reports/review/layer1_table.md)

## What harmonization does

Harmonization estimates a relationship between instruments during years when both have observations. CINDERLINE learns that relationship from earlier overlapping records, then applies the saved conversion to VIIRS detections. The result is expressed in Aqua-reference-equivalent detections: the activity expressed on Aqua's scale, with measurable disagreement still remaining.

The calendar uses observed Aqua for 2003-2012 and converted S-NPP VIIRS from 2013. Training uses 2013-2017; model selection uses 2018-2019; the locked selection is evaluated on 2020-2024. The separate 2025 extension uses the frozen model and is labelled beyond the validation period. [Sources: the method and time splits](../METHODS.md), [the locked model selection](../reports/selection_lock.json), and [the 2025 continuity check](../reports/review/extend2025/CONTINUITY.md).

Aqua is a useful declared reference because its historical overpass schedule is closer to VIIRS's than Terra's morning schedule. It still has its own missed detections and changing observation conditions. Harmonization cannot recover every small heat source MODIS missed, remove cloud gaps, or establish local accuracy from national agreement.

## What FRP measures

Fire radiative power, or FRP, estimates the rate at which a detected heat source emits radiant energy at the observation time. The archive reports it in megawatts. It describes sampled power, not the total energy released over an event's lifetime. [Source: NASA's FRP field definition.](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html)

The more detailed conversion groups detections by country, day or night, and reported FRP range. These groups help estimate the count relationship; they do not make FRP physically interchangeable across instruments. A separate US daytime study compares weekday patterns in counts with patterns in summed FRP from the same qualifying records. That study uses the original streams and does not produce harmonized FRP. [Sources: calibration groups](../METHODS.md) and [the count-versus-FRP report](../reports/review/frp/FRP_TEST.md).

## Why continuity matters as MODIS ends

NASA is preparing for the end of MODIS science collection on Terra and Aqua. A long historical record needs a documented way to compare those observations with successor instruments, including tests of where the comparison fails. Orbital drift already changes when the older instruments observe, adding a reason to check stability before the record ends. [Source: NASA's transition guidance.](https://ladsweb.modaps.eosdis.nasa.gov/learn/modis-to-viirs-transition)

CINDERLINE tests a count-based conversion on archived S-NPP data. Its separate NOAA-20 check applies the saved model to another VIIRS platform, but covers only the countries with completed inputs and still has an unresolved common-date coverage check. It does not establish accuracy for every future platform or year. [Source: the NOAA-20 transfer report.](../reports/review/noaa20/NOAA20.md)
