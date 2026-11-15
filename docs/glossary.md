# Glossary

These definitions describe how terms are used in CINDERLINE. Measurement and model definitions follow [METHODS.md](../METHODS.md); the [limitations](07-limitations-and-faq.md) explain where a quantity should not be overinterpreted.

## Instruments and observations

| Term | Meaning here |
| --- | --- |
| Active-fire product | A dataset of detected heat signals at satellite observation times, rather than a map of all previously burned ground. |
| Aqua | The satellite carrying the MODIS instrument used as CINDERLINE's reference. |
| Archive | Saved observations downloaded for a stated country, instrument and period. A complete file does not mean complete observation coverage. |
| Burned area | Ground affected by burning. A hotspot count or pixel footprint does not measure this area. |
| Confidence | A quality field supplied by the hotspot detection algorithm. It differs from a statistical confidence interval. |
| Detection, or hotspot | An observation of a pixel classified as a thermal anomaly. Repeated observations can belong to the same continuing event. |
| FIRMS | NASA's Fire Information for Resource Management System, which distributes the source observations. |
| Footprint | The ground area represented by a sensor pixel. Its dimensions can change with viewing geometry. |
| FRP | Fire radiative power, the estimated radiant power of a detected heat source at the sampling time, reported in megawatts. Summing sampled FRP does not give total energy, emissions or burned area. |
| Ground truth | Independently established reference information about conditions on the ground. Aqua observations are an instrument reference, not ground truth. |
| Ignition | The start of an event. A newly detected pixel or newly active cell does not establish that an ignition occurred then. |
| Infrared | Radiation at wavelengths longer than visible light, including wavelengths used to detect heat. |
| MODIS | Moderate Resolution Imaging Spectroradiometer, carried by Terra and Aqua. |
| MW | Megawatts, the unit used for reported FRP. It measures power. |
| NOAA-20 | Another satellite carrying VIIRS. The saved conversion is checked on its observations separately from the main S-NPP record. |
| Observation exposure | The opportunities for a satellite to make usable observations, including effects of cloud and overpass coverage. Eligible calendar dates do not measure it. |
| Orbit drift | A change in a satellite's orbital timing or path, which can change when it observes activity. |
| Overpass | A satellite's passage over a location and the associated opportunity to observe it. |
| Pixel | A measurement unit representing a patch of ground, not an exact event boundary. |
| Resolution | The nominal size of the ground detail a product samples. It is distinct from the application's aggregation grid. |
| Saturation | An instrument measurement reaching its upper response limit. |
| Scan and track | Reported pixel dimensions across the satellite's flight path and along it, respectively. They do not, by themselves, define a precisely oriented ground polygon. |
| S-NPP | Suomi National Polar-orbiting Partnership, the satellite supplying the historical VIIRS calendar record. |
| Static-source control | Hotspot records classified as persistent non-vegetation sources, used for diagnostic comparisons. They are not guaranteed to have flat weekday patterns. |
| Stream | One instrument/platform record kept separate during analysis, such as Aqua MODIS or S-NPP VIIRS. |
| Terra | The satellite carrying the other MODIS instrument. Its record remains separate from Aqua and VIIRS. |
| Type | The archive's inferred hotspot category. CINDERLINE uses presumed vegetation detections for its main analysis and other source categories for checks. |
| VIIRS | Visible Infrared Imaging Radiometer Suite, carried by S-NPP and other platforms. |

## Geography, time and the calendar

| Term | Meaning here |
| --- | --- |
| Area of interest | A user-selected geographic area whose available grid-cell records are combined. |
| Calendar week, or bin | In the website, consecutive seven-day groups starting on January 1. These are not ISO weeks. |
| Cell center, or centroid | The coordinate used to place a grid cell or summarize a region on a map. It does not locate every detection within it. |
| Civil time | Local clock time assigned using time-zone rules, including daylight saving time where applicable. |
| Climatology | The historical distribution for the same seasonal period across eligible years. Here it describes detection activity rather than a weather forecast. |
| Critical period | A historical high-activity window derived from the seasonal summary. It is not a warning about a future date. |
| Day/night | The source product's classification of an observation as daytime or nighttime. |
| Daylight saving time | A seasonal change to local clock rules in some time zones. The stored UTC timestamp does not change when those rules are applied. |
| Grid cell | A latitude-longitude box used to aggregate observations. Degree-based cells cover different ground areas at different latitudes. |
| IANA time-zone database | Historical local-clock rules for named time zones. Coordinates are mapped to those zones separately before dates and weekdays are assigned. |
| ICS | The calendar-file format used to export historical seasonal windows into a chosen year. The file is a reference, not a forecast. |
| ISO week | An international week-numbering convention. The site's January-anchored calendar does not use it, even where a helper retains a historical name. |
| Local-year spillover | An observation near New Year falling into a different year after conversion from UTC to local time. |
| No observation | A calendar supplier date excluded under the project's gap rules. Other satellite streams can still have recorded detections on that date. |
| Null | A field with no available or computed value, such as an excluded daily estimate or an uncomputed calibration bound. It must not be converted to numeric zero. |
| Occupied cell | A cell with qualifying detections somewhere in the processed record, not necessarily in the selected period. |
| Outage mask | A list of dates excluded because of documented instrument gaps or specified unavailable-data checks. |
| Padded mask | An outage mask widened at interval boundaries to test sensitivity to date assignment. |
| Seasonal shape | How a period's activity is distributed across months or weeks, independently of its total size. |
| Spatial scope | The geography a value describes: a whole country, a selected cell or a chosen area. |
| UTC | Coordinated Universal Time, the source timestamp basis before local-time conversion. |
| W-MON | The Monday-ended weekly aggregation used in the saved evaluation. Its week boundaries differ from the website's January-anchored bins. |
| Zero | A raw zero count has no qualifying archived detections. Rounded area estimates can also become zero. Neither establishes continuous observation or absence of burning. |

## Harmonization and evaluation

| Term | Meaning here |
| --- | --- |
| Aqua-reference-equivalent | A value expressed on Aqua's instrument scale, using observed Aqua directly or a converted VIIRS estimate. Converted values can be fractional. |
| B0, or raw baseline | The unconverted VIIRS comparison used to show the effect of switching instruments without calibration. The site's historical raw series uses Aqua before the switch and VIIRS afterward. |
| B1 | A single Aqua-count/VIIRS-count ratio learned across the training countries and applied to VIIRS counts. |
| Bias | Total predicted-minus-reference discrepancy divided by total reference activity, expressed as a percentage. Positive values indicate a higher model total. |
| Calibration | Estimating the conversion between instrument records. It does not certify either instrument as complete or error-free. |
| Calibration interval | The range produced by refitting the conversion on resampled training years. It omits several sources of observation and model error. |
| Correlation, or r | A measure of linear co-movement. A series can have high correlation with Aqua while its totals remain biased. |
| Frozen model | Saved parameters and selection used without fitting them again to later results. |
| Harmonization | Putting measurements from different instruments on a declared common reference scale. |
| Held-out test | Data reserved from fitting and model selection for evaluation of the locked choice. |
| Jaccard similarity | Overlap between two sets divided by their combined membership. In spatial checks, better overlap does not establish exact locations. |
| M1 | The more detailed ratio model grouped by country, day/night and reported FRP class, with sparse groups pulled toward B1. |
| MAE | Mean absolute error: average size of the model-reference difference, ignoring its sign. Units depend on the aggregation being compared. |
| Monthly share | A month's activity divided by the total over the comparison period. It describes timing separately from total count. |
| Normalized absolute error | Summed absolute errors divided by reference activity. This differs from signed bias because errors do not cancel. |
| Out of sample | A comparison using records not used for fitting or model selection. It does not make the measurements independent. |
| Peak-week error | The absolute difference in peak-week dates, expressed in weeks and averaged over evaluated years. It does not describe displacement of the entire season. |
| Pseudo-count | A fixed stabilizing contribution in the ratio model, not an added source observation. |
| Shrinkage | Pulling estimates for small groups toward a broader estimate so sparse data have less influence. |
| Stratum | A group sharing model attributes, such as country, day/night and reported FRP class. |
| Training | The records used to estimate model parameters. |
| Transfer check | Applying a saved model to another period or platform to measure agreement without refitting. |
| TV, or total variation | Half the sum of absolute differences between monthly shares. The season report displays TV multiplied by 100 as disagreement points. |
| Validation | The separate records used to choose between fitted candidate models. It is distinct from the final held-out test. |

These definitions also cover the [season-preservation report](../reports/review/season/SEASON_CHECK.md) and [spatial sensitivity checks](../reports/scientific_validation/SCIENTIFIC_SENSITIVITY.md).

## Weekly patterns and statistical tests

| Term | Meaning here |
| --- | --- |
| Anomaly | A departure from the same seasonal bin in other eligible years. It is an exploratory historical comparison. |
| Association | A measured relationship between variables that does not establish cause. |
| Benjamini-Hochberg, or BH | The multiple-testing procedure used on the exploratory cell map to control the expected proportion of false discoveries under its assumptions. |
| Bonferroni correction | An adjustment for testing a fixed family of hypotheses together. It reduces the chance of declaring a result just because many tests were tried. |
| Bootstrap | Repeatedly resampling the observed units to examine variability in an estimate. Here whole years are the resampling units for the stated temporal analyses. |
| Confidence interval | An uncertainty range calculated under a specified statistical model. It is not a guarantee that the true value lies inside this particular range. |
| Confounding | An unaccounted factor that can affect an observed relationship, preventing a simple causal interpretation. |
| Delta | The difference between two quantities. In the FRP comparison it is the FRP Sunday index minus the count Sunday index. |
| Exchangeability | The assumption that labels may be reassigned under the null model without changing the relevant statistical behavior. |
| Exploratory analysis | A study used to inspect patterns or develop questions after examining data. It needs different interpretation from an untouched test. |
| Gate, or pass rule | The pre-specified conditions used to report a test outcome. A pass does not imply general accuracy or identify a cause. |
| Leave-one-year-out check | Repeating an estimate after omitting each year in turn to see whether one year dominates it. |
| Maximum-day removal | A sensitivity check that removes each stream-year's highest-FRP day before repeating the contrast. |
| Monte Carlo draws | Repeated random simulations used to approximate a null distribution or uncertainty calculation. |
| Negative control | A comparison intended to reveal measurement or analysis effects unrelated to the target question. Imperfect controls cannot rule out every bias. |
| Newly active cell | A cell detected after a day with no detection in that cell. It is not a verified ignition. |
| Null test | A comparison with patterns generated under a stated no-effect assumption. |
| p-value | How often the null model generates a result at least as extreme in the tested direction. It is not the probability that the claim is true. |
| Percentile | A position in an ordered set of values, used to describe a historical distribution or resampling range. |
| Pointwise interval | An interval for one reported estimate, without simultaneous coverage guarantees for every displayed estimate. |
| Power | The probability that a test detects a specified effect under a stated model. The Nepal power experiment uses simulated reductions on observed data volume. |
| Pre-specified | A rule recorded before the stated calculation. The project's chronology explains which data and results were already known. |
| q-value | The Benjamini-Hochberg-adjusted p-value used for the exploratory cell map. It is not the probability that an individual cell's result is false. |
| Random-weekday null | The rhythm test that selects a random weekday within each year to construct a no-designated-day comparison. |
| Rest day | The weekday hypothesized for a country before the stated rhythm test. It does not describe every person or area in that country. |
| Retrospective | Performed on historical data already examined, rather than a newly reserved test. |
| Sensitivity check | Repeating an analysis with a declared alternative choice to see how much its conclusion changes. |
| Significant | Meeting the stated statistical rule. The official stream table also requires the predicted day to be lowest; a country pass has further conditions. The label does not establish cause or freedom from bias. |
| Weekly Rhythm Index | A weekday's exposure-adjusted rate divided by the mean weekday rate within each year, then averaged across years. The reference level is 1. |
| Year block | A whole year retained as one unit when resampling, rather than treating every detection as independent. |
| z-score | A difference from the historical comparison mean divided by its standard deviation. It describes distance from that comparison, not future risk. |

For the exact testing rules, use [the weekly-rhythm method](../METHODS.md) and [the separate FRP protocol](../reports/review/frp/FRP_TEST.md).

## Data files and software

| Term | Meaning here |
| --- | --- |
| API | A defined way for software components to exchange requests and results. The deployed app reads static files rather than asking a server to run its scientific model. |
| Branch | A named line of work in Git. Changes on an unmerged branch are not automatically part of the published application. |
| Build | Turning source files into the precomputed data or browser assets needed for a particular output. Building locally does not deploy it. |
| Cache | Previously stored data reused to avoid repeating a download or calculation. Its identity must match the current inputs. |
| Canvas | A browser drawing surface. The area-selection map draws on a two-dimensional canvas; Earth uses WebGL. |
| Checkout | The local files for a chosen Git revision or branch. |
| CLI | Command-line interface: running a tool by entering its command and arguments in a terminal. |
| Commit | A saved Git revision identifying a set of source-file changes. It is separate from a deployment. |
| CSV | A table stored as text with separated fields, used for source records and analysis outputs. |
| Data contract | The expected fields, types, units and validation rules for a file exchanged between components. |
| Dependency lock | A file recording the package versions used for installation, such as the web app's package-lock file. |
| Deployment | Publishing a built revision to the hosting service. A local build or Git push alone does not do this in the current setup. |
| GPU | Graphics processing hardware used by a browser to draw the globe. Support can vary across devices. |
| Hash, or checksum | A file fingerprint used to detect changed bytes. A matching hash verifies file identity, not scientific correctness. |
| HTTPS | The encrypted web connection used to serve the published application and verify its assets. |
| JSON | The structured text format used for the site's published data and metadata. |
| Lazy loading | Downloading a component or data file only when its view is needed. |
| Lossless encoding | Storing repeated values more compactly while recovering the same original values. |
| Manifest | A record of input files, sources, dates, counts and hashes used by a build. |
| Metadata | Information about observations or outputs, such as source, units, model and date range. |
| MiB | Mebibyte, a binary size unit used in the build and hosting checks. It differs from a decimal megabyte. |
| Multiplicity | The number of source detections represented by an aggregated row. It must be summed, not replaced by a count of summary rows. |
| Node.js and npm | The JavaScript runtime and package manager used to install, test and build the web application. |
| Parquet | A column-oriented file format used for intermediate processed data. |
| Pipeline | The sequence of cleaning, aggregation, fitting, evaluation and export steps. |
| Preparation | Verified intermediate count partitions produced from source archives before analysis and export. |
| Provenance | The record of where data came from and which transformations produced an output. |
| Pull request, or PR | A proposed branch change submitted for review before merging. Opening one does not publish the website. |
| React | The library used to implement the application's interactive views and state. |
| Reconciliation | Checking that separately generated aggregates agree within their stated scope and precision. |
| Remote | A named Git repository connection. This project's release commands use the remote named `github`. |
| Schema | The specified structure of a data payload, including its fields and allowed value types. |
| SHA-256 | The hashing method used for many source and output fingerprints. |
| SQLite | The local database used to combine intermediate records without loading the full archive into memory. |
| Static hosting | Serving prebuilt application and data files. Cloudflare Pages hosts the published site. |
| Sufficient statistics | Aggregated counts that retain the group information needed by the implemented calculation. They do not preserve every possible question about the original rows. |
| SVG | A vector image format used for charts and exported figures. |
| Synthetic fixture | Explicitly artificial input used to test software behavior under known conditions. |
| TypeScript | JavaScript with declared types checked during the build. A type declaration alone does not validate downloaded data at runtime. |
| Vite | The tool that serves the local app and builds its production browser assets. |
| WebGL | The browser graphics interface used to render the globe. |
| Worker | Cloudflare's server-side execution product. The merged app described here is served as static Pages files and does not depend on a Worker function. |
| Wrangler | Cloudflare's command-line tool, used here for explicit Pages uploads. |

The file formats and build steps are documented in [data and reproduction](05-data-and-reproduction.md) and [architecture](06-architecture.md).
